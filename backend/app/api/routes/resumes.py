import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ResumeOut
from app.services import resume_parser as resume_parser_service

router = APIRouter(prefix="/resumes", tags=["简历"])

ALLOWED_SUFFIXES = {".pdf", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024
MIN_TEXT_LENGTH = 30


@router.post(
    "", response_model=ResumeOut, status_code=status.HTTP_201_CREATED, summary="上传并解析简历"
)
def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Resume:
    filename = file.filename or "resume"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "仅支持 PDF / DOCX 格式")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / f"{uuid.uuid4().hex}{suffix}"

    size = 0
    with dest.open("wb") as out:
        while chunk := file.file.read(1 << 20):
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                dest.unlink(missing_ok=True)
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "文件大小不能超过 10MB")
            out.write(chunk)

    try:
        text = resume_parser_service.extract_text(str(dest), suffix)
    except Exception:
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "无法读取文件内容，请确认文件未加密、未损坏"
        ) from None
    if len(text.strip()) < MIN_TEXT_LENGTH:
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "未能从文件中提取到有效文本（可能是扫描件或空文档）"
        )

    resume = Resume(
        user_id=user.id,
        filename=filename,
        file_path=str(dest),
        content_text=text,
        parse_status="pending",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    try:
        content = resume_parser_service.structure_resume(text)
        resume.content_json = json.dumps(content, ensure_ascii=False)
        resume.parse_status = "success"
    except Exception:
        # LLM 结构化失败不阻塞上传，降级为"仅原文"，面试时仍可用文本做上下文
        logger.warning(f"简历 #{resume.id} 结构化失败，降级保存原文")
        resume.parse_status = "raw"
    db.commit()
    db.refresh(resume)
    return resume


@router.get("", response_model=list[ResumeOut], summary="简历列表")
def list_resumes(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Resume]:
    return db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.id.desc()).all()


@router.get("/{resume_id}", response_model=ResumeOut, summary="简历详情")
def get_resume(
    resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Resume:
    resume = (
        db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
    )
    if resume is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "简历不存在")
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除简历")
def delete_resume(
    resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    resume = (
        db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user.id).first()
    )
    if resume is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "简历不存在")
    Path(resume.file_path).unlink(missing_ok=True)
    db.delete(resume)
    db.commit()
