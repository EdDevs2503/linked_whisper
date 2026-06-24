from datetime import datetime
import httpx
from .base import BaseConnector
from ..schemas.job import JobPosition


class RemotiveConnector(BaseConnector):
    name = "remotive"
    _url = "https://remotive.com/api/remote-jobs"

    async def fetch_jobs(self) -> list[JobPosition]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self._url, params={"limit": 100})
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
