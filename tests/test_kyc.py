import pytest, io, json

@pytest.fixture
def register_and_login_user(client):
    data = {
        "name": "TestUser2",
        "email": "testuser2@example.com",
        "password": "123456",
        "address": "Bengaluru"
    }
    client.post("/api/register", data=data)
    login_data = {"email": "testuser2@example.com", "password": "123456"}
    response = client.post("/api/login", data=json.dumps(login_data), content_type='application/json')
    token = response.get_json()["access_token"]
    return token

def test_upload_kyc(client, register_and_login_user):
    token = register_and_login_user
    data = {"kyc_document": (io.BytesIO(b"dummy content"), "kyc.txt")}
    response = client.post("/api/upload_kyc", content_type='multipart/form-data',
                           data=data,
                           headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "KYC uploaded successfully" in response.get_json()["message"]

def test_admin_pending_and_verify(client):
    # Register user for KYC
    data = {"name": "TestUser3", "email": "testuser3@example.com", "password": "123456", "address": "Bengaluru"}
    client.post("/api/register", data=data)
    login_data = {"email": "testuser3@example.com", "password": "123456"}
    response = client.post("/api/login", data=json.dumps(login_data), content_type='application/json')
    token = response.get_json()["access_token"]

    # Get pending KYC
    response = client.get("/api/admin/pending_kyc", headers={"Authorization": f"Bearer {token}"})
    pending = response.get_json()
    assert len(pending) > 0
    user_id = pending[0]["_id"]

    # Verify KYC
    response = client.patch(f"/api/admin/verify_kyc/{user_id}",
                            headers={"Authorization": f"Bearer {token}"},
                            data=json.dumps({"status": "Verified"}),
                            content_type='application/json')
    assert response.status_code == 200
    assert "KYC Verified successfully" in response.get_json()["message"]
