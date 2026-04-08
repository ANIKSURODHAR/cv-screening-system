"""
STEP 4: Feature Engineering — BERT-Only (Best Accuracy)

Uses sentence-transformers to generate dense 384-dim embeddings.
No TF-IDF — BERT captures both keywords AND semantic meaning.

Feature vector per CV-job pair:
  - CV embedding (384d)
  - Job embedding (384d)
  - CV * Job element-wise (384d) — interaction features
  - |CV - Job| absolute diff (384d) — gap features
  - Cosine similarity (1d)
  - Structured features (12d)
  Total: 1549 dims
"""
import os
import pickle
import logging
import numpy as np
from typing import Dict
from django.conf import settings

logger = logging.getLogger(__name__)

BERT_MODEL_NAME = "all-MiniLM-L6-v2"
_model_cache = {}


def get_bert_model():
    """Load BERT model with caching (loads once, reuses)."""
    if "bert" not in _model_cache:
        try:
            import torch
            # Force CPU to avoid macOS Metal GPU crash
            os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
            if hasattr(torch.backends, "mps"):
                os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

            from sentence_transformers import SentenceTransformer
            _model_cache["bert"] = SentenceTransformer(
                BERT_MODEL_NAME,
                device="cpu",  # Force CPU — works everywhere
            )
            logger.info(f"BERT model loaded: {BERT_MODEL_NAME} (CPU)")
        except ImportError:
            logger.warning("sentence-transformers not installed")
            _model_cache["bert"] = None
        except Exception as e:
            logger.error(f"BERT load failed: {e}")
            _model_cache["bert"] = None
    return _model_cache["bert"]


def get_bert_embeddings(text: str) -> np.ndarray:
    """Get BERT embedding for a single text. Returns 384-dim vector."""
    model = get_bert_model()
    if model is None:
        return np.zeros(384)

    try:
        truncated = text[:5000]  # BERT max ~512 tokens
        embedding = model.encode(
            [truncated],
            show_progress_bar=False,
            convert_to_numpy=True,
            device="cpu",
        )
        return embedding[0]
    except Exception as e:
        logger.error(f"BERT encoding failed: {e}")
        return np.zeros(384)


def get_structured_features(nlp_data: Dict, job_hard_reqs: list) -> np.ndarray:
    """
    Hand-crafted features from NLP output (12 dims).
    These capture information BERT can't: skill counts, education level, years.
    """
    features = []

    # Skill counts by category
    skills = nlp_data.get("skills", [])
    features.append(len(skills))  # Total skills

    categories = ["programming", "frameworks", "ml_ai", "data", "cloud_devops", "databases", "other"]
    for cat in categories:
        count = sum(1 for s in skills if s.get("category") == cat)
        features.append(count)

    # Education level (0-4)
    education = nlp_data.get("education", [])
    max_edu = max((e.get("numeric_level", 0) for e in education), default=0)
    features.append(max_edu)

    # Experience years
    features.append(nlp_data.get("experience_years", 0))

    # Word count (normalized)
    features.append(min(nlp_data.get("word_count", 0) / 1000, 5.0))

    # Hard requirement match ratio
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
    Build BERT-based feature vector.

    Returns ~1549 dim vector:
      384 (CV emb) + 384 (Job emb) + 384 (interaction) + 384 (diff) + 1 (cosine) + 12 (structured)
    """
    logger.info("Building BERT feature vector...")

    # BERT embeddings
    cv_emb = get_bert_embeddings(cv_text)
    job_emb = get_bert_embeddings(job_text)

    # Cosine similarity
    norm_product = np.linalg.norm(cv_emb) * np.linalg.norm(job_emb) + 1e-8
    cosine_sim = np.dot(cv_emb, job_emb) / norm_product

    # Structured features
    struct_feats = get_structured_features(nlp_data, job_hard_reqs)

    # Concatenate: CV + Job + Interaction + Difference + Similarity + Structured
    feature_vector = np.concatenate([
        cv_emb,                        # 384
        job_emb,                       # 384
        cv_emb * job_emb,             # 384 element-wise interaction
        np.abs(cv_emb - job_emb),     # 384 absolute difference
        [cosine_sim],                  # 1
        struct_feats,                  # 12
    ])

    logger.info(f"Feature vector: {len(feature_vector)} dims (BERT + structured)")
    return feature_vector


def build_feature_vector_for_training(cv_text: str) -> np.ndarray:
    """
    Build feature vector for Category+Resume training format.
    Uses only CV embedding + no job text needed.
    Returns 384 dims.
    """
    return get_bert_embeddings(cv_text)
