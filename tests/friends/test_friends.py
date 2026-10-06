import pytest
from app.core.config import settings

@pytest.fixture
def test_users(client):
    users = []
    for i in range(3):
        client.post(
            f"{settings.API_V1_STR}/auth/signup",
            json={"email": f"friend{i}@example.com", "username": f"friend{i}", "password": "password123"}
        )
        resp = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={"username": f"friend{i}@example.com", "password": "password123"}
        )
        users.append({"token": resp.json()["access_token"], "id": i + 1}) # id is likely 1, 2, 3
    
    # We should get actual IDs to be safe
    users_with_ids = []
    for u in users:
        me_resp = client.get(f"{settings.API_V1_STR}/users/me", headers={"Authorization": f"Bearer {u['token']}"})
        users_with_ids.append({"token": u["token"], "id": me_resp.json()["id"]})
    return users_with_ids

def test_send_friend_request(client, test_users):
    u1, u2, u3 = test_users
    resp = client.post(
        f"{settings.API_V1_STR}/friends/requests",
        json={"receiver_id": u2["id"]},
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"

def test_send_self_request(client, test_users):
    u1, _, _ = test_users
    resp = client.post(
        f"{settings.API_V1_STR}/friends/requests",
        json={"receiver_id": u1["id"]},
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    assert resp.status_code == 400

def test_duplicate_request(client, test_users):
    u1, u2, _ = test_users
    client.post(
        f"{settings.API_V1_STR}/friends/requests",
        json={"receiver_id": u2["id"]},
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    resp = client.post(
        f"{settings.API_V1_STR}/friends/requests",
        json={"receiver_id": u2["id"]},
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    assert resp.status_code == 400

def test_accept_friend_request(client, test_users):
    u1, u2, _ = test_users
    req_resp = client.post(
        f"{settings.API_V1_STR}/friends/requests",
        json={"receiver_id": u2["id"]},
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    req_id = req_resp.json()["id"]
    
    accept_resp = client.post(
        f"{settings.API_V1_STR}/friends/requests/{req_id}/accept",
        headers={"Authorization": f"Bearer {u2['token']}"}
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "accepted"

def test_unauthorized_accept(client, test_users):
    u1, u2, u3 = test_users
    req_resp = client.post(
        f"{settings.API_V1_STR}/friends/requests",
        json={"receiver_id": u2["id"]},
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    req_id = req_resp.json()["id"]
    
    accept_resp = client.post(
        f"{settings.API_V1_STR}/friends/requests/{req_id}/accept",
        headers={"Authorization": f"Bearer {u3['token']}"} # u3 tries to accept
    )
    assert accept_resp.status_code == 403

def test_reverse_friend_request_auto_accept(client, test_users):
    u1, u2, _ = test_users
    client.post(
        f"{settings.API_V1_STR}/friends/requests",
        json={"receiver_id": u2["id"]},
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    
    # u2 sends back to u1 instead of accepting
    resp = client.post(
        f"{settings.API_V1_STR}/friends/requests",
        json={"receiver_id": u1["id"]},
        headers={"Authorization": f"Bearer {u2['token']}"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"

def test_reject_request(client, test_users):
    u1, u2, _ = test_users
    req_resp = client.post(
        f"{settings.API_V1_STR}/friends/requests",
        json={"receiver_id": u2["id"]},
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    req_id = req_resp.json()["id"]
    
    reject_resp = client.post(
        f"{settings.API_V1_STR}/friends/requests/{req_id}/reject",
        headers={"Authorization": f"Bearer {u2['token']}"}
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

def test_list_friends_and_remove(client, test_users):
    u1, u2, _ = test_users
    # send and accept
    req_resp = client.post(
        f"{settings.API_V1_STR}/friends/requests",
        json={"receiver_id": u2["id"]},
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    client.post(
        f"{settings.API_V1_STR}/friends/requests/{req_resp.json()['id']}/accept",
        headers={"Authorization": f"Bearer {u2['token']}"}
    )
    
    # list
    friends_resp = client.get(
        f"{settings.API_V1_STR}/friends",
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    assert friends_resp.status_code == 200
    assert len(friends_resp.json()) == 1
    assert friends_resp.json()[0]["friend_id"] == u2["id"]
    
    # remove
    del_resp = client.delete(
        f"{settings.API_V1_STR}/friends/{u2['id']}",
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    assert del_resp.status_code == 204
    
    friends_resp2 = client.get(
        f"{settings.API_V1_STR}/friends",
        headers={"Authorization": f"Bearer {u1['token']}"}
    )
    assert len(friends_resp2.json()) == 0
