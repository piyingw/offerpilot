def _create(
    client, headers, company: str = "字节跳动", status: str = "applied", **overrides
) -> dict:
    payload = {"company": company, "position": "后端开发", "channel": "boss", **overrides}
    if status:
        payload["current_status"] = status
    resp = client.post("/api/applications", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_records_first_event(client, auth_headers):
    application = _create(client, auth_headers)
    assert application["current_status"] == "applied"

    detail = client.get(
        f"/api/applications/{application['id']}", headers=auth_headers
    ).json()
    assert len(detail["events"]) == 1
    assert detail["events"][0]["to_status"] == "applied"
    assert detail["events"][0]["from_status"] is None


def test_create_with_unknown_resume_rejected(client, auth_headers):
    payload = {"company": "X公司", "position": "后端", "resume_id": 999}
    resp = client.post("/api/applications", headers=auth_headers, json=payload)
    assert resp.status_code == 400


def test_status_transition_records_event(client, auth_headers):
    application = _create(client, auth_headers)
    resp = client.patch(
        f"/api/applications/{application['id']}",
        headers=auth_headers,
        json={"status": "interview_1", "status_note": "下周三 14:00"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_status"] == "interview_1"
    assert len(body["events"]) == 2
    assert body["events"][-1]["from_status"] == "applied"
    assert body["events"][-1]["note"] == "下周三 14:00"


def test_patch_without_status_change_keeps_single_event(client, auth_headers):
    application = _create(client, auth_headers)
    resp = client.patch(
        f"/api/applications/{application['id']}",
        headers=auth_headers,
        json={"salary": "25k-35k", "status": "applied"},
    )
    body = resp.json()
    assert body["salary"] == "25k-35k"
    assert len(body["events"]) == 1


def test_list_filters_and_pagination(client, auth_headers):
    _create(client, auth_headers, company="A公司")
    _create(client, auth_headers, company="B公司", status="offer")
    _create(client, auth_headers, company="C公司")

    by_q = client.get("/api/applications?q=B", headers=auth_headers).json()
    assert by_q["total"] == 1 and by_q["items"][0]["company"] == "B公司"

    by_status = client.get("/api/applications?status_filter=offer", headers=auth_headers).json()
    assert by_status["total"] == 1 and by_status["items"][0]["current_status"] == "offer"

    page1 = client.get("/api/applications?page=1&page_size=2", headers=auth_headers).json()
    assert page1["total"] == 3 and len(page1["items"]) == 2 and page1["page"] == 1
    page2 = client.get("/api/applications?page=2&page_size=2", headers=auth_headers).json()
    assert len(page2["items"]) == 1 and page2["page"] == 2


def test_stats_funnel_distribution_weekly(client, auth_headers):
    _create(client, auth_headers, company="A公司")
    b = _create(client, auth_headers, company="B公司")
    _create(client, auth_headers, company="C公司", status="rejected")
    client.patch(
        f"/api/applications/{b['id']}", headers=auth_headers, json={"status": "hr_interview"}
    )

    stats = client.get("/api/applications/stats", headers=auth_headers).json()
    assert stats["total"] == 3
    assert stats["active"] == 2
    assert stats["offers"] == 0
    assert stats["rejected"] == 1

    funnel = {f["status"]: f["count"] for f in stats["funnel"]}
    assert funnel["applied"] == 3  # 被拒的也算"曾投递"
    assert funnel["hr_interview"] == 1
    assert funnel["offer"] == 0

    dist = {d["status"]: d["count"] for d in stats["distribution"] if d["count"] > 0}
    assert dist == {"applied": 1, "hr_interview": 1, "rejected": 1}

    assert len(stats["weekly"]) == 8
    assert sum(w["count"] for w in stats["weekly"]) == 3
    # 3 条创建事件 + B 公司 1 次状态流转
    assert len(stats["recent_events"]) == 4


def test_delete_application(client, auth_headers):
    application = _create(client, auth_headers)
    resp = client.delete(f"/api/applications/{application['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get("/api/applications", headers=auth_headers).json()["items"] == []


def test_isolated_between_users(client, auth_headers):
    application = _create(client, auth_headers)
    other = {"username": "app-other", "email": "app-other@example.com", "password": "password-xyz"}
    client.post("/api/auth/register", json=other)
    other_creds = {"username": other["username"], "password": other["password"]}
    other_token = client.post("/api/auth/login", json=other_creds).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    assert (
        client.get(
            f"/api/applications/{application['id']}", headers=other_headers
        ).status_code
        == 404
    )
    assert client.get("/api/applications", headers=other_headers).json()["items"] == []
    assert (
        client.delete(
            f"/api/applications/{application['id']}", headers=other_headers
        ).status_code
        == 404
    )
