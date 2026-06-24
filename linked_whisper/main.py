import asyncio
import json
from pathlib import Path
from typing import Optional
import typer

from .schemas.profile import ProfileSchema
from .connectors.remoteok import RemoteOKConnector
from .connectors.himalayas import HimalayasConnector
from .connectors.remotive import RemotiveConnector
from .connectors.working_nomads import WorkingNomadsConnector
from .connectors.jobicy import JobicyConnector
from .matcher.keyword_filter import passes_keyword_filter, keyword_score
from .matcher.llm_matcher import llm_match
from .storage.database import init_db, save_match, save_evaluation, list_matches, already_matched
from .schema_generator.generator import generate_profile
from . import config

app = typer.Typer(help="LinkedWhisper — AI-powered remote job matcher")

ALL_CONNECTORS = {
    "remoteok": RemoteOKConnector,
    "himalayas": HimalayasConnector,
    "remotive": RemotiveConnector,
    "working_nomads": WorkingNomadsConnector,
    "jobicy": JobicyConnector,
}


@app.command("generate-schema")
def generate_schema(
    resume: Path = typer.Option(..., help="Path to resume text file"),
    output: Path = typer.Option(Path("profile.json"), help="Output path for profile JSON"),
):
    """Generate a ProfileSchema from a resume using Claude."""

    async def _run():
        text = resume.read_text(encoding="utf-8")
        typer.echo(f"Generating profile schema from {resume}...")
        profile = await generate_profile(text)
        output.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
        typer.echo(f"Profile saved to {output}")
        typer.echo(f"  Name: {profile.name}")
        typer.echo(f"  Title: {profile.title}")
        typer.echo(f"  Skills ({len(profile.skills)}): {', '.join(profile.skills[:8])}{'...' if len(profile.skills) > 8 else ''}")

    asyncio.run(_run())


@app.command("run")
def run(
    profile: Path = typer.Option(Path("profile.json"), help="Path to profile JSON"),
    connectors: str = typer.Option(
        ",".join(ALL_CONNECTORS.keys()),
        help="Comma-separated list of connectors to use",
    ),
    dry_run: bool = typer.Option(False, help="Fetch and filter jobs without saving or calling LLM"),
    skip_existing: bool = typer.Option(True, help="Skip jobs already saved in the database"),
):
    """Fetch jobs from connectors and match against your profile."""

    async def _run():
        await init_db()

        profile_data = json.loads(profile.read_text(encoding="utf-8"))
        prof = ProfileSchema(**profile_data)
        typer.echo(f"Loaded profile: {prof.name} — {prof.title}")

        selected = [c.strip() for c in connectors.split(",") if c.strip() in ALL_CONNECTORS]
        if not selected:
            typer.echo(f"No valid connectors. Choose from: {', '.join(ALL_CONNECTORS)}", err=True)
            raise typer.Exit(1)

        all_jobs = []
        for name in selected:
            connector = ALL_CONNECTORS[name]()
            typer.echo(f"Fetching from {name}...")
            try:
                jobs = await connector.fetch_jobs()
                typer.echo(f"  {len(jobs)} jobs fetched")
                all_jobs.extend(jobs)
            except Exception as e:
                typer.echo(f"  Error: {e}", err=True)

        typer.echo(f"\nTotal jobs fetched: {len(all_jobs)}")

        # Phase 1: keyword filter
        candidates = []
        for job in all_jobs:
            score = keyword_score(job, prof)
            if score >= config.KEYWORD_FILTER_THRESHOLD:
                candidates.append(job)

        typer.echo(f"After keyword filter ({config.KEYWORD_FILTER_THRESHOLD}): {len(candidates)} candidates")

        if dry_run:
            typer.echo("\n[dry-run] Skipping LLM evaluation and storage.")
            for job in candidates[:20]:
                typer.echo(f"  [{job.source}] {job.title} @ {job.company}")
            return

        # Phase 2: LLM matching
        typer.echo("Running LLM evaluation...")
        matched = []
        for i, job in enumerate(candidates, 1):
            if skip_existing and await already_matched(job.id, job.source):
                continue
            result = await llm_match(job, prof)
            await save_evaluation(job.id, job.source, result.score)
            status = "MATCH" if result.match else "skip"
            typer.echo(f"  [{i}/{len(candidates)}] {status} ({result.score:.2f}) {job.title} @ {job.company}")
            if result.match and result.score >= config.LLM_MATCH_THRESHOLD:
                await save_match(job, result.score, result.reason)
                matched.append((job, result))

        typer.echo(f"\nMatched and saved: {len(matched)} jobs")
        for job, result in matched:
            typer.echo(f"  {job.title} @ {job.company} [{result.score:.2f}] — {result.reason}")
            typer.echo(f"    {job.url}")

    asyncio.run(_run())


@app.command("list-matches")
def list_matches_cmd(
    min_score: float = typer.Option(0.0, help="Minimum match score (0.0-1.0)"),
    limit: Optional[int] = typer.Option(None, help="Max number of results to show"),
):
    """List saved job matches from the database."""

    async def _run():
        matches = await list_matches(min_score=min_score)
        if limit:
            matches = matches[:limit]
        if not matches:
            typer.echo("No matches found.")
            return
        typer.echo(f"Found {len(matches)} match(es) (score >= {min_score}):\n")
        for m in matches:
            typer.echo(f"[{m.score:.2f}] {m.title} @ {m.company}  ({m.source})")
            typer.echo(f"  {m.url}")
            typer.echo(f"  {m.reason}")
            typer.echo()

    asyncio.run(_run())


if __name__ == "__main__":
    app()
