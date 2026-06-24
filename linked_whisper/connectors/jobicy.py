from datetime import datetime
import httpx
from .base import BaseConnector
from ..schemas.job import JobPosition


class JobicyConnector(BaseConnector):
    name = "jobicy"
    _url = "https://jobicy.com/api/v2/remote-jobs"

    async def fetch_jobs(self) -> list[JobPosition]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self._url, params={"count": 50})
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
