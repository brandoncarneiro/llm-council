from uuid import uuid4

import pytest

from backend import storage


@pytest.fixture()
def isolated_storage(tmp_path, monkeypatch):
    data_dir = tmp_path / "conversations"
    monkeypatch.setattr(storage, "DATA_DIR", data_dir)
    return data_dir


def test_create_get_list_and_delete_conversation(isolated_storage):
    conversation_id = str(uuid4())

    created = storage.create_conversation(conversation_id)
    loaded = storage.get_conversation(conversation_id)
    listed = storage.list_conversations()
    deleted = storage.delete_conversation(conversation_id)

    assert created["id"] == conversation_id
    assert loaded == created
    assert listed == [
        {
            "id": conversation_id,
            "created_at": created["created_at"],
            "title": "New Conversation",
            "message_count": 0,
        }
    ]
    assert deleted is True
    assert storage.get_conversation(conversation_id) is None
    assert list(isolated_storage.glob("*.json")) == []


@pytest.mark.parametrize(
    "conversation_id",
    [
        "../outside",
        "..%2foutside",
        "/tmp/outside",
        "abc/def",
        "not-a-uuid",
        "00000000-0000-0000-0000-000000000000/evil",
        "00000000-0000-0000-0000-000000000000.json",
    ],
)
def test_rejects_unsafe_conversation_ids(isolated_storage, conversation_id):
    with pytest.raises(storage.InvalidConversationIdError):
        storage.get_conversation_path(conversation_id)

    assert not list(isolated_storage.rglob("*"))


def test_normalizes_uuid_before_writing(isolated_storage):
    compact_id = "12345678123456781234567812345678"

    created = storage.create_conversation(compact_id)
    path = storage.get_conversation_path(compact_id)

    assert created["id"] == "12345678-1234-5678-1234-567812345678"
    assert path.name == "12345678-1234-5678-1234-567812345678.json"
    assert path.parent == isolated_storage.resolve()


def test_list_conversations_ignores_symlinks(isolated_storage, tmp_path):
    conversation_id = str(uuid4())
    storage.create_conversation(conversation_id)

    outside_file = tmp_path / "outside.json"
    outside_file.write_text('{"id":"outside"}', encoding="utf-8")
    symlink_path = isolated_storage / f"{uuid4()}.json"
    symlink_path.symlink_to(outside_file)

    conversations = storage.list_conversations()

    assert [conversation["id"] for conversation in conversations] == [conversation_id]
