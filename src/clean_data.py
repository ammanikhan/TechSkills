
"""Clean Hacker News Who is Hiring comments for analysis."""

import json
import re
from pathlib import Path
from html import unescape

import pandas as pd


SKILLS = [
    "python", "java", "javascript", "typescript", "react",
    "node.js", "sql", "postgresql", "aws", "docker",
    "kubernetes", "go", "rust", "c++", "ruby", "rails",
    "tensorflow", "pytorch", "machine learning", "llm",
    "generative ai", "git", "linux", "scala", "swift",
    "flutter"
]

PATTERNS = {
    skill: re.compile(
        r"(?<!\w)" + re.escape(skill) + r"(?!\w)",
        re.I
    )
    for skill in SKILLS
}

ROLE_WORDS = re.compile(
    r"\b(engineer|developer|designer|scientist|analyst|"
    r"architect|manager|intern|researcher|devops|"
    r"frontend|backend|full.stack|software|security|"
    r"data|product|sre|qa|roles?|positions?)\b",
    re.I
)

LOCATION_WORDS = re.compile(
    r"\b(remote|hybrid|onsite|on.site|"
    r"new york|nyc|san francisco|seattle|chicago|"
    r"boston|austin|london|berlin|munich|münchen|"
    r"india|germany|canada|usa|united states|"
    r"europe|worldwide|global|sf|bay area)\b",
    re.I
)

EMPLOYMENT_WORDS = re.compile(
    r"^(full.time|part.time|contract|contractor|"
    r"permanent|temporary|freelance|internship)$",
    re.I
)

URL_PATTERN = re.compile(r"https?://\S+", re.I)


def strip_html(value):
    """Remove HTML while preserving paragraph boundaries."""
    value = value or ""
    value = re.sub(
        r"</?(?:p|div|br|li)\b[^>]*>",
        "\n",
        value,
        flags=re.I
    )
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n\s*\n+", "\n", value)
    return value.strip()


def normalize_field(value):
    """Remove URLs and clean whitespace."""
    value = URL_PATTERN.sub("", value or "")
    value = re.sub(r"\(\s*\)", "", value)
    value = re.sub(r"\s+", " ", value).strip(" |,;-")
    return value or None


def looks_like_role(value):
    """Check whether a header segment resembles a job title."""
    if not value:
        return False

    if EMPLOYMENT_WORDS.fullmatch(value.strip()):
        return False

    if not ROLE_WORDS.search(value):
        return False

    return True


def looks_like_location(value):
    """Check whether a header segment resembles a location."""
    if not value:
        return False

    if LOCATION_WORDS.search(value):
        return True

    # Examples: Ithaca, NY / Portland, OR
    if re.search(r"\b[A-Za-z .]+,\s*[A-Z]{2}\b", value):
        return True

    return False


def extract_job_details(text):
    """Extract likely company, role and location from header."""
    if not text:
        return None, None, None

    # Use only the first paragraph to avoid capturing
    # the entire job description as a header.
    header = text.split("\n", 1)[0][:350]

    parts = [
        normalize_field(part)
        for part in header.split("|")
    ]
    parts = [part for part in parts if part]

    if len(parts) < 2:
        return None, None, None

    company = parts[0]
    role = None
    location = None

    # The first segment is normally the company name.
    # Examine the remaining header segments.
    for part in parts[1:6]:

        if EMPLOYMENT_WORDS.fullmatch(part):
            continue

        if len(part) > 100:
            continue

        is_role = looks_like_role(part)
        is_location = looks_like_location(part)

        if is_role and not is_location and role is None:
            role = part

        elif is_location and not is_role and location is None:
            location = part

        elif is_role and is_location:
            # A segment can contain both, such as
            # "Remote Software Engineer".
            if role is None:
                role = part
            if location is None:
                location = part

    return company, role, location


def extract_skills(text):
    """Find technologies mentioned in a posting."""
    return ", ".join(
        skill
        for skill, pattern in PATTERNS.items()
        if pattern.search(text)
    )


def extract_work_mode(text):
    """Classify work arrangement using the posting header."""
    header = text.split("\n", 1)[0][:350].lower()

    if re.search(r"\bhybrid\b", header):
        return "hybrid"

    if re.search(
        r"\b(no remote|not remote|remote not available)\b",
        header
    ):
        return "onsite"

    if re.search(r"\bremote\b", header):
        return "remote"

    if re.search(r"\b(on.site|onsite|in.office)\b", header):
        return "onsite"

    return "unknown"


def is_likely_job_post(text):
    """Flag comments that resemble hiring advertisements."""
    if not text:
        return False

    header = text.split("\n", 1)[0][:350]

    # Most HN hiring advertisements have pipe-separated
    # headers with company, role, and location.
    if "|" in header and (
        ROLE_WORDS.search(header)
        or LOCATION_WORDS.search(header)
    ):
        return True

    # Also accept posts with explicit hiring language.
    if re.search(
        r"\b(we are hiring|we're hiring|"
        r"we are looking for|open positions|"
        r"join our team)\b",
        text,
        re.I
    ):
        return True

    return False


def clean(
    source="data/raw/hn_jobs.jsonl",
    dest="data/processed/jobs_cleaned.csv"
):
    records = []

    with Path(source).open("r", encoding="utf-8") as file:
        for line in file:
            obj = json.loads(line)

            content = strip_html(obj.get("text"))

            if len(content) < 30:
                continue

            date = pd.to_datetime(
                obj.get("created_at"),
                utc=True,
                errors="coerce"
            )

            company, role, location = extract_job_details(
                content
            )

            skills = extract_skills(content)
            work_mode = extract_work_mode(content)

            records.append({
                "id": obj["id"],
                "thread_id": obj["thread_id"],
                "date": date,
                "year": date.year if pd.notna(date) else None,
                "month": date.month if pd.notna(date) else None,
                "company": company,
                "role": role,
                "location": location,
                "remote": work_mode == "remote",
                "work_mode": work_mode,
                "salary": None,
                "skills": skills,
                "skill_count": len(
                    [s for s in skills.split(", ") if s]
                ),
                "is_likely_job": is_likely_job_post(content),
                "text": content
            })

    df = pd.DataFrame.from_records(records)

    if df.empty:
        raise ValueError("No records found.")

    # Remove duplicates
    df = df.drop_duplicates(subset=["id"])

    # Remove records without valid dates
    df = df.dropna(subset=["date"])

    # Sort chronologically
    df = df.sort_values("date").reset_index(drop=True)

    # Create output folder
    Path(dest).parent.mkdir(parents=True, exist_ok=True)

    # Save all records, including those needing review
    df.to_csv(dest, index=False)

    print(f"\nSaved {len(df):,} posts to {dest}")

    print("\nDate range:")
    print(df["date"].min(), "to", df["date"].max())

    print("\nMissing values:")
    print(df.isna().sum())

    print("\nPosts with recognized skills:")
    print((df["skill_count"] > 0).sum())

    print("\nLikely hiring posts:")
    print(df["is_likely_job"].value_counts())

    print("\nWork modes:")
    print(df["work_mode"].value_counts())

    print("\nSample job details:")
    print(
        df[
            ["company", "role", "location", "work_mode"]
        ].head(10).to_string(index=False, max_colwidth=55)
    )


if __name__ == "__main__":
    clean()
