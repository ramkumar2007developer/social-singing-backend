"""
Tests for the Conversations module.

Covers:
  - Happy paths: create, retrieve, list
  - Idempotency: same conversation returned on duplicate POST
  - Authorization: non-participant cannot read a conversation
  - Edge cases: self-conversation, nonexistent user, nonexistent conversation,
                unauthenticated access, invalid IDs
"""
import pytest
from app.core.config import settings

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _signup_and_login(client, email: str, username: str, password: str = "password123") -> dict:
    """Helper: create a user and return their token + id."""
    client.post(
        f"{settings.API_V1_STR}/auth/signup",
        json={"email": email, "username": username, "password": password},
    )
    token_resp = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": email, "password": password},
    )
    token = token_resp.json()["access_token"]
    me = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    return {"token": token, "id": me["id"]}


@pytest.fixture
def three_users(client):
    alice = _signup_and_login(client, "alice@conv.com", "alice_conv")
    bob = _signup_and_login(client, "bob@conv.com", "bob_conv")
    carol = _signup_and_login(client, "carol@conv.com", "carol_conv")
    return alice, bob, carol


# ---------------------------------------------------------------------------
# Happy path — create conversation
# ---------------------------------------------------------------------------

def test_create_conversation(client, three_users):
    alice, bob, _ = three_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    participant_ids = {p["user_id"] for p in data["participants"]}
    assert alice["id"] in participant_ids
    assert bob["id"] in participant_ids
    assert len(data["participants"]) == 2


# ---------------------------------------------------------------------------
# Idempotency — second POST returns same conversation
# ---------------------------------------------------------------------------

def test_create_conversation_idempotent(client, three_users):
    alice, bob, _ = three_users
    r1 = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    r2 = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"], "Duplicate POST must return the same conversation"


def test_create_conversation_idempotent_from_other_side(client, three_users):
    """Bob creating with Alice should return the same conversation Alice already created."""
    alice, bob, _ = three_users
    r1 = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    r2 = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": alice["id"]},
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert r1.json()["id"] == r2.json()["id"]


# ---------------------------------------------------------------------------
# Authorization — non-participant is rejected
# ---------------------------------------------------------------------------

def test_get_conversation_as_non_participant_is_forbidden(client, three_users):
    alice, bob, carol = three_users
    conv_id = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    ).json()["id"]

    resp = client.get(
        f"{settings.API_V1_STR}/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {carol['token']}"},  # carol is NOT in A-B conv
    )
    assert resp.status_code == 403


def test_list_conversations_does_not_include_others(client, three_users):
    alice, bob, carol = three_users
    # Alice-Bob conversation
    client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    # Carol should see an empty list
    resp = client.get(
        f"{settings.API_V1_STR}/conversations",
        headers={"Authorization": f"Bearer {carol['token']}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Retrieve conversation — happy path
# ---------------------------------------------------------------------------

def test_get_conversation_by_id(client, three_users):
    alice, bob, _ = three_users
    conv_id = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    ).json()["id"]

    # Alice can fetch it
    resp = client.get(
        f"{settings.API_V1_STR}/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == conv_id

    # Bob can also fetch it (he is a participant)
    resp2 = client.get(
        f"{settings.API_V1_STR}/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {bob['token']}"},
    )
    assert resp2.status_code == 200


# ---------------------------------------------------------------------------
# List conversations
# ---------------------------------------------------------------------------

def test_list_conversations(client, three_users):
    alice, bob, carol = three_users
    # Alice creates two conversations
    client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": carol["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    resp = client.get(
        f"{settings.API_V1_STR}/conversations",
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ---------------------------------------------------------------------------
# Edge cases — invalid inputs
# ---------------------------------------------------------------------------

def test_create_conversation_with_self_is_rejected(client, three_users):
    alice, _, _ = three_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": alice["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 400


def test_create_conversation_with_nonexistent_user(client, three_users):
    alice, _, _ = three_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": 99999},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 404


def test_get_nonexistent_conversation(client, three_users):
    alice, _, _ = three_users
    resp = client.get(
        f"{settings.API_V1_STR}/conversations/99999",
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 404


def test_get_conversation_unauthenticated(client, three_users):
    alice, bob, _ = three_users
    conv_id = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    ).json()["id"]

    resp = client.get(f"{settings.API_V1_STR}/conversations/{conv_id}")
    assert resp.status_code == 401


def test_create_conversation_unauthenticated(client, three_users):
    _, bob, _ = three_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
    )
    assert resp.status_code == 401


def test_create_conversation_missing_body_field(client, three_users):
    alice, _, _ = three_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 422


def test_create_conversation_invalid_participant_id_type(client, three_users):
    alice, _, _ = three_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": "not-a-number"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 422


def test_response_schema_has_required_fields(client, three_users):
    alice, bob, _ = three_users
    data = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    ).json()
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "participants" in data
    assert isinstance(data["participants"], list)
    for p in data["participants"]:
        assert "user_id" in p
        assert "joined_at" in p
