from datetime import datetime
import httpx
from .base import BaseConnector, api_tags_from_profile
from ..schemas.job import JobPosition
from ..schemas.profile import ProfileSchema


class JobicyConnector(BaseConnector):
    name = "jobicy"
    _url = "https://jobicy.com/api/v2/remote-jobs"

    default_limit: int = 50

    async def fetch_jobs(self, profile: ProfileSchema, limit: int = 50) -> list[JobPosition]:
        tags = api_tags_from_profile(profile)
        # Jobicy tag param accepts a single value; use the first mapped skill
        params: dict = {"count": limit}
        if tags:
            params["tag"] = tags[0]
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self._url, params=params)
            response.raise_for_status()
            data = response.json()

        jobs = []
        for item in data.get("jobs", []):
            posted_at = None
            if item.get("pubDate"):
                try:
                    posted_at = datetime.fromisoformat(item["pubDate"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            tags = item.get("jobIndustry", [])
            if isinstance(tags, str):
                tags = [tags]
            skills = item.get("jobSkills", [])
            if isinstance(skills, str):
                skills = [s.strip() for s in skills.split(",") if s.strip()]
            jobs.append(JobPosition(
                id=str(item["id"]),
                source=self.name,
                title=item.get("jobTitle", ""),
                company=item.get("companyName", ""),
                description=item.get("jobDescription", ""),
                tags=list(set(tags + skills)),
                location=item.get("jobGeo") or "Remote",
                salary_min=None,
                salary_max=None,
                url=item.get("url", ""),
                posted_at=posted_at,
            ))
        return jobs
