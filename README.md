# LinkedWhisper

AI-powered remote job matcher. You give it your resume; it searches multiple job boards, filters by keywords, and uses Claude to score each posting against your profile — keeping only the jobs worth reading.

## What it does

1. **Generates your profile** from a plain-text resume using Claude. Extracts skills, preferred roles, salary floor, and keywords to exclude.
2. **Searches job boards** across five sources simultaneously: RemoteOK, Himalayas, Remotive, Working Nomads, and Jobicy.
3. **Filters by keyword** — a fast pre-pass that drops postings that don't mention your skills or mention things you've excluded.
4. **Scores with Claude** — every posting that passes the keyword filter is evaluated by an LLM that gives it a match score (0–1) and a one-sentence reason.
5. **Persists matches** in a local SQLite database so you can query them later and avoid re-evaluating the same job twice.

## What to expect

- Typical run: 50–200 raw postings → keyword filter drops ~70% → Claude scores the rest → 5–30 matched jobs stored.
- LLM scoring costs a few cents per run depending on how many postings clear the keyword filter.
- Results are stored locally; nothing is sent anywhere except the Anthropic API.

## Setup

**Prerequisites:** Python 3.11+, [Poetry](https://python-poetry.org/docs/#installation)

```bash
# Install dependencies
poetry install

# Copy and fill in your API key
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

### 1. Generate your profile schema

Point it at a plain-text resume file:

```bash
poetry run linked-whisper generate-schema resume.txt
# → Writes profile.json in the current directory
```

Review `profile.json` and tweak anything before running the search. The `excluded_keywords` field is particularly important — add technologies or role types you don't want.

### 2. Search and match jobs

```bash
poetry run linked-whisper search --profile profile.json
```

By default this searches all five job boards. To limit sources:

```bash
poetry run linked-whisper search --profile profile.json --sources remoteok,himalayas
```

You'll see live output as each posting is evaluated. Matches at or above the threshold (default: 0.6) are saved to the local database.

### 3. List saved matches

```bash
poetry run linked-whisper list-matches
```

Shows all stored matches sorted by score, with the Claude-generated reason for each.

## Configuration

All settings live in `.env` (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required. Your Anthropic API key. |
| `KEYWORD_FILTER_THRESHOLD` | `0.2` | Minimum keyword score (0–1) to pass pre-filter. Lower = more postings reach Claude. |
| `LLM_MATCH_THRESHOLD` | `0.6` | Minimum Claude score to store a match. |
| `DB_PATH` | `linked_whisper.db` | Path to the SQLite database file. |

## Job board connectors

| Source | What it covers |
|---|---|
| RemoteOK | Engineering, design, marketing remote roles |
| Himalayas | Curated fully-remote positions |
| Remotive | Remote tech jobs with salary data |
| Working Nomads | Location-flexible roles across categories |
| Jobicy | Remote-first companies |
