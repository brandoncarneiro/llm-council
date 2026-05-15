import asyncio

from backend import council


def test_parse_ranking_from_final_section():
    ranking = """
Response A is thorough.
Response B misses the key point.

FINAL RANKING:
1. Response B
2. Response A
"""

    assert council.parse_ranking_from_text(ranking) == ["Response B", "Response A"]


def test_calculate_aggregate_rankings_orders_by_average_position():
    stage2_results = [
        {"ranking": "FINAL RANKING:\n1. Response B\n2. Response A"},
        {"ranking": "FINAL RANKING:\n1. Response A\n2. Response B"},
        {"ranking": "FINAL RANKING:\n1. Response B\n2. Response A"},
    ]
    label_to_model = {
        "Response A": "model/a",
        "Response B": "model/b",
    }

    assert council.calculate_aggregate_rankings(stage2_results, label_to_model) == [
        {"model": "model/b", "average_rank": 1.33, "rankings_count": 3},
        {"model": "model/a", "average_rank": 1.67, "rankings_count": 3},
    ]


def test_stage2_handles_role_names_in_user_input(monkeypatch):
    async def fake_query_models_parallel(models, messages):
        prompt = messages[0]["content"]
        assert "Advisor (" not in prompt
        assert "Response A" in prompt
        return {
            model: {
                "content": "Evaluation text.\n\nFINAL RANKING:\n1. Response A"
            }
            for model in models
        }

    monkeypatch.setattr(council, "query_models_parallel", fake_query_models_parallel)

    results, label_to_model = asyncio.run(
        council.stage2_collect_rankings(
            "Should the Executor disagree with the Contrarian?",
            [
                {
                    "role": "Contrarian",
                    "model": "model/a",
                    "response": "The best answer mentions the Executor role.",
                }
            ],
        )
    )

    assert label_to_model == {"Response A": "model/a"}
    assert results == [
        {
            "model": "x-ai/grok-4.20",
            "ranking": "Evaluation text.\n\nFINAL RANKING:\n1. Response A",
            "parsed_ranking": ["Response A"],
        },
        {
            "model": "anthropic/claude-opus-4.7",
            "ranking": "Evaluation text.\n\nFINAL RANKING:\n1. Response A",
            "parsed_ranking": ["Response A"],
        },
        {
            "model": "google/gemini-3.1-pro-preview",
            "ranking": "Evaluation text.\n\nFINAL RANKING:\n1. Response A",
            "parsed_ranking": ["Response A"],
        },
        {
            "model": "moonshotai/kimi-k2.6",
            "ranking": "Evaluation text.\n\nFINAL RANKING:\n1. Response A",
            "parsed_ranking": ["Response A"],
        },
        {
            "model": "deepseek/deepseek-v4-pro",
            "ranking": "Evaluation text.\n\nFINAL RANKING:\n1. Response A",
            "parsed_ranking": ["Response A"],
        },
    ]
