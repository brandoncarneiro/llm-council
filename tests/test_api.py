from uuid import uuid4

from fastapi.testclient import TestClient

from backend import main, storage


def test_conversation_crud_uses_safe_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "conversations")
    client = TestClient(main.app)

    create_response = client.post("/api/conversations", json={})
    assert create_response.status_code == 200
    conversation = create_response.json()

    get_response = client.get(f"/api/conversations/{conversation['id']}")
    list_response = client.get("/api/conversations")
    delete_response = client.delete(f"/api/conversations/{conversation['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == conversation["id"]
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == conversation["id"]
    assert delete_response.status_code == 204


def test_invalid_conversation_id_returns_400(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "conversations")
    client = TestClient(main.app)

    response = client.get("/api/conversations/not-a-uuid")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid conversation ID"}
    assert not list(tmp_path.rglob("*"))


def test_empty_message_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "conversations")
    client = TestClient(main.app)
    conversation_id = storage.create_conversation(str(uuid4()))["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/message",
        json={"content": ""},
    )

    assert response.status_code == 422


def test_send_message_persists_stubbed_council_response(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "conversations")

    async def fake_generate_title(content):
        assert content == "What should we do?"
        return "Decision Test"

    async def fake_run_full_council(content):
        assert content == "What should we do?"
        return (
            [{"role": "Contrarian", "model": "model/a", "response": "No"}],
            [{"model": "model/a", "ranking": "FINAL RANKING:\n1. Response A"}],
            {"model": "chairman", "response": "Proceed carefully."},
            {"label_to_model": {"Response A": "model/a"}, "aggregate_rankings": []},
        )

    monkeypatch.setattr(main, "generate_conversation_title", fake_generate_title)
    monkeypatch.setattr(main, "run_full_council", fake_run_full_council)

    client = TestClient(main.app)
    conversation_id = str(uuid4())
    storage.create_conversation(conversation_id)

    response = client.post(
        f"/api/conversations/{conversation_id}/message",
        json={"content": "What should we do?"},
    )
    saved = storage.get_conversation(conversation_id)

    assert response.status_code == 200
    assert response.json()["stage3"] == {
        "model": "chairman",
        "response": "Proceed carefully.",
    }
    assert saved["title"] == "Decision Test"
    assert [message["role"] for message in saved["messages"]] == ["user", "assistant"]


def test_stream_message_handles_no_advisor_responses(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "conversations")

    async def fake_generate_title(_content):
        return "No Model Response"

    async def fake_stage1(_content):
        return []

    monkeypatch.setattr(main, "generate_conversation_title", fake_generate_title)
    monkeypatch.setattr(main, "stage1_collect_responses", fake_stage1)

    client = TestClient(main.app)
    conversation_id = storage.create_conversation(str(uuid4()))["id"]
    response = client.post(
        f"/api/conversations/{conversation_id}/message/stream",
        json={"content": "Will anyone answer?"},
    )
    body = response.text
    saved = storage.get_conversation(conversation_id)

    assert response.status_code == 200
    assert '"type":"stage1_complete","data":[]' in body
    assert '"type":"stage3_complete"' in body
    assert saved["title"] == "No Model Response"
    assert [message["role"] for message in saved["messages"]] == ["user", "assistant"]
