import json
from langchain_core.messages import HumanMessage
from src.groq_client import get_llm

# ─── Blocked keywords (fast rule-based check) ────────────────────────────────

BLOCKED_PATTERNS = [
    "how to make bomb", "how to make weapon", "how to kill",
    "child pornography", "child abuse", "sexual abuse",
    "how to hack", "how to synthesize drugs", "drug synthesis",
    "suicide method", "self harm method", "how to hurt",
    "terrorist", "extremist attack", "mass shooting",
]

GUARDRAIL_PROMPT = """You are a content safety checker for an educational platform.
Analyze the following input and determine if it is safe and appropriate for an educational context.

Input: {content}

Respond with JSON only, no markdown, no backticks:
{{"safe": true or false, "reason": "short reason if unsafe, else ok"}}

Mark as UNSAFE if the input:
- Contains requests for violence, weapons, or harm
- Contains hate speech, racism, or discrimination
- Contains sexually explicit or inappropriate content
- Contains requests to generate malware or illegal content
- Is completely unrelated to any educational purpose
- Contains personal attacks or harassment

Mark as SAFE if the input is:
- An educational question or topic
- A request for factual information
- Study material or academic content
- General knowledge questions
- Even controversial but legitimate academic topics (history of wars, political theory, etc.)"""


async def check_input_safety(content: str) -> tuple[bool, str]:
    """
    Returns (is_safe, reason).
    First does fast keyword check, then LLM-based check.
    """
    if not content or not content.strip():
        return False, "Empty input provided"

    # Fast rule-based check
    content_lower = content.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in content_lower:
            return False, f"Content contains blocked pattern: {pattern}"

    # LLM-based check
    llm = get_llm()
    prompt = GUARDRAIL_PROMPT.format(content=content[:2000])  # cap at 2000 chars for speed

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        is_safe = result.get("safe", True)
        reason = result.get("reason", "")
        return is_safe, reason
    except Exception:
        # If guardrail check itself fails, allow through (fail open)
        return True, ""


async def check_output_safety(content: str) -> tuple[bool, str]:
    """
    Checks LLM output before returning to user.
    Lighter check — only catches clear violations.
    """
    if not content:
        return True, ""

    content_lower = content.lower()
    for pattern in BLOCKED_PATTERNS:
        if pattern in content_lower:
            return False, "Response contained unsafe content and was blocked"

    return True, ""