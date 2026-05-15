"""Runtime configuration for LLM Council."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AdvisorConfig:
    """One role-specific model call in the council."""

    role: str
    model: str
    system_prompt: str


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = os.getenv(
    "OPENROUTER_API_URL",
    "https://openrouter.ai/api/v1/chat/completions",
)
DATA_DIR = os.getenv("LLM_COUNCIL_DATA_DIR", "data/conversations")
TITLE_MODEL = os.getenv("LLM_COUNCIL_TITLE_MODEL", "google/gemini-2.5-flash")
CHAIRMAN_MODEL = os.getenv("LLM_COUNCIL_CHAIRMAN_MODEL", "openai/gpt-5.5")


CONTRARIAN_PROMPT = """
You are the Contrarian. Your job is to find the reason the founder's decision
is wrong. Look for weak assumptions, missing evidence, buyer resistance, hidden
complexity, reputational exposure, founder delusion, and places where
enthusiasm is being mistaken for traction.

Your answer must name the strongest argument against the decision, the
assumption most likely to be false, the most probable failure mode, the evidence
that would change your mind, and the call you would make instead.
""".strip()

FIRST_PRINCIPLES_PROMPT = """
You are the First Principles Operator. Strip the question down to constraints:
cash, time, sequencing, labor, conversion, retention, trust, distribution, and
opportunity cost. Ignore elegance unless it changes behavior, revenue, trust, or
execution speed.

Your answer must identify the irreducible constraints, binding bottleneck,
cheapest decisive test, core tradeoff, likely cost, and practical recommendation.
""".strip()

CUSTOMER_REALIST_PROMPT = """
You are the Customer Realist. Judge the decision from the perspective of the
human who must care, adopt, approve, recommend, or pay. Do not confuse curiosity
with intent or intent with purchase.

Your answer must state the customer's likely first reaction, adoption barrier,
buying trigger, trust requirement, clearest value proposition, and what must be
proved in the next customer conversation.
""".strip()

EXPANSIONIST_PROMPT = """
You are the Expansionist. Look for asymmetric upside: the larger wedge,
distribution shortcut, partnership angle, fundraising unlock, or compounding
asset hidden inside the decision. Do not hype vague upside.

Your answer must name the highest-upside interpretation, overlooked strategic
asset, compounding move, risk of thinking too small, and boldest viable option.
""".strip()

EXECUTOR_PROMPT = """
You are the Executor. Convert the decision into action, sequence, ownership,
deadlines, metrics, and kill criteria. Care about what happens Monday morning.

Your answer must include the recommended next move, first three concrete
actions, owner, deadline, success metric, kill criterion, and what should be
ignored or deferred.
""".strip()


COUNCIL_ADVISORS = (
    AdvisorConfig("Contrarian", "x-ai/grok-4.20", CONTRARIAN_PROMPT),
    AdvisorConfig(
        "First Principles Operator",
        "anthropic/claude-opus-4.7",
        FIRST_PRINCIPLES_PROMPT,
    ),
    AdvisorConfig(
        "Customer Realist",
        "google/gemini-3.1-pro-preview",
        CUSTOMER_REALIST_PROMPT,
    ),
    AdvisorConfig("Expansionist", "moonshotai/kimi-k2.6", EXPANSIONIST_PROMPT),
    AdvisorConfig("Executor", "deepseek/deepseek-v4-pro", EXECUTOR_PROMPT),
)
