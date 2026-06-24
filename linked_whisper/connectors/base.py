from abc import ABC, abstractmethod
from ..schemas.job import JobPosition


class BaseConnector(ABC):
    name: str

    @abstractmethod
    async def fetch_jobs(self) -> list[JobPosition]: ...
