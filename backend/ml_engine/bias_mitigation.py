"""
BIAS MITIGATION MODULE

Removes personal identifiers that can cause discrimination:
  - Names (gender inference)
  - Gender pronouns (he/she/him/her)
  - Age indicators
  - Photos (already handled — PDF text has no photos)
  - University prestige bias (normalize institution names)
  - Marital status, religion, nationality

Uses: Fairlearn concepts + custom regex-based anonymization.
Applied BEFORE feature engineering so ML models never see biased data.
"""
import re
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# ─── Bias Patterns to Remove ─────────────────────────────

GENDER_PRONOUNS = [
    r"\bhe\b", r"\bshe\b", r"\bhim\b", r"\bher\b", r"\bhis\b",
    r"\bherself\b", r"\bhimself\b", r"\bmr\.?\b", r"\bmrs\.?\b",
    r"\bms\.?\b", r"\bmiss\b", r"\bsir\b", r"\bmadam\b",
]

AGE_PATTERNS = [
    r"\b\d{1,2}\s*years?\s*old\b",
    r"\bage[d]?\s*:?\s*\d{1,2}\b",
    r"\bborn\s+(?:in\s+)?\d{4}\b",
    r"\bdate\s+of\s+birth\s*:?\s*[\d/\-\.]+\b",
    r"\bdob\s*:?\s*[\d/\-\.]+\b",
]

PERSONAL_PATTERNS = [
    r"\bmarried\b", r"\bsingle\b", r"\bdivorced\b", r"\bwidowed\b",
    r"\breligion\s*:?\s*\w+\b",
    r"\bnationality\s*:?\s*\w+\b",
    r"\bgender\s*:?\s*\w+\b",
    r"\bsex\s*:?\s*\w+\b",
    r"\bfather['\u2019]?s?\s+name\s*:?\s*[\w\s]+\b",
    r"\bmother['\u2019]?s?\s+name\s*:?\s*[\w\s]+\b",
]

# Common name patterns (first line of CV is usually the name)
NAME_PATTERN = r"^[\s]*[A-Z][a-z]+\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]+[\s]*$"

# Photo-related (in case CV text mentions it)
PHOTO_PATTERNS = [
    r"\bphoto\s*:?\s*(?:attached|enclosed|included)\b",
    r"\bphotograph\b",
    r"\bpassport\s*(?:size)?\s*photo\b",
]


def remove_names(text: str) -> str:
    """Remove candidate name (typically first 1-2 lines of CV)."""
    lines = text.split("\n")
    cleaned_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        # First 3 lines: remove if looks like a name (2-4 capitalized words)
        if i < 3 and re.match(r"^[A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+){0,2}\s*$", stripped):
            cleaned_lines.append("[NAME REMOVED]")
        # Also remove "Name: John Doe" patterns anywhere
        elif re.match(r"(?i)^name\s*:?\s*", stripped):
            cleaned_lines.append("[NAME REMOVED]")
        else:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def remove_gender_indicators(text: str) -> str:
    """Remove gender pronouns and titles."""
    result = text
    for pattern in GENDER_PRONOUNS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    return result


def remove_age_indicators(text: str) -> str:
    """Remove age and date of birth."""
    result = text
    for pattern in AGE_PATTERNS:
        result = re.sub(pattern, "[AGE REMOVED]", result, flags=re.IGNORECASE)
    return result


def remove_personal_info(text: str) -> str:
    """Remove marital status, religion, nationality, etc."""
    result = text
    for pattern in PERSONAL_PATTERNS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    for pattern in PHOTO_PATTERNS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    return result


def remove_email_phone(text: str) -> str:
    """Remove email and phone (contact info not relevant for scoring)."""
    # Email
    result = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]", text)
    # Phone
    result = re.sub(r"[\+]?[\d\s\-\(\)]{7,15}", "[PHONE]", result)
    return result


def normalize_universities(text: str) -> str:
    """
    Normalize university names to reduce prestige bias.
    Replace specific university names with generic 'University'.
    This ensures ML models judge skills, not school name.
    """
    # Pattern: "University of X" or "X University" or "X Institute"
    result = re.sub(
        r"\b(?:university|college|institute|school)\s+of\s+[\w\s]+",
        "University",
        text,
        flags=re.IGNORECASE,
    )
    result = re.sub(
        r"\b[\w\s]+(?:university|college|institute|polytechnic)\b",
        "University",
        result,
        flags=re.IGNORECASE,
    )
    return result


def anonymize_cv(text: str, config: Dict = None) -> Dict:
    """
    Main anonymization function. Removes biased information from CV text.

    Args:
        text: Raw CV text
        config: Optional dict to control what gets removed
            {
                "remove_names": True,
                "remove_gender": True,
                "remove_age": True,
                "remove_personal": True,
                "remove_contact": True,
                "normalize_universities": False,  # Off by default
            }

    Returns:
        {
            "anonymized_text": str,
            "removed_items": [str],
            "bias_risk_score": float (0-1, higher = more bias detected),
        }
    """
    if config is None:
        config = {
            "remove_names": True,
            "remove_gender": True,
            "remove_age": True,
            "remove_personal": True,
            "remove_contact": True,
            "normalize_universities": False,
        }

    removed = []
    result = text
    bias_indicators = 0

    if config.get("remove_names", True):
        new_text = remove_names(result)
        if new_text != result:
            removed.append("Name detected and removed")
            bias_indicators += 1
        result = new_text

    if config.get("remove_gender", True):
        new_text = remove_gender_indicators(result)
        if new_text != result:
            removed.append("Gender indicators removed")
            bias_indicators += 1
        result = new_text

    if config.get("remove_age", True):
        new_text = remove_age_indicators(result)
        if new_text != result:
            removed.append("Age/DOB removed")
            bias_indicators += 1
        result = new_text

    if config.get("remove_personal", True):
        new_text = remove_personal_info(result)
        if new_text != result:
            removed.append("Personal info removed (marital status, religion, etc.)")
            bias_indicators += 1
        result = new_text

    if config.get("remove_contact", True):
        result = remove_email_phone(result)

    if config.get("normalize_universities", False):
        new_text = normalize_universities(result)
        if new_text != result:
            removed.append("University names normalized")
        result = new_text

    # Clean up extra whitespace
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = re.sub(r"  +", " ", result)

    # Bias risk score (0-1)
    bias_risk = min(bias_indicators / 4, 1.0)

    logger.info(f"Anonymization: {len(removed)} items removed, bias risk: {bias_risk:.1%}")

    return {
        "anonymized_text": result.strip(),
        "removed_items": removed,
        "bias_risk_score": bias_risk,
    }
