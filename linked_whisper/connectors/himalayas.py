from datetime import datetime
import httpx
from .base import BaseConnector, api_tags_from_profile
from ..schemas.job import JobPosition
from ..schemas.profile import ProfileSchema


class HimalayasConnector(BaseConnector):
    name = "himalayas"
    _url = "https://himalayas.app/jobs/api"

    async def fetch_jobs(self, profile: ProfileSchema, limit: int = 100) -> list[JobPosition]:
        tags = api_tags_from_profile(profile)
        params: dict = {"limit": limit}
        if tags:
            params["q"] = " ".join(tags[:3])
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self._url, params=params)
            response.raise_for_status()
            data = response.json()

        jobs = []
        for item in data.get("jobs", []):
            posted_at = None
            if item.get("pubDate"):
                try:
                    pub = item["pubDate"]
                    if isinstance(pub, int):
                        posted_at = datetime.fromtimestamp(pub / 1000 if pub > 1e10 else pub)
                    else:
                        posted_at = datetime.fromisoformat(str(pub).replace("Z", "+00:00"))
                except (ValueError, OSError):
                    pass
            tags = [t.get("name", "") for t in item.get("skills", [])]
            jobs.append(JobPosition(
                id=str(item.get("id", item.get("slug", ""))),
                source=self.name,
                title=item.get("title", ""),
                company=item.get("companyName", ""),
                description=item.get("description", ""),
                tags=tags,
                location=item.get("locationRestrictions", ["Remote"])[0] if item.get("locationRestrictions") else "Remote",
                salary_min=item.get("salaryMin"),
                salary_max=item.get("salaryMax"),
                url=item.get("applicationLink", f"https://himalayas.app/jobs/{item.get('slug', '')}"),
                posted_at=posted_at,
            ))
        return jobs
