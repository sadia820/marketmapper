def upload(client, content: bytes, filename: str = "leads.csv"):
    return client.post("/api/jobs", files={"file": (filename, content, "text/csv")})


def test_auth_flow(client):
    payload = {"email": "Team@TxLabz.com", "name": "Team", "password": "password123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409

    bad = client.post("/api/auth/login", data={"username": "team@txlabz.com", "password": "nope"})
    assert bad.status_code == 401

    res = client.post("/api/auth/login", data={"username": "team@txlabz.com", "password": "password123"})
    token = res.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "team@txlabz.com"


def test_jobs_require_login(client):
    assert client.get("/api/jobs").status_code == 401


def test_upload_research_and_export(auth_client, site_url):
    csv = (f"company,website,city,owner_phone\n"
           f"Flowly,{site_url}/saas/,Remote,555\n"
           f"Sunrise Bakery,,Lahore,555\n").encode()
    res = upload(auth_client, csv)
    assert res.status_code == 201
    body = res.json()
    assert body["ignored_columns"] == ["owner_phone"]

    job = auth_client.get(f"/api/jobs/{body['job']['id']}").json()
    assert job["status"] == "completed"
    assert (job["total"], job["processed"], job["failed_count"]) == (2, 2, 0)

    items = auth_client.get(f"/api/jobs/{job['id']}/businesses").json()["items"]
    assert [b["status"] for b in items] == ["done", "done"]
    assert items[0]["offers"][0]["id"] == "ai_saas"

    export = auth_client.get(f"/api/jobs/{job['id']}/export.csv")
    assert export.headers["content-type"].startswith("text/csv")
    assert "Flowly" in export.text and "owner_phone" not in export.text

    assert len(auth_client.get("/api/jobs").json()) == 1
    assert auth_client.delete(f"/api/jobs/{job['id']}").status_code == 204
    assert auth_client.get(f"/api/jobs/{job['id']}").status_code == 404


def test_bad_upload_returns_clear_error(auth_client):
    res = upload(auth_client, b"website\nacme.com\n")
    assert res.status_code == 422
    assert "business name" in res.json()["detail"]
