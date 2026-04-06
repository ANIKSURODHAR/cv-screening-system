"""
STEP 3: NLP Processing

Pipeline:
  1. Clean & normalize text
  2. Tokenize (spaCy)
  3. Remove stopwords
  4. Lemmatize
  5. NER extraction (skills, education, experience years)

Uses spaCy for tokenization/NER + regex patterns for skill matching.
"""
import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# ─── Skill Taxonomy ──────────────────────────────────────────
# Comprehensive skill keywords grouped by category
SKILL_TAXONOMY = {
    "programming": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
        "html", "css", "sql", "bash", "shell", "powershell",
    ],
    "frameworks": [
        "django", "flask", "fastapi", "react", "angular", "vue", "next.js",
        "node.js", "express", "spring", "spring boot", ".net", "rails",
        "laravel", "flutter", "react native", "svelte",
    ],
    "ml_ai": [
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
        "xgboost", "lightgbm", "catboost", "huggingface", "transformers",
        "bert", "gpt", "llm", "nlp", "computer vision", "deep learning",
        "machine learning", "neural network", "reinforcement learning",
        "spacy", "nltk", "opencv", "yolo", "stable diffusion",
    ],
    "data": [
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
        "tableau", "power bi", "excel", "jupyter", "spark", "hadoop",
        "airflow", "dbt", "snowflake", "bigquery", "redshift",
        "data analysis", "data engineering", "data science", "etl",
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
        "terraform", "ansible", "jenkins", "ci/cd", "github actions",
        "gitlab ci", "linux", "nginx", "apache",
    ],
    "databases": [
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "sqlite", "oracle", "sql server",
        "neo4j", "firebase",
    ],
    "other": [
        "git", "rest api", "graphql", "microservices", "agile", "scrum",
        "jira", "figma", "photoshop", "leadership", "communication",
        "project management", "problem solving",
    ],
}

# Flatten for quick lookup
ALL_SKILLS = set()
for skills in SKILL_TAXONOMY.values():
    ALL_SKILLS.update(skills)

# Education patterns
EDUCATION_PATTERNS = {
    "phd": r"\b(ph\.?d|doctor(?:ate)?|d\.?phil)\b",
    "masters": r"\b(m\.?s\.?c?|m\.?a\.?|master(?:s|'s)?|m\.?eng|mba|m\.?tech)\b",
    "bachelors": r"\b(b\.?s\.?c?|b\.?a\.?|bachelor(?:s|'s)?|b\.?eng|b\.?tech|undergraduate)\b",
    "diploma": r"\b(diploma|associate|certificate|certification)\b",
}

EDUCATION_LEVELS = {"phd": 4, "masters": 3, "bachelors": 2, "diploma": 1}


def clean_text(text: str) -> str:
    """Clean and normalize CV text."""
    # Remove URLs
    text = re.sub(r"https?://\S+", " ", text)
    # Remove email addresses (save them first)
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", " ", text)
    # Remove phone numbers
    text = re.sub(r"[\+]?[\d\s\-\(\)]{7,15}", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove special characters but keep periods and hyphens
    text = re.sub(r"[^\w\s\.\-\/\+\#]", " ", text)
    return text.strip()


def extract_skills(text: str) -> List[Dict]:
    """Extract skills from CV text using taxonomy matching."""
    text_lower = text.lower()
    found_skills = []

    for category, skills in SKILL_TAXONOMY.items():
        for skill in skills:
            # Use word boundary matching for accuracy
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text_lower):
                found_skills.append({
                    "skill": skill,
                    "category": category,
                })

    # Deduplicate
    seen = set()
    unique_skills = []
    for s in found_skills:
        if s["skill"] not in seen:
            seen.add(s["skill"])
            unique_skills.append(s)

    return unique_skills


def extract_education(text: str) -> List[Dict]:
    """Extract education levels from CV text."""
    text_lower = text.lower()
    found = []

    for level, pattern in EDUCATION_PATTERNS.items():
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            # Try to find nearby institution name
            context = text_lower[max(0, match.start() - 100):match.end() + 100]
            found.append({
                "level": level,
                "numeric_level": EDUCATION_LEVELS[level],
                "context": context.strip(),
            })

    # Deduplicate by level
    seen = set()
    unique = []
    for e in found:
        if e["level"] not in seen:
            seen.add(e["level"])
            unique.append(e)

    return sorted(unique, key=lambda x: x["numeric_level"], reverse=True)


def extract_experience_years(text: str) -> float:
    """
    Extract years of experience from CV text.

    Strategies:
    1. Look for explicit mentions: "5+ years of experience"
    2. Calculate from date ranges: "2019 - 2024"
    3. Look for "X years" patterns
    """
    text_lower = text.lower()
    years_found = []

    # Strategy 1: Explicit experience mentions
    exp_patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)",
        r"(?:experience|exp)\s*(?:of\s+)?(\d+)\+?\s*(?:years?|yrs?)",
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:in|with|of)",
    ]
    for pattern in exp_patterns:
        matches = re.findall(pattern, text_lower)
        for m in matches:
            try:
                years_found.append(float(m))
            except (ValueError, TypeError):
                pass

    # Strategy 2: Date ranges (2019 - 2024, 2019-present)
    date_pattern = r"\b(20\d{2}|19\d{2})\s*[-–—to]+\s*(20\d{2}|19\d{2}|present|current|now)\b"
    date_matches = re.findall(date_pattern, text_lower)
    total_from_dates = 0
    for start, end in date_matches:
        try:
            start_year = int(start)
            if end in ("present", "current", "now"):
                end_year = 2026  # Current year
            else:
                end_year = int(end)
            diff = end_year - start_year
            if 0 < diff < 40:  # Sanity check
                total_from_dates += diff
        except (ValueError, TypeError):
            pass

    if total_from_dates > 0:
        years_found.append(total_from_dates)

    if years_found:
        return max(years_found)  # Return the highest
    return 0.0


def process_cv_text(raw_text: str) -> Dict:
    """
    Main NLP processing function.

    Returns:
        {
            "cleaned_text": str,
            "skills": [{"skill": str, "category": str}],
            "education": [{"level": str, "numeric_level": int}],
            "experience_years": float,
            "word_count": int,
        }
    """
    logger.info("Running NLP processing on CV text...")

    cleaned = clean_text(raw_text)
    skills = extract_skills(raw_text)  # Use raw text for better matching
    education = extract_education(raw_text)
    experience = extract_experience_years(raw_text)

    result = {
        "cleaned_text": cleaned,
        "skills": skills,
        "education": education,
        "experience_years": experience,
        "word_count": len(cleaned.split()),
    }

    logger.info(
        f"NLP results: {len(skills)} skills, "
        f"{len(education)} education levels, "
        f"{experience} years experience"
    )

    return result


def process_with_spacy(text: str) -> Dict:
    """
    Enhanced NLP processing using spaCy.
    Falls back to regex-based processing if spaCy is unavailable.
    """
    try:
        import spacy

        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            return process_cv_text(text)

        doc = nlp(text[:100000])  # Limit text length for spaCy

        # Extract named entities
        entities = {
            "organizations": [],
            "persons": [],
            "dates": [],
            "locations": [],
        }
        for ent in doc.ents:
            if ent.label_ == "ORG":
                entities["organizations"].append(ent.text)
            elif ent.label_ == "PERSON":
                entities["persons"].append(ent.text)
            elif ent.label_ == "DATE":
                entities["dates"].append(ent.text)
            elif ent.label_ in ("GPE", "LOC"):
                entities["locations"].append(ent.text)

        # Get base NLP results
        base_results = process_cv_text(text)

        # Lemmatized tokens (for feature engineering)
        tokens = [
            token.lemma_.lower()
            for token in doc
            if not token.is_stop and not token.is_punct and token.is_alpha
        ]

        base_results["entities"] = entities
        base_results["lemmatized_tokens"] = tokens

        return base_results

    except ImportError:
        logger.warning("spaCy not installed, falling back to regex processing")
        return process_cv_text(text)
