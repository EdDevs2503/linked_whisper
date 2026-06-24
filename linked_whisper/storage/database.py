from dataclasses import dataclass
from datetime import datetime, timezone
import aiosqlite
from ..schemas.job import JobPosition
from .. import config


@dataclass
class JobMatch:
    id: str
    source: str
    title: str
    company: str
    url: str
    score: float
    reason: str
    matched_at: datetime
    raw_json: str


CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS job_matches (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    url TEXT NOT NULL,
    score REAL NOT NULL,
    reason TEXT,
    matched_at TIMESTAMP NOT NULL,
    raw_json TEXT NOT NULL
)
"""

CREATE_EVALUATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS job_evaluations (
    id TEXT PRIMARY KEY,
    score REAL NOT NULL,
    evaluated_at TIMESTAMP NOT NULL
)
"""


async def init_db(db_path: str = config.DB_PATH) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_TABLE)
        await db.execute(CREATE_EVALUATIONS_TABLE)
        await db.commit()


async def save_match(
    job: JobPosition,
    score: float,
    reason: str,
    db_path: str = config.DB_PATH,
) -> None:
    record_id = f"{job.source}:{job.id}"
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO job_matches
                (id, source, title, company, url, score, reason, matched_at, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                job.source,
                job.title,
                job.company,
                job.url,
                score,
                reason,
                datetime.now(timezone.utc).isoformat(),
                job.model_dump_json(),
            ),
        )
        await db.commit()


async def list_matches(
    min_score: float = 0.0,
    db_path: str = config.DB_PATH,
) -> list[JobMatch]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM job_matches WHERE score >= ? ORDER BY score DESC, matched_at DESC",
            (min_score,),
        ) as cursor:
            rows = await cursor.fetchall()
    return [
        JobMatch(
            id=row["id"],
            source=row["source"],
            title=row["title"],
            company=row["company"],
            url=row["url"],
            score=row["score"],
            reason=row["reason"],
            matched_at=datetime.fromisoformat(row["matched_at"]),
            raw_json=row["raw_json"],
        )
        for row in rows
    ]


async def save_evaluation(
    job_id: str,
    source: str,
    score: float,
    db_path: str = config.DB_PATH,
) -> None:
    record_id = f"{source}:{job_id}"
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO job_evaluations (id, score, evaluated_at) VALUES (?, ?, ?)",
            (record_id, score, datetime.now(timezone.utc).isoformat()),
        )
        await db.commit()


async def already_matched(job_id: str, source: str, db_path: str = config.DB_PATH) -> bool:
    record_id = f"{source}:{job_id}"
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT 1 FROM job_evaluations WHERE id = ?", (record_id,)
        ) as cursor:
            return await cursor.fetchone() is not None
