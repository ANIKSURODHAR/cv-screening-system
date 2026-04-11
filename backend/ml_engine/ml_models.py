"""
STEP 6: ML Model Ensemble — 8 models with weighted voting.

Handles both BERT features (384 dims) and TF-IDF features (variable dims).
Automatically detects feature dimension from saved models.
"""
import os
import pickle
import logging
import numpy as np
from typing import Dict
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL_WEIGHTS = {
    "logistic_regression": 0.10,
    "naive_bayes": 0.10,
    "knn": 0.10,
    "random_forest": 0.20,
    "svm": 0.15,
    "xgboost": 0.35,
}

MODEL_FILES = {
    "logistic_regression": "logistic_regression.pkl",
    "naive_bayes": "naive_bayes.pkl",
    "knn": "knn.pkl",
    "random_forest": "random_forest.pkl",
    "svm": "svm.pkl",
    "xgboost": "xgboost.pkl",
}

_model_cache = {}


def load_model(model_name: str):
    """Load a pre-trained model from disk with caching."""
    if model_name in _model_cache:
        return _model_cache[model_name]

    model_path = os.path.join(settings.ML_MODELS_DIR, MODEL_FILES.get(model_name, ""))
    if not os.path.exists(model_path):
        logger.warning(f"Model not found: {model_path}")
        return None
    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        _model_cache[model_name] = model
        return model
    except Exception as e:
        logger.error(f"Failed to load {model_name}: {e}")
        return None


def get_expected_features() -> int:
    """Detect expected feature count from a saved model."""
    for name in ["random_forest", "logistic_regression", "svm"]:
        model = load_model(name)
        if model is not None and hasattr(model, "n_features_in_"):
            return model.n_features_in_
    return None


def adapt_features(features: np.ndarray, expected: int) -> np.ndarray:
    """Pad or truncate feature vector to match model's expected input."""
    current = len(features)
    if current == expected:
        return features
    elif current < expected:
        return np.pad(features, (0, expected - current))
    else:
        return features[:expected]


def predict_with_model(model, features: np.ndarray, model_name: str) -> float:
    """Get prediction probability from a single model. Returns 0-100 score."""
    try:
        features_2d = features.reshape(1, -1)

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(features_2d)
            if proba.shape[1] > 2:
                # Multi-class: use max probability
                score = float(np.max(proba[0]))
            else:
                score = float(proba[0][1]) if proba.shape[1] > 1 else float(proba[0][0])
        elif hasattr(model, "decision_function"):
            decision = model.decision_function(features_2d)
            if hasattr(decision, '__len__') and len(decision.shape) > 1:
                score = float(np.max(1 / (1 + np.exp(-decision[0]))))
            else:
                score = float(1 / (1 + np.exp(-decision[0])))
        else:
            pred = model.predict(features_2d)
            score = float(pred[0])

        return round(score * 100, 1)

    except Exception as e:
        logger.error(f"Prediction failed for {model_name}: {e}")
        return 0.0


def run_ensemble(features: np.ndarray) -> Dict:
    """Run all models and compute weighted ensemble score."""
    logger.info("Running ML ensemble...")

    # Detect expected feature count and adapt
    expected = get_expected_features()
    if expected is not None and len(features) != expected:
        logger.info(f"Adapting features: {len(features)} → {expected}")
        features = adapt_features(features, expected)

    individual_scores = {}
    models_failed = []
    weighted_sum = 0.0
    total_weight = 0.0

    for model_name, weight in MODEL_WEIGHTS.items():
        model = load_model(model_name)
        if model is None:
            models_failed.append(model_name)
            continue

        score = predict_with_model(model, features, model_name)
        individual_scores[model_name] = score
        weighted_sum += score * weight
        total_weight += weight

    ensemble_score = weighted_sum / total_weight if total_weight > 0 else 0.0

    logger.info(f"Ensemble: {len(individual_scores)}/{len(MODEL_WEIGHTS)} models, score={ensemble_score:.1f}%")

    return {
        "individual_scores": individual_scores,
        "ensemble_score": round(ensemble_score, 1),
        "models_used": len(individual_scores),
        "models_failed": models_failed,
    }


def calculate_overall_score(hard_req_score, ensemble_score, hard_req_passed):
    """Calculate final score: 30% hard reqs + 70% ML ensemble."""
    if hard_req_passed:
        overall = 0.3 * hard_req_score + 0.7 * ensemble_score
    else:
        overall = 0.5 * hard_req_score + 0.5 * ensemble_score
        overall = min(overall, 50.0)
    return round(overall, 1)
