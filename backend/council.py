"""Council orchestration and ranking utilities."""

from __future__ import annotations

import asyncio
import re
import string
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from .config import CHAIRMAN_MODEL, COUNCIL_ADVISORS, TITLE_MODEL, AdvisorConfig
from .openrouter import query_model, query_models_parallel

Stage1Result = dict[str, Any]
Stage2Result = dict[str, Any]
Stage3Result = dict[str, Any]
Metadata = dict[str, Any]

_RESPONSE_LABEL_PATTERN = re.compile(r"\bResponse\s+([A-Z])\b")
_FINAL_RANKING_PATTERN = re.compile(r"FINAL\s+RANKING\s*:\s*(?P<body>.*)", re.I | re.S)


def _response_label(index: int) -> str:
    if index >= len(string.ascii_uppercase):
        raise ValueError("LLM Council currently supports at most 26 advisors")
    return f"Response {string.ascii_uppercase[index]}"


def _compact_text(value: str, limit: int = 80) -> str:
    text = " ".join(value.split())
    return text[: limit - 3].rstrip() + "..." if len(text) > limit else text


def _advisor_messages(advisor: AdvisorConfig, user_query: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": advisor.system_prompt},
        {"role": "user", "content": user_query},
    ]


async def stage1_collect_responses(user_query: str) -> list[Stage1Result]:
    """Ask each configured advisor for an independent first-pass answer."""
    calls = [
        query_model(advisor.model, _advisor_messages(advisor, user_query))
        for advisor in COUNCIL_ADVISORS
    ]
    replies = await asyncio.gather(*calls)

    results: list[Stage1Result] = []
    for advisor, reply in zip(COUNCIL_ADVISORS, replies, strict=True):
        if not reply:
            continue
        results.append(
            {
                "role": advisor.role,
                "model": advisor.model,
                "response": reply.get("content", ""),
            }
        )

    return results


def build_stage2_prompt(user_query: str, stage1_results: Sequence[Stage1Result]) -> str:
    """Build the anonymous peer-review prompt for Stage 2."""
    labeled_answers = []
    for index, result in enumerate(stage1_results):
        labeled_answers.append(f"{_response_label(index)}\n{result['response']}")
    expected_ranking = "\n".join(
        f"{index + 1}. {_response_label(index)}"
        for index in range(len(stage1_results))
    )

    return f"""
Evaluate the anonymized answers below.

Original question:
{user_query}

Anonymized answers:
{chr(10).join(chr(10).join(('', answer)) for answer in labeled_answers)}

Instructions:
1. Evaluate each answer on correctness, usefulness, and decision quality.
2. Do not infer or mention model names or advisor roles.
3. End with a machine-readable ranking section.

Ranking format:
FINAL RANKING:
{expected_ranking}

Use every response label exactly once in the final ranking.
""".strip()


def _label_maps(stage1_results: Sequence[Stage1Result]) -> tuple[dict[str, str], dict[str, str]]:
    label_to_model: dict[str, str] = {}
    label_to_role: dict[str, str] = {}

    for index, result in enumerate(stage1_results):
        label = _response_label(index)
        label_to_model[label] = result["model"]
        label_to_role[label] = result["role"]

    return label_to_model, label_to_role


async def stage2_collect_rankings(
    user_query: str,
    stage1_results: Sequence[Stage1Result],
) -> tuple[list[Stage2Result], dict[str, str]]:
    """Ask every configured model to rank anonymous Stage 1 answers."""
    label_to_model, _label_to_role = _label_maps(stage1_results)
    prompt = build_stage2_prompt(user_query, stage1_results)
    messages = [{"role": "user", "content": prompt}]
    models = [advisor.model for advisor in COUNCIL_ADVISORS]
    replies = await query_models_parallel(models, messages)

    rankings: list[Stage2Result] = []
    for model in models:
        reply = replies.get(model)
        if not reply:
            continue
        text = reply.get("content", "")
        rankings.append(
            {
                "model": model,
                "ranking": text,
                "parsed_ranking": parse_ranking_from_text(text),
            }
        )

    return rankings, label_to_model


def build_stage3_prompt(
    user_query: str,
    stage1_results: Sequence[Stage1Result],
    stage2_results: Sequence[Stage2Result],
) -> str:
    """Build the Chairman synthesis prompt with role context restored."""
    advisor_blocks = "\n\n".join(
        f"{result['role']} ({result['model']}):\n{result['response']}"
        for result in stage1_results
    )
    ranking_blocks = "\n\n".join(
        f"{result['model']} ranking:\n{result['ranking']}"
        for result in stage2_results
    )

    return f"""
You are synthesizing a council decision memo.

Original question:
{user_query}

Advisor answers:
{advisor_blocks}

Peer rankings:
{ranking_blocks or "No peer rankings were returned."}

Write one final answer. Resolve disagreement directly, do not average weak
answers, and keep the recommendation actionable. Mention advisor roles only
when attribution makes the conclusion clearer.
""".strip()


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: Sequence[Stage1Result],
    stage2_results: Sequence[Stage2Result],
) -> Stage3Result:
    """Ask the Chairman model to turn the council output into one answer."""
    reply = await query_model(
        CHAIRMAN_MODEL,
        [
            {
                "role": "user",
                "content": build_stage3_prompt(user_query, stage1_results, stage2_results),
            }
        ],
    )
    if not reply:
        return {
            "model": CHAIRMAN_MODEL,
            "response": "Unable to generate a final synthesis from the configured Chairman model.",
        }

    return {"model": CHAIRMAN_MODEL, "response": reply.get("content", "")}


def parse_ranking_from_text(ranking_text: str) -> list[str]:
    """Extract unique `Response X` labels from the final ranking section."""
    section_match = _FINAL_RANKING_PATTERN.search(ranking_text)
    search_area = section_match.group("body") if section_match else ranking_text

    labels: list[str] = []
    seen: set[str] = set()
    for match in _RESPONSE_LABEL_PATTERN.finditer(search_area):
        label = f"Response {match.group(1)}"
        if label not in seen:
            seen.add(label)
            labels.append(label)

    return labels


def calculate_aggregate_rankings(
    stage2_results: Sequence[Stage2Result],
    label_to_model: dict[str, str],
) -> list[dict[str, Any]]:
    """Aggregate peer rankings by average position, lower is better."""
    positions_by_model: defaultdict[str, list[int]] = defaultdict(list)

    for result in stage2_results:
        parsed = result.get("parsed_ranking") or parse_ranking_from_text(result.get("ranking", ""))
        for position, label in enumerate(parsed, start=1):
            model = label_to_model.get(label)
            if model:
                positions_by_model[model].append(position)

    summary = [
        {
            "model": model,
            "average_rank": round(sum(positions) / len(positions), 2),
            "rankings_count": len(positions),
        }
        for model, positions in positions_by_model.items()
        if positions
    ]
    return sorted(summary, key=lambda row: (row["average_rank"], row["model"]))


async def generate_conversation_title(user_query: str) -> str:
    """Generate a short local conversation title."""
    reply = await query_model(
        TITLE_MODEL,
        [
            {
                "role": "user",
                "content": (
                    "Write a 3 to 5 word title for this question. "
                    "Return only the title, with no quotes or punctuation.\n\n"
                    f"Question: {user_query}"
                ),
            }
        ],
        timeout=30.0,
    )
    if not reply:
        return "New Conversation"

    title = _compact_text(str(reply.get("content", "")).strip().strip("\"'"), limit=50)
    return title or "New Conversation"


def _metadata(
    stage1_results: Sequence[Stage1Result],
    label_to_model: dict[str, str],
    rankings: Sequence[Stage2Result],
) -> Metadata:
    _unused_label_to_model, label_to_role = _label_maps(stage1_results)
    return {
        "label_to_model": label_to_model,
        "label_to_role": label_to_role,
        "aggregate_rankings": calculate_aggregate_rankings(rankings, label_to_model),
    }


async def run_full_council(
    user_query: str,
) -> tuple[list[Stage1Result], list[Stage2Result], Stage3Result, Metadata]:
    """Run Stage 1, Stage 2, and Stage 3 for one user question."""
    stage1_results = await stage1_collect_responses(user_query)
    if not stage1_results:
        return (
            [],
            [],
            {
                "model": "none",
                "response": (
                    "No advisor models returned a response. "
                    "Check your OpenRouter key and model IDs."
                ),
            },
            {},
        )

    stage2_results, label_to_model = await stage2_collect_rankings(user_query, stage1_results)
    stage3_result = await stage3_synthesize_final(user_query, stage1_results, stage2_results)
    return (
        stage1_results,
        stage2_results,
        stage3_result,
        _metadata(stage1_results, label_to_model, stage2_results),
    )
