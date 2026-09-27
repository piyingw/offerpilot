import io

from docx import Document


def make_docx_bytes(text: str) -> bytes:
    buf = io.BytesIO()
    doc = Document()
    doc.add_paragraph(text)
    doc.save(buf)
    return buf.getvalue()


RESUME_TEXT = (
    "张三，男，本科，XX大学计算机专业。"
    "项目：电商后台管理系统，负责订单模块，使用 Python/FastAPI + MySQL，"
    "日订单峰值 5 万，接口 P99 延迟 200ms。技能：Python、MySQL、Redis、Docker。"
)


def test_upload_docx(client, auth_headers, fake_llm):
    resp = client.post(
        "/api/resumes",
        headers=auth_headers,
        files={"file": ("我的简历.docx", make_docx_bytes(RESUME_TEXT), "application/octet-stream")},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["filename"] == "我的简历.docx"
    assert body["parse_status"] == "success"
    assert body["content"]["basic_info"]["name"] == "张三"


def test_upload_rejects_bad_extension(client, auth_headers, fake_llm):
    resp = client.post(
        "/api/resumes",
        headers=auth_headers,
        files={"file": ("a.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_rejects_unauthorized(client):
    resp = client.post("/api/resumes", files={"file": ("a.docx", b"x", "application/octet-stream")})
    assert resp.status_code == 401


def test_resume_list_and_detail(client, auth_headers, fake_llm):
    client.post(
        "/api/resumes",
        headers=auth_headers,
        files={"file": ("r.docx", make_docx_bytes(RESUME_TEXT), "application/octet-stream")},
    )
    resp = client.get("/api/resumes", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1

    detail = client.get(f"/api/resumes/{items[0]['id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["content"]["skills"] == ["Python"]


def test_delete_resume(client, auth_headers, fake_llm):
    resp = client.post(
        "/api/resumes",
        headers=auth_headers,
        files={"file": ("r.docx", make_docx_bytes(RESUME_TEXT), "application/octet-stream")},
    )
    resume_id = resp.json()["id"]
    resp = client.delete(f"/api/resumes/{resume_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get("/api/resumes", headers=auth_headers).json() == []


def test_resume_isolated_between_users(client, auth_headers, fake_llm):
    client.post(
        "/api/resumes",
        headers=auth_headers,
        files={"file": ("r.docx", make_docx_bytes(RESUME_TEXT), "application/octet-stream")},
    )
    other = {"username": "other-user", "email": "other@example.com", "password": "password-456"}
    client.post("/api/auth/register", json=other)
    other_token = client.post(
        "/api/auth/login", json={"username": other["username"], "password": other["password"]}
    ).json()["access_token"]
    resp = client.get("/api/resumes", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.json() == []
