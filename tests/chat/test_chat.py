"""
Tests for Phase 4: Text Chat Module
"""
import pytest
from app.core.config import settings
from app.schemas.message import MAX_MESSAGE_LENGTH


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _signup_and_login(client, email: str, username: str, password: str = "password123") -> dict:
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
def chat_users(client):
    alice = _signup_and_login(client, "alice@chat.com", "alice_chat")
    bob = _signup_and_login(client, "bob@chat.com", "bob_chat")
    carol = _signup_and_login(client, "carol@chat.com", "carol_chat")
    return alice, bob, carol


@pytest.fixture
def test_conversation(client, chat_users):
    alice, bob, _ = chat_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations",
        json={"participant_id": bob["id"]},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_send_normal_message(client, chat_users, test_conversation):
    alice, _, _ = chat_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
        json={"content": "Hello bob, how are you?"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "Hello bob, how are you?"
    assert data["sender_id"] == alice["id"]
    assert data["conversation_id"] == test_conversation
    assert data["message_type"] == "text"
    assert "id" in data
    assert "created_at" in data


def test_send_unicode_emoji_message(client, chat_users, test_conversation):
    alice, _, _ = chat_users
    content = "Hello 🌍! 🎤🎶 楽しんでね"
    resp = client.post(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
        json={"content": content},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == content


# ---------------------------------------------------------------------------
# Validation Edge Cases
# ---------------------------------------------------------------------------

def test_send_empty_message(client, chat_users, test_conversation):
    alice, _, _ = chat_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
        json={"content": ""},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 422


def test_send_whitespace_message(client, chat_users, test_conversation):
    alice, _, _ = chat_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
        json={"content": "    \n  \t  "},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 422


def test_send_very_long_message(client, chat_users, test_conversation):
    alice, _, _ = chat_users
    content = "a" * (MAX_MESSAGE_LENGTH + 1)
    resp = client.post(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
        json={"content": content},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 422


def test_send_invalid_message_data(client, chat_users, test_conversation):
    alice, _, _ = chat_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
        json={"wrong_field": "hello"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 422


def test_repeated_duplicate_requests(client, chat_users, test_conversation):
    alice, _, _ = chat_users
    # Sending the exact same string twice should create two distinct messages
    r1 = client.post(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
        json={"content": "duplicate"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    r2 = client.post(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
        json={"content": "duplicate"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["id"] != r2.json()["id"]


# ---------------------------------------------------------------------------
# Authorization & Invalid DB State
# ---------------------------------------------------------------------------

def test_send_unauthorized_user(client, chat_users, test_conversation):
    """Carol is not in the Alice-Bob conversation."""
    _, _, carol = chat_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
        json={"content": "I am snooping!"},
        headers={"Authorization": f"Bearer {carol['token']}"},
    )
    assert resp.status_code == 403


def test_read_unauthorized_user(client, chat_users, test_conversation):
    _, _, carol = chat_users
    resp = client.get(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
        headers={"Authorization": f"Bearer {carol['token']}"},
    )
    assert resp.status_code == 403


def test_send_invalid_conversation(client, chat_users):
    alice, _, _ = chat_users
    resp = client.post(
        f"{settings.API_V1_STR}/conversations/99999/messages",
        json={"content": "Hello void"},
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Retrieval, Ordering, and Pagination
# ---------------------------------------------------------------------------

def test_message_ordering_and_pagination(client, chat_users, test_conversation):
    alice, bob, _ = chat_users
    
    # Alice and Bob send 10 messages sequentially
    for i in range(10):
        sender = alice if i % 2 == 0 else bob
        client.post(
            f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
            json={"content": f"Message {i}"},
            headers={"Authorization": f"Bearer {sender['token']}"},
        )
        
    # Get all messages
    resp = client.get(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages",
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    assert resp.status_code == 200
    msgs = resp.json()
    assert len(msgs) == 10
    
    # Ordering must be ascending (oldest first)
    for i in range(10):
        assert msgs[i]["content"] == f"Message {i}"
        if i > 0:
            assert msgs[i]["id"] > msgs[i-1]["id"]
            
    # Pagination test
    resp_page = client.get(
        f"{settings.API_V1_STR}/conversations/{test_conversation}/messages?skip=5&limit=3",
        headers={"Authorization": f"Bearer {alice['token']}"},
    )
    page_msgs = resp_page.json()
    assert len(page_msgs) == 3
    assert page_msgs[0]["content"] == "Message 5"
    assert page_msgs[1]["content"] == "Message 6"
    assert page_msgs[2]["content"] == "Message 7"
