from datetime import datetime
import httpx
from .base import BaseConnector
from ..schemas.job import JobPosition


class WorkingNomadsConnector(BaseConnector):
    name = "working_nomads"
    _url = "https://www.workingnomads.com/api/published_jobs/"

    async def fetch_jobs(self) -> list[JobPosition]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self._url)
            response.raise_for_status()
            data = response.json()

        jobs = []
        for item in data:
            posted_at = None
            if item.get("pub_date"):
                try:
                    posted_at = datetime.fromisoformat(item["pub_date"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            tags = [t.strip() for t in item.get("tags", "").split(",") if t.strip()]
            jobs.append(JobPosition(
                id=str(item["id"]),
                source=self.name,
                title=item.get("title", ""),
                company=item.get("company", ""),
                description=item.get("description", ""),
                tags=tags,
                location=item.get("region") or "Remote",
                salary_min=None,
                salary_max=None,
                url=item.get("url", ""),
                posted_at=posted_at,
            ))
        return jobs
