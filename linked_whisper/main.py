import asyncio
import json
import re
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from .schemas.profile import ProfileSchema
from .connectors.remoteok import RemoteOKConnector
from .connectors.himalayas import HimalayasConnector
from .connectors.remotive import RemotiveConnector
from .connectors.working_nomads import WorkingNomadsConnector
from .connectors.jobicy import JobicyConnector
from .matcher.keyword_filter import keyword_score
from .schema_generator.generator import generate_profile
from . import config

app = typer.Typer(help="LinkedWhisper — remote job matcher")

ALL_CONNECTORS = {
    "remoteok": RemoteOKConnector,
    "himalayas": HimalayasConnector,
    "remotive": RemotiveConnector,
    "working_nomads": WorkingNomadsConnector,
    "jobicy": JobicyConnector,
}


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


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
):
    """Fetch jobs, filter by profile, and print matching candidates."""

    async def _run():
        profile_data = json.loads(profile.read_text(encoding="utf-8"))
        prof = ProfileSchema(**profile_data)
        typer.echo(f"Loaded profile: {prof.name} — {prof.title}\n")

        selected = [c.strip() for c in connectors.split(",") if c.strip() in ALL_CONNECTORS]
        if not selected:
            typer.echo(f"No valid connectors. Choose from: {', '.join(ALL_CONNECTORS)}", err=True)
            raise typer.Exit(1)

        all_jobs = []
        for name in selected:
            connector = ALL_CONNECTORS[name]()
            typer.echo(f"Fetching from {name}...")
            try:
                jobs = await connector.fetch_jobs(prof)
                typer.echo(f"  {len(jobs)} jobs fetched")
                all_jobs.extend(jobs)
            except Exception as e:
                typer.echo(f"  Error: {e}", err=True)

        typer.echo(f"\nTotal jobs fetched: {len(all_jobs)}")

        candidates = [
            job for job in all_jobs
            if keyword_score(job, prof) >= config.KEYWORD_FILTER_THRESHOLD
        ]

        typer.echo(f"After keyword filter: {len(candidates)} candidates\n")

        if not candidates:
            typer.echo("No candidates found. Try adjusting your profile or lowering KEYWORD_FILTER_THRESHOLD.")
            return

        console = Console()
        table = Table(show_header=True, header_style="bold cyan", show_lines=True, expand=True)
        table.add_column("#", style="dim", width=3, no_wrap=True)
        table.add_column("Title & Company", min_width=30)
        table.add_column("Summary", min_width=40)
        table.add_column("URL", min_width=30, no_wrap=False)

        for i, job in enumerate(candidates, 1):
            summary = _strip_html(job.description)[:200]
            if len(_strip_html(job.description)) > 200:
                summary += "…"
            table.add_row(
                str(i),
                f"{job.title}\n[dim]{job.company}[/dim]",
                summary,
                job.url,
            )

        console.print(table)

    asyncio.run(_run())


if __name__ == "__main__":
    app()
