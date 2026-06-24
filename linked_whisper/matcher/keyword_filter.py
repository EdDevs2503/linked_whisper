from ..schemas.job import JobPosition
from ..schemas.profile import ProfileSchema


def _normalize(text: str) -> str:
    return text.lower().strip()


def keyword_score(job: JobPosition, profile: ProfileSchema) -> float:
    job_text = _normalize(f"{job.title} {' '.join(job.tags)} {job.description[:500]}")

    for kw in profile.excluded_keywords:
        if _normalize(kw) in job_text:
            return 0.0

    profile_terms = [_normalize(s) for s in profile.skills + profile.preferred_roles]
    if not profile_terms:
        return 0.5

    matched = sum(1 for term in profile_terms if term in job_text)
    return matched / len(profile_terms)


def passes_keyword_filter(job: JobPosition, profile: ProfileSchema, threshold: float) -> bool:
    return keyword_score(job, profile) >= threshold
