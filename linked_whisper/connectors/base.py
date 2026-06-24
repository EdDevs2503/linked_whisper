import re
from abc import ABC, abstractmethod
from ..schemas.job import JobPosition
from ..schemas.profile import ProfileSchema

# Skills that map cleanly to API tag values (lowercase, no spaces/special chars).
_API_SKILL_MAP = {
    "typescript": "typescript",
    "javascript": "javascript",
    "python": "python",
    "react": "react",
    "react native": "react-native",
    "node.js": "nodejs",
    "next.js": "nextjs",
    "nestjs": "nestjs",
    "docker": "docker",
    "sql": "sql",
    "postgresql": "postgresql",
    "aws lambda": "aws",
    "amazon ecs": "aws",
    "figma": "figma",
    "graphql": "graphql",
    "c#": "csharp",
}


def api_tags_from_profile(profile: ProfileSchema, max_tags: int = 5) -> list[str]:
    """Return a deduplicated list of API-friendly tag strings derived from profile skills."""
    tags: list[str] = []
    seen: set[str] = set()
    for skill in profile.skills:
        tag = _API_SKILL_MAP.get(skill.lower())
        if tag and tag not in seen:
            tags.append(tag)
            seen.add(tag)
        if len(tags) >= max_tags:
            break
    return tags


class BaseConnector(ABC):
    name: str

    default_limit: int = 100

    @abstractmethod
    async def fetch_jobs(self, profile: ProfileSchema, limit: int = 100) -> list[JobPosition]: ...
