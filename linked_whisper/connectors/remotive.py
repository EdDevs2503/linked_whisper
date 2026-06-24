from datetime import datetime
import httpx
from .base import BaseConnector, api_tags_from_profile
from ..schemas.job import JobPosition
from ..schemas.profile import ProfileSchema


class RemotiveConnector(BaseConnector):
    name = "remotive"
    _url = "https://remotive.com/api/remote-jobs"

    async def fetch_jobs(self, profile: ProfileSchema, limit: int = 100) -> list[JobPosition]:
        tags = api_tags_from_profile(profile)
        params: dict = {"limit": limit, "category": "software-dev"}
        if tags:
            params["search"] = " ".join(tags[:3])
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self._url, params=params)
            response.raise_for_status()
            data = response.json()

        jobs = []
        for item in data.get("jobs", []):
            posted_at = None
            if item.get("publication_date"):
                try:
                    posted_at = datetime.fromisoformat(item["publication_date"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            tags = [t.strip() for t in item.get("tags", [])]
            jobs.append(JobPosition(
                id=str(item["id"]),
                source=self.name,
                title=item.get("title", ""),
                company=item.get("company_name", ""),
                description=item.get("description", ""),
                tags=tags,
                location=item.get("candidate_required_location") or "Remote",
                salary_min=None,
                salary_max=None,
                url=item.get("url", ""),
                posted_at=posted_at,
            ))
        return jobs
