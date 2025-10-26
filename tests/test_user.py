import pytest
import json

def test_register_login_profile(client):
    # Register
    data = {
        "name": "TestUser",
        "email": "testuser@example.com",
        "password": "123456",
        "address": "Bengaluru"
    }
    response = client.post("/api/register", data=data)
    assert response.status_code == 201

    # Login
    login_data = {"email": "testuser@example.com", "password": "123456"}
    response = client.post("/api/login", data=json.dumps(login_data), content_type='application/json')
    assert response.status_code == 200
    token = response.get_json()["access_token"]

    # Get Profile
    response = client.get("/api/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.get_json()["email"] == "testuser@example.com"
