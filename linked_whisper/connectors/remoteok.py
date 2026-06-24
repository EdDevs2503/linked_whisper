from datetime import datetime
import httpx
from .base import BaseConnector
from ..schemas.job import JobPosition


class RemoteOKConnector(BaseConnector):
    name = "remoteok"
    _url = "https://remoteok.com/api"

    async def fetch_jobs(self) -> list[JobPosition]:
        async with httpx.AsyncClient(headers={"User-Agent": "LinkedWhisper/1.0"}, timeout=30) as client:
            response = await client.get(self._url)
            response.raise_for_status()
            data = response.json()

        jobs = []
        for item in data:
            if not isinstance(item, dict) or "id" not in item:
                continue
            posted_at = None
            if item.get("date"):
                try:
                    posted_at = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            jobs.append(JobPosition(
                id=str(item["id"]),
                source=self.name,
                title=item.get("position", ""),
                company=item.get("company", ""),
                description=item.get("description", ""),
                tags=item.get("tags", []),
                location=item.get("location") or "Remote",
                salary_min=item.get("salary_min"),
                salary_max=item.get("salary_max"),
                url=item.get("url", f"https://remoteok.com/remote-jobs/{item['id']}"),
                posted_at=posted_at,
            ))
        return jobs
