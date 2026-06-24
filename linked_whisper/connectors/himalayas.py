from datetime import datetime
import httpx
from .base import BaseConnector
from ..schemas.job import JobPosition


class HimalayasConnector(BaseConnector):
    name = "himalayas"
    _url = "https://himalayas.app/jobs/api"

    async def fetch_jobs(self) -> list[JobPosition]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self._url, params={"limit": 100})
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
