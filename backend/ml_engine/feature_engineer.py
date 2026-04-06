"""
STEP 4: Feature Engineering

Convert CV text + job description → numerical feature vectors.

Two-pronged approach:
  1. TF-IDF Vectorizer → sparse features (~500 dims) — captures keyword overlap
  2. BERT Sentence Embeddings → dense features (768 dims) — captures semantic meaning

Final: Concatenate both → 1268-dim feature vector per CV-job pair.

Also includes:
  - Cosine similarity between CV and job description
  - Structured features (years exp, education level, skill count)
"""
import os
import pickle
import logging
import numpy as np
from typing import Dict, Tuple, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Paths for saved vectorizers
TFIDF_PATH = os.path.join(settings.ML_MODELS_DIR, "tfidf_vectorizer.pkl")


def get_tfidf_features(cv_text: str, job_text: str) -> np.ndarray:
    """
    Generate TF-IDF feature vector for a CV-job pair.

    If a pre-trained vectorizer exists, use it.
    Otherwise, create a new one on-the-fly.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        # Try to load pre-trained vectorizer
        if os.path.exists(TFIDF_PATH):
            with open(TFIDF_PATH, "rb") as f:
                vectorizer = pickle.load(f)
            vectors = vectorizer.transform([cv_text, job_text])
        else:
            # Create new vectorizer (will be saved during training)
            vectorizer = TfidfVectorizer(
                max_features=500,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95,
            )
            vectors = vectorizer.fit_transform([cv_text, job_text])

        cv_vector = vectors[0].toarray().flatten()
        job_vector = vectors[1].toarray().flatten()

        # Cosine similarity as an additional feature
        similarity = cosine_similarity(
            cv_vector.reshape(1, -1),
            job_vector.reshape(1, -1),
        )[0][0]

        # Combine: CV vector + job vector + similarity
        # Pad/truncate to 500 dims
        target_dim = 250
        cv_feat = cv_vector[:target_dim] if len(cv_vector) >= target_dim else np.pad(
            cv_vector, (0, target_dim - len(cv_vector))
        )
        job_feat = job_vector[:target_dim] if len(job_vector) >= target_dim else np.pad(
            job_vector, (0, target_dim - len(job_vector))
        )

        return np.concatenate([cv_feat, job_feat, [similarity]])

    except Exception as e:
        logger.error(f"TF-IDF feature extraction failed: {e}")
        return np.zeros(501)


def get_bert_embeddings(cv_text: str, job_text: str) -> np.ndarray:
    """
    Generate BERT sentence embeddings for CV and job description.
    Uses sentence-transformers for efficient encoding.

    Returns concatenated [CV_embedding, Job_embedding, cosine_sim] = 768+768+1 = 1537 dims
    Truncated to 768 dims via mean pooling of CV+Job.
    """
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")  # Fast & good quality

        # Truncate texts to model's max length
        cv_truncated = cv_text[:5000]
        job_truncated = job_text[:2000]

        embeddings = model.encode(
            [cv_truncated, job_truncated],
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        cv_emb = embeddings[0]   # 384 dims for MiniLM (or 768 for full BERT)
        job_emb = embeddings[1]

        # Cosine similarity
        similarity = np.dot(cv_emb, job_emb) / (
            np.linalg.norm(cv_emb) * np.linalg.norm(job_emb) + 1e-8
        )

        # Combine via element-wise operations
        combined = np.concatenate([
            cv_emb,
            job_emb,
            cv_emb * job_emb,        # Element-wise interaction
            np.abs(cv_emb - job_emb),  # Absolute difference
            [similarity],
        ])

        return combined

    except ImportError:
        logger.warning("sentence-transformers not installed, using zero embeddings")
        return np.zeros(384 * 4 + 1)
    except Exception as e:
        logger.error(f"BERT embedding failed: {e}")
        return np.zeros(384 * 4 + 1)


def get_structured_features(nlp_data: Dict, job_hard_reqs: list) -> np.ndarray:
    """
    Create structured (hand-crafted) features from NLP output.

    Features:
    - Total skills count
    - Skills per category count
    - Education level (numeric)
    - Experience years
    - Hard requirement match ratio
    - Word count
    """
    features = []

    # Skill counts
    skills = nlp_data.get("skills", [])
    features.append(len(skills))

    # Skills by category
    categories = ["programming", "frameworks", "ml_ai", "data", "cloud_devops", "databases", "other"]
    for cat in categories:
        count = sum(1 for s in skills if s.get("category") == cat)
        features.append(count)

    # Education level
    education = nlp_data.get("education", [])
    max_edu = max(
        (e.get("numeric_level", 0) for e in education),
        default=0,
    )
    features.append(max_edu)

    # Experience years
    features.append(nlp_data.get("experience_years", 0))

    # Word count (normalized)
    word_count = nlp_data.get("word_count", 0)
    features.append(min(word_count / 1000, 5.0))

    # Hard requirement match ratio (pre-computed feature)
    if job_hard_reqs:
        skill_names = {s["skill"].lower() for s in skills}
        matched = sum(
            1 for req in job_hard_reqs
            if any(kw.strip().lower() in skill_names for kw in req.get("keywords", "").split(","))
        )
        features.append(matched / len(job_hard_reqs))
    else:
        features.append(0.0)

    return np.array(features, dtype=np.float32)


def build_feature_vector(
    cv_text: str,
    job_text: str,
    nlp_data: Dict,
    job_hard_reqs: list,
) -> np.ndarray:
    """
    Build the complete feature vector by concatenating:
      1. TF-IDF features (~501 dims)
      2. BERT embeddings (~1537 dims)
      3. Structured features (~12 dims)

    Total: ~2050 dims
    """
    logger.info("Building feature vector...")

    tfidf_feats = get_tfidf_features(cv_text, job_text)
    bert_feats = get_bert_embeddings(cv_text, job_text)
    struct_feats = get_structured_features(nlp_data, job_hard_reqs)

    # Concatenate all features
    feature_vector = np.concatenate([tfidf_feats, bert_feats, struct_feats])

    logger.info(
        f"Feature vector built: {len(feature_vector)} dims "
        f"(TF-IDF={len(tfidf_feats)}, BERT={len(bert_feats)}, "
        f"Structured={len(struct_feats)})"
    )

    return feature_vector


def save_tfidf_vectorizer(vectorizer):
    """Save trained TF-IDF vectorizer for reuse."""
    with open(TFIDF_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    logger.info(f"TF-IDF vectorizer saved to {TFIDF_PATH}")
