import json
import anthropic
from ..schemas.profile import ProfileSchema
from .. import config

_SYSTEM_PROMPT = """\
You are a career profile extractor. Given a resume, extract a structured profile schema.
Respond ONLY with a valid JSON object matching this exact structure:
{
  "name": "Full Name",
  "title": "Current or target job title",
  "years_of_experience": <integer>,
  "skills": ["skill1", "skill2", ...],
  "preferred_roles": ["role1", "role2", ...],
  "preferred_industries": ["industry1", ...],
  "excluded_keywords": ["keyword to avoid in job titles/descriptions", ...],
  "min_salary": <integer or null>,
  "work_type": ["remote", "async", ...],
  "summary": "2-3 sentence narrative about the candidate for LLM matching context"
}
Be comprehensive with skills. For excluded_keywords, include technologies, industries, or role types the candidate clearly doesn't match or wouldn't want.\
"""


async def generate_profile(resume_text: str) -> ProfileSchema:
    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"RESUME:\n\n{resume_text}"}],
    )

    raw = message.content[0].text.strip()
    parsed = json.loads(raw)
    return ProfileSchema(**parsed)
