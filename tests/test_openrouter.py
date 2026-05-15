import asyncio

import httpx

from backend import openrouter


def test_query_model_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr(openrouter, "OPENROUTER_API_KEY", None)

    result = asyncio.run(
        openrouter.query_model("model/test", [{"role": "user", "content": "hi"}])
    )

    assert result is None


def test_query_model_extracts_message(monkeypatch):
    monkeypatch.setattr(openrouter, "OPENROUTER_API_KEY", "test-key")

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            return httpx.Response(
                200,
                request=httpx.Request("POST", "https://openrouter.test"),
                json={
                    "choices": [
                        {
                            "message": {
                                "content": "hello",
                                "reasoning_details": [{"type": "summary"}],
                            }
                        }
                    ]
                },
            )

    monkeypatch.setattr(openrouter.httpx, "AsyncClient", FakeClient)

    result = asyncio.run(
        openrouter.query_model("model/test", [{"role": "user", "content": "hi"}])
    )

    assert result == {
        "content": "hello",
        "reasoning_details": [{"type": "summary"}],
    }
