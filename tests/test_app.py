import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402


def _client(tmp_path):
    return create_app(str(tmp_path / "test.db")).test_client()


def _token(client):
    client.post("/signup", json={"username": "asha", "password": "correct-horse"})
    return client.post(
        "/login", json={"username": "asha", "password": "correct-horse"}
    ).get_json()["token"]


def test_expenses_need_login(tmp_path):
    assert _client(tmp_path).get("/expenses").status_code == 401


def test_add_and_list_expense(tmp_path):
    client = _client(tmp_path)
    headers = {"Authorization": f"Bearer {_token(client)}"}
    assert client.post(
        "/expenses", json={"amount": 12.5, "note": "lunch"}, headers=headers
    ).status_code == 201
    expenses = client.get("/expenses", headers=headers).get_json()["expenses"]
    assert expenses == [{"id": 1, "amount_cents": 1250, "note": "lunch"}]


def test_wrong_password_rejected(tmp_path):
    client = _client(tmp_path)
    _token(client)
    resp = client.post("/login", json={"username": "asha", "password": "nope-nope"})
    assert resp.status_code == 401
