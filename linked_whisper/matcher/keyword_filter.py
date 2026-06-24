import re
from ..schemas.job import JobPosition
from ..schemas.profile import ProfileSchema

# Title must contain at least one of these for the job to be considered engineering.
_ENGINEERING_TITLE_TERMS = {
    "engineer", "developer", "architect", "programmer", "frontend", "backend",
    "fullstack", "full-stack", "full stack", "mobile", "ios", "android",
    "software", "ai", "ml", "llm", "devops", "sre", "platform", "tech lead",
    "staff", "principal",
}

# Known primary-tech discriminators: if any appear in the title, the job is
# primarily about that tech. We reject it unless the profile claims that skill.
_TECH_DISCRIMINATORS: dict[str, set[str]] = {
    # token in title -> set of profile skill substrings that would allow it
    "golang":       {"golang", "go"},
    "rust":         {"rust"},
    "flutter":      {"flutter"},
    "rails":        {"rails", "ruby on rails"},
    "ruby":         {"ruby", "rails"},
    "php":          {"php", "laravel"},
    "laravel":      {"laravel", "php"},
    "wordpress":    {"wordpress"},
    "elixir":       {"elixir"},
    "kotlin":       {"kotlin", "android"},
    "swift":        {"swift", "ios"},
    "scala":        {"scala"},
    "django":       {"django", "python"},
    "flask":        {"flask", "python"},
    "angular":      {"angular"},
    "vue":          {"vue"},
    "java":         {"java"},
    "spring":       {"spring", "java"},
    "dotnet":       {".net", "c#"},
    ".net":         {".net", "c#"},
    "salesforce":   {"salesforce"},
    "sap":          {"sap"},
    "cobol":        {"cobol"},
}


def _normalize(text: str) -> str:
    return text.lower().strip()


def _word_match(term: str, text: str) -> bool:
    pattern = r'\b' + re.escape(term) + r'\b'
    return bool(re.search(pattern, text))


# Locations that mean "open to everyone" — no country restriction.
_WORLDWIDE_TERMS = {"worldwide", "anywhere", "global", "anywhere in the world", "distributed"}

# Single-country restrictions. A job listing only one of these is not open worldwide.
# Multi-region strings like "Americas, Europe" are allowed through — the LLM evaluates those.
_SINGLE_COUNTRY_RESTRICTIONS = {
    "usa", "united states", "u.s.", "us only", "us-only",
    "canada", "uk", "united kingdom", "germany", "france", "spain",
    "australia", "india", "brazil", "brasil", "mexico",
    "portugal", "colombia", "argentina", "chile", "peru",
    "netherlands", "sweden", "poland", "italy",
}


def _is_location_compatible(job: JobPosition, profile: ProfileSchema) -> bool:
    if "remote" not in [w.lower() for w in profile.work_type]:
        return True  # no location preference, allow everything

    location = _normalize(job.location or "")

    # No location info → unknown, let LLM evaluate
    if not location:
        return True

    # Explicitly worldwide → allow
    if any(term in location for term in _WORLDWIDE_TERMS):
        return True

    # Single country restriction → reject
    # Only reject if the ENTIRE location is one country (not part of a multi-region list)
    location_parts = [p.strip() for p in location.split(",")]
    if len(location_parts) == 1 and location_parts[0] in _SINGLE_COUNTRY_RESTRICTIONS:
        return False

    # Multi-region ("Americas, Europe, Israel") or plain "remote" → let LLM decide
    return True


def _profile_skill_set(profile: ProfileSchema) -> set[str]:
    return {s.lower() for s in profile.skills + profile.excluded_keywords}


def keyword_score(job: JobPosition, profile: ProfileSchema) -> float:
    title = _normalize(job.title)

    # Reject anything whose title doesn't look like an engineering role.
    if not any(t in title for t in _ENGINEERING_TITLE_TERMS):
        return 0.0

    # Reject jobs whose location is incompatible with the profile's work_type.
    if not _is_location_compatible(job, profile):
        return 0.0

    # Reject titles that name a primary tech stack not represented in the profile.
    profile_skills = _profile_skill_set(profile)
    for token, allowed_skills in _TECH_DISCRIMINATORS.items():
        if _word_match(token, title) and not allowed_skills.intersection(profile_skills):
            return 0.0

    job_text = _normalize(f"{title} {' '.join(job.tags)} {job.description[:500]}")

    for kw in profile.excluded_keywords:
        if _word_match(_normalize(kw), job_text):
            return 0.0

    profile_terms = [_normalize(s) for s in profile.skills + profile.preferred_roles]
    if not profile_terms:
        return 0.5

    matched = sum(1 for term in profile_terms if _word_match(term, job_text))
    # Cap denominator so broad skill lists don't make every score near-zero.
    # With denominator=5: 1 match → 0.2 (passes default threshold), 0 → filtered out.
    denominator = min(len(profile_terms), 5)
    return min(matched / denominator, 1.0)


def passes_keyword_filter(job: JobPosition, profile: ProfileSchema, threshold: float) -> bool:
    return keyword_score(job, profile) >= threshold
