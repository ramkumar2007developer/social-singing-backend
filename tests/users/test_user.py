import pytest
from app.core.config import settings

def test_create_user(client):
    response = client.post(
        f"{settings.API_V1_STR}/auth/signup",
        json={"email": "test@example.com", "username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_create_user_duplicate_email(client):
    # Create the first user
    client.post(
        f"{settings.API_V1_STR}/auth/signup",
        json={"email": "dup@example.com", "username": "dupuser1", "password": "password123"}
    )
    # Try creating a second user with the same email
    response = client.post(
        f"{settings.API_V1_STR}/auth/signup",
        json={"email": "dup@example.com", "username": "dupuser2", "password": "password123"}
    )
    assert response.status_code == 400

def test_login_user(client):
    client.post(
        f"{settings.API_V1_STR}/auth/signup",
        json={"email": "test_login@example.com", "username": "testuser_login", "password": "password123"}
    )
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test_login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_read_users_me(client):
    client.post(
        f"{settings.API_V1_STR}/auth/signup",
        json={"email": "test_me@example.com", "username": "testuser_me", "password": "password123"}
    )
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test_me@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test_me@example.com"

def test_read_users_me_unauthorized(client):
    response = client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 401
