def _upload_resume(client, headers) -> int:
    from tests.test_resumes import RESUME_TEXT, make_docx_bytes

    resp = client.post(
        "/api/resumes",
        headers=headers,
        files={"file": ("r.docx", make_docx_bytes(RESUME_TEXT), "application/octet-stream")},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_interview(client, headers, resume_id: int) -> dict:
    resp = client.post(
        "/api/interviews",
        headers=headers,
        json={"resume_id": resume_id, "interview_type": "resume", "difficulty": "medium"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_interview_generates_first_question(client, auth_headers, fake_llm):
    resume_id = _upload_resume(client, auth_headers)
    session = _create_interview(client, auth_headers, resume_id)

    assert session["status"] == "in_progress"
    assert len(session["messages"]) == 1
    assert session["messages"][0]["role"] == "interviewer"
    assert "项目" in session["messages"][0]["content"]


def test_create_interview_unknown_resume(client, auth_headers, fake_llm):
    resp = client.post(
        "/api/interviews",
        headers=auth_headers,
        json={"resume_id": 999, "interview_type": "technical"},
    )
    assert resp.status_code == 404


def test_answer_streams_reply(client, auth_headers, fake_llm):
    resume_id = _upload_resume(client, auth_headers)
    session = _create_interview(client, auth_headers, resume_id)

    resp = client.post(
        f"/api/interviews/{session['id']}/answer",
        headers=auth_headers,
        json={"content": "我做过一个电商后台项目，负责订单模块。"},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert '"delta"' in body
    assert '"done"' in body
    assert "日活" in body

    detail = client.get(f"/api/interviews/{session['id']}", headers=auth_headers).json()
    roles = [m["role"] for m in detail["messages"]]
    assert roles == ["interviewer", "candidate", "interviewer"]
    assert "日活" in detail["messages"][-1]["content"]


def test_answer_rejected_after_finish(client, auth_headers, fake_llm):
    resume_id = _upload_resume(client, auth_headers)
    session = _create_interview(client, auth_headers, resume_id)
    client.post(
        f"/api/interviews/{session['id']}/answer",
        headers=auth_headers,
        json={"content": "我的回答。"},
    )
    client.post(f"/api/interviews/{session['id']}/finish", headers=auth_headers)

    resp = client.post(
        f"/api/interviews/{session['id']}/answer",
        headers=auth_headers,
        json={"content": "还想继续回答。"},
    )
    assert resp.status_code == 409


def test_finish_generates_report_idempotent(client, auth_headers, fake_llm):
    resume_id = _upload_resume(client, auth_headers)
    session = _create_interview(client, auth_headers, resume_id)
    client.post(
        f"/api/interviews/{session['id']}/answer",
        headers=auth_headers,
        json={"content": "项目背景是公司内部系统，我负责核心链路。"},
    )

    first = client.post(f"/api/interviews/{session['id']}/finish", headers=auth_headers)
    assert first.status_code == 200
    report = first.json()
    assert report["total_score"] == 82
    assert report["dimensions"]["表达清晰"] == 85
    assert len(report["question_reviews"]) == 1

    detail = client.get(f"/api/interviews/{session['id']}", headers=auth_headers).json()
    assert detail["status"] == "finished"
    assert detail["total_score"] == 82

    second = client.post(f"/api/interviews/{session['id']}/finish", headers=auth_headers)
    assert second.json()["id"] == report["id"]


def test_finish_without_answer_rejected(client, auth_headers, fake_llm):
    resume_id = _upload_resume(client, auth_headers)
    session = _create_interview(client, auth_headers, resume_id)
    resp = client.post(f"/api/interviews/{session['id']}/finish", headers=auth_headers)
    assert resp.status_code == 400


def test_interview_isolated_between_users(client, auth_headers, fake_llm):
    resume_id = _upload_resume(client, auth_headers)
    session = _create_interview(client, auth_headers, resume_id)

    other = {"username": "other-user2", "email": "other2@example.com", "password": "password-789"}
    client.post("/api/auth/register", json=other)
    other_creds = {"username": other["username"], "password": other["password"]}
    other_token = client.post("/api/auth/login", json=other_creds).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    resp = client.get(f"/api/interviews/{session['id']}", headers=other_headers)
    assert resp.status_code == 404
    resp = client.delete(f"/api/interviews/{session['id']}", headers=other_headers)
    assert resp.status_code == 404

    # 属主删除正常
    resp = client.delete(f"/api/interviews/{session['id']}", headers=auth_headers)
    assert resp.status_code == 204
