from datetime import datetime
import httpx
from .base import BaseConnector
from ..schemas.job import JobPosition
from ..schemas.profile import ProfileSchema


_DEV_CATEGORIES = {"development", "programming", "engineering", "software", "devops", "mobile", "ai", "data"}


class WorkingNomadsConnector(BaseConnector):
    name = "working_nomads"
    _url = "https://www.workingnomads.com/api/exposed_jobs/"

    async def fetch_jobs(self, profile: ProfileSchema, limit: int = 100) -> list[JobPosition]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self._url)
            response.raise_for_status()
            data = response.json()

        jobs = []
        for item in data:
            category = item.get("category_name", "").lower()
            if not any(c in category for c in _DEV_CATEGORIES):
                continue

            posted_at = None
            if item.get("pub_date"):
                try:
                    posted_at = datetime.fromisoformat(item["pub_date"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            url = item.get("url", "")
            job_id = url.rstrip("/").split("/")[-1] or url
            tags = [t.strip() for t in item.get("tags", "").split(",") if t.strip()]
            jobs.append(JobPosition(
                id=job_id,
                source=self.name,
                title=item.get("title", ""),
                company=item.get("company_name", ""),
                description=item.get("description", ""),
                tags=tags,
                location=item.get("location") or "Remote",
                salary_min=None,
                salary_max=None,
                url=url,
                posted_at=posted_at,
            ))
        return jobs[:limit]
