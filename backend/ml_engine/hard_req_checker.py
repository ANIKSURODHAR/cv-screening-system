"""
STEP 5: Hard Requirement Check

Binary match on recruiter-defined must-haves.
This is a GATE: candidates must pass to proceed to ML scoring.

Matching strategies:
  - Skill matching: keyword lookup in extracted skills list
  - Experience matching: compare years found vs required
  - Education matching: compare education level
  - Certification matching: keyword search in CV text

Returns per-requirement match details + overall pass/fail.
"""
import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def check_skill_requirement(
    requirement: Dict,
    skills: List[Dict],
    cv_text: str,
) -> Dict:
    """Check if candidate has required skill."""
    keywords = [kw.strip().lower() for kw in requirement.get("keywords", "").split(",")]
    skill_names = {s["skill"].lower() for s in skills}

    matched_keywords = []
    for kw in keywords:
        # Check in extracted skills
        if kw in skill_names:
            matched_keywords.append(kw)
            continue
        # Fallback: search in raw CV text
        if re.search(r"\b" + re.escape(kw) + r"\b", cv_text.lower()):
            matched_keywords.append(kw)

    is_matched = len(matched_keywords) > 0

    return {
        "requirement": requirement["description"],
        "type": "skill",
        "matched": is_matched,
        "matched_keywords": matched_keywords,
        "required_keywords": keywords,
        "confidence": len(matched_keywords) / max(len(keywords), 1),
    }


def check_experience_requirement(
    requirement: Dict,
    experience_years: float,
) -> Dict:
    """Check if candidate meets minimum experience years."""
    min_years = requirement.get("min_years", 0)
    is_matched = experience_years >= min_years
    # Partial credit: if close but not quite
    confidence = min(experience_years / max(min_years, 1), 1.0) if min_years > 0 else 1.0

    return {
        "requirement": requirement["description"],
        "type": "experience",
        "matched": is_matched,
        "found_years": experience_years,
        "required_years": min_years,
        "confidence": confidence,
    }


def check_education_requirement(
    requirement: Dict,
    education: List[Dict],
) -> Dict:
    """Check if candidate meets education level requirement."""
    # Map requirement keywords to levels
    level_map = {"phd": 4, "masters": 3, "bachelors": 2, "diploma": 1}
    keywords = [kw.strip().lower() for kw in requirement.get("keywords", "").split(",")]

    required_level = 0
    for kw in keywords:
        for level_name, level_num in level_map.items():
            if level_name in kw:
                required_level = max(required_level, level_num)

    # Get candidate's highest education
    candidate_level = max(
        (e.get("numeric_level", 0) for e in education),
        default=0,
    )

    is_matched = candidate_level >= required_level
    # Check if "preferred" (partial match)
    is_partial = candidate_level >= required_level - 1 and candidate_level > 0

    return {
        "requirement": requirement["description"],
        "type": "education",
        "matched": is_matched,
        "partial_match": is_partial,
        "found_level": candidate_level,
        "required_level": required_level,
        "confidence": min(candidate_level / max(required_level, 1), 1.0),
    }


def check_certification_requirement(
    requirement: Dict,
    cv_text: str,
) -> Dict:
    """Check if candidate has required certification."""
    keywords = [kw.strip().lower() for kw in requirement.get("keywords", "").split(",")]
    cv_lower = cv_text.lower()

    matched = []
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", cv_lower):
            matched.append(kw)

    return {
        "requirement": requirement["description"],
        "type": "certification",
        "matched": len(matched) > 0,
        "matched_keywords": matched,
        "required_keywords": keywords,
        "confidence": len(matched) / max(len(keywords), 1),
    }


def check_hard_requirements(
    nlp_data: Dict,
    cv_text: str,
    hard_requirements: List[Dict],
) -> Dict:
    """
    Main function: check ALL hard requirements.

    Args:
        nlp_data: Output from NLP processor (skills, education, experience)
        cv_text: Raw CV text
        hard_requirements: List of requirement dicts from the job

    Returns:
        {
            "passed": bool,
            "score": float (0-100),
            "mandatory_passed": bool,
            "details": [per-requirement results],
            "summary": str,
        }
    """
    logger.info(f"Checking {len(hard_requirements)} hard requirements...")

    skills = nlp_data.get("skills", [])
    education = nlp_data.get("education", [])
    experience = nlp_data.get("experience_years", 0)

    results = []
    mandatory_results = []

    for req in hard_requirements:
        req_type = req.get("requirement_type", "skill")
        is_mandatory = req.get("is_mandatory", True)

        if req_type == "experience":
            result = check_experience_requirement(req, experience)
        elif req_type == "education":
            result = check_education_requirement(req, education)
        elif req_type == "certification":
            result = check_certification_requirement(req, cv_text)
        else:  # skill or other
            result = check_skill_requirement(req, skills, cv_text)

        result["is_mandatory"] = is_mandatory
        results.append(result)

        if is_mandatory:
            mandatory_results.append(result)

    # Calculate scores
    total_confidence = sum(r["confidence"] for r in results)
    score = (total_confidence / max(len(results), 1)) * 100

    mandatory_passed = all(r["matched"] or r.get("partial_match", False) for r in mandatory_results)
    all_passed = all(r["matched"] for r in results)

    # Generate summary
    matched_count = sum(1 for r in results if r["matched"])
    partial_count = sum(1 for r in results if r.get("partial_match") and not r["matched"])

    summary = (
        f"{matched_count}/{len(results)} requirements matched"
        + (f", {partial_count} partial" if partial_count else "")
        + (". ✅ Mandatory requirements met." if mandatory_passed else ". ❌ Mandatory requirements NOT met.")
    )

    logger.info(summary)

    return {
        "passed": mandatory_passed,
        "score": round(score, 1),
        "mandatory_passed": mandatory_passed,
        "all_matched": all_passed,
        "details": results,
        "summary": summary,
    }
