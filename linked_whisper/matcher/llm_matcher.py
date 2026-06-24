from __future__ import annotations
import json
import anthropic
from ..schemas.job import JobPosition
from ..schemas.profile import ProfileSchema
from .. import config


class MatchResult:
    def __init__(self, match: bool, score: float, reason: str):
        self.match = match
        self.score = score
        self.reason = reason


_SYSTEM_PROMPT = """\
You are a job matching assistant. Given a candidate profile and a job posting, evaluate whether the job is a good fit.
Respond ONLY with a JSON object in this exact format:
{"match": true|false, "score": 0.0-1.0, "reason": "one sentence explanation"}
- score 0.8-1.0: excellent match
- score 0.6-0.8: good match
- score 0.4-0.6: partial match
- score below 0.4: poor match
Set match=true only when score >= 0.6.\
"""


async def llm_match(job: JobPosition, profile: ProfileSchema) -> MatchResult:
    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    user_message = f"""
CANDIDATE PROFILE:
{profile.model_dump_json(indent=2)}

JOB POSTING:
Title: {job.title}
Company: {job.company}
Location: {job.location}
Tags: {', '.join(job.tags)}
Description (first 1500 chars):
{job.description[:1500]}
URL: {job.url}
"""

    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text.strip()
    try:
        parsed = json.loads(raw)
        return MatchResult(
            match=bool(parsed.get("match", False)),
            score=float(parsed.get("score", 0.0)),
            reason=str(parsed.get("reason", "")),
        )
    except (json.JSONDecodeError, KeyError):
        return MatchResult(match=False, score=0.0, reason=f"Parse error: {raw[:100]}")
