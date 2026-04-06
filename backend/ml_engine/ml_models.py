"""
STEP 6: ML Model Ensemble

8 trained models vote via weighted ensemble → final score.

Models & Weights (tuned for CV screening):
  1. Logistic Regression  — weight: 0.08 (baseline)
  2. Naïve Bayes          — weight: 0.07 (fast filter)
  3. KNN                  — weight: 0.08 (similarity)
  4. Decision Tree        — weight: 0.09 (explainable)
  5. Random Forest        — weight: 0.15 (robust)
  6. SVM                  — weight: 0.14 (text classification)
  7. XGBoost              — weight: 0.22 (best performer)
  8. AutoGluon            — weight: 0.17 (auto-tuned)

Training: Models are pre-trained on labeled CV-job match data.
Inference: Each model predicts match probability → weighted average.
"""
import os
import pickle
import logging
import numpy as np
from typing import Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Model weights (sum = 1.0)
MODEL_WEIGHTS = {
    "logistic_regression": 0.08,
    "naive_bayes": 0.07,
    "knn": 0.08,
    "decision_tree": 0.09,
    "random_forest": 0.15,
    "svm": 0.14,
    "xgboost": 0.22,
    "autogluon": 0.17,
}

MODEL_FILES = {
    "logistic_regression": "logistic_regression.pkl",
    "naive_bayes": "naive_bayes.pkl",
    "knn": "knn.pkl",
    "decision_tree": "decision_tree.pkl",
    "random_forest": "random_forest.pkl",
    "svm": "svm.pkl",
    "xgboost": "xgboost.pkl",
    "autogluon": "autogluon.pkl",
}


def load_model(model_name: str):
    """Load a pre-trained model from disk."""
    model_path = os.path.join(settings.ML_MODELS_DIR, MODEL_FILES[model_name])
    if not os.path.exists(model_path):
        logger.warning(f"Model file not found: {model_path}")
        return None
    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        return None


def predict_with_model(model, features: np.ndarray, model_name: str) -> float:
    """
    Get prediction probability from a single model.
    Returns probability of positive class (good match) as 0-100 score.
    """
    try:
        features_2d = features.reshape(1, -1)

        # Try predict_proba first (gives probability)
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(features_2d)
            # Positive class probability
            score = proba[0][1] if proba.shape[1] > 1 else proba[0][0]
        else:
            # Fallback to decision_function (SVM)
            if hasattr(model, "decision_function"):
                decision = model.decision_function(features_2d)
                # Convert to 0-1 range using sigmoid
                score = 1 / (1 + np.exp(-decision[0]))
            else:
                # Last resort: predict
                pred = model.predict(features_2d)
                score = float(pred[0])

        return round(float(score) * 100, 1)

    except Exception as e:
        logger.error(f"Prediction failed for {model_name}: {e}")
        return 0.0


def run_ensemble(features: np.ndarray) -> Dict:
    """
    Run all 8 models and compute weighted ensemble score.

    Args:
        features: Feature vector (from feature_engineer.build_feature_vector)

    Returns:
        {
            "individual_scores": {"model_name": score, ...},
            "ensemble_score": float,
            "models_used": int,
            "models_failed": [str],
        }
    """
    logger.info("Running ML ensemble (8 models)...")

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

    # Calculate weighted average
    if total_weight > 0:
        ensemble_score = weighted_sum / total_weight
    else:
        ensemble_score = 0.0

    models_used = len(individual_scores)

    logger.info(
        f"Ensemble complete: {models_used}/8 models, "
        f"score={ensemble_score:.1f}%"
    )

    return {
        "individual_scores": individual_scores,
        "ensemble_score": round(ensemble_score, 1),
        "models_used": models_used,
        "models_failed": models_failed,
    }


def calculate_overall_score(
    hard_req_score: float,
    ensemble_score: float,
    hard_req_passed: bool,
) -> float:
    """
    Calculate the final overall score.

    Formula:
      If hard requirements passed:
        overall = 0.3 * hard_req_score + 0.7 * ensemble_score
      If hard requirements failed:
        overall = 0.5 * hard_req_score + 0.5 * ensemble_score
        (capped at 50 to penalize missing mandatory requirements)
    """
    if hard_req_passed:
        overall = 0.3 * hard_req_score + 0.7 * ensemble_score
    else:
        overall = 0.5 * hard_req_score + 0.5 * ensemble_score
        overall = min(overall, 50.0)  # Cap at 50%

    return round(overall, 1)


# ─── Training Functions ──────────────────────────────────────

def train_all_models(X_train: np.ndarray, y_train: np.ndarray) -> Dict:
    """
    Train all 8 ML models on labeled data.

    Args:
        X_train: Feature matrix (n_samples, n_features)
        y_train: Labels (0 = not suitable, 1 = suitable)

    Returns training results with accuracy per model.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.naive_bayes import GaussianNB
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.svm import SVC
    from sklearn.model_selection import cross_val_score

    logger.info(f"Training models on {X_train.shape[0]} samples, {X_train.shape[1]} features")

    models = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, C=1.0, class_weight="balanced", random_state=42
        ),
        "naive_bayes": GaussianNB(),
        "knn": KNeighborsClassifier(
            n_neighbors=5, weights="distance", metric="cosine"
        ),
        "decision_tree": DecisionTreeClassifier(
            max_depth=10, min_samples_split=5, class_weight="balanced", random_state=42
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=15, min_samples_split=5,
            class_weight="balanced", random_state=42, n_jobs=-1,
        ),
        "svm": SVC(
            kernel="rbf", C=1.0, gamma="scale",
            probability=True, class_weight="balanced", random_state=42,
        ),
    }

    results = {}

    for name, model in models.items():
        logger.info(f"Training {name}...")
        try:
            # Cross-validation score
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")
            # Train on full data
            model.fit(X_train, y_train)
            # Save
            model_path = os.path.join(settings.ML_MODELS_DIR, MODEL_FILES[name])
            with open(model_path, "wb") as f:
                pickle.dump(model, f)

            results[name] = {
                "accuracy": round(cv_scores.mean() * 100, 1),
                "std": round(cv_scores.std() * 100, 1),
                "saved": model_path,
            }
            logger.info(f"  {name}: accuracy={results[name]['accuracy']}% ± {results[name]['std']}%")

        except Exception as e:
            logger.error(f"  {name} training failed: {e}")
            results[name] = {"error": str(e)}

    # XGBoost
    try:
        import xgboost as xgb
        logger.info("Training xgboost...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            use_label_encoder=False, eval_metric="logloss",
            random_state=42, n_jobs=-1,
        )
        cv_scores = cross_val_score(xgb_model, X_train, y_train, cv=5, scoring="accuracy")
        xgb_model.fit(X_train, y_train)
        model_path = os.path.join(settings.ML_MODELS_DIR, MODEL_FILES["xgboost"])
        with open(model_path, "wb") as f:
            pickle.dump(xgb_model, f)
        results["xgboost"] = {
            "accuracy": round(cv_scores.mean() * 100, 1),
            "std": round(cv_scores.std() * 100, 1),
            "saved": model_path,
        }
    except ImportError:
        logger.warning("XGBoost not installed")
        results["xgboost"] = {"error": "Not installed"}

    # AutoGluon
    try:
        from autogluon.tabular import TabularPredictor
        import pandas as pd
        import tempfile

        logger.info("Training autogluon...")
        df = pd.DataFrame(X_train)
        df["label"] = y_train

        with tempfile.TemporaryDirectory() as tmpdir:
            predictor = TabularPredictor(
                label="label",
                path=tmpdir,
                eval_metric="accuracy",
            ).fit(
                df,
                time_limit=120,  # 2 minutes
                presets="medium_quality",
            )

            # Save
            model_path = os.path.join(settings.ML_MODELS_DIR, MODEL_FILES["autogluon"])
            with open(model_path, "wb") as f:
                pickle.dump(predictor, f)

            results["autogluon"] = {
                "accuracy": round(predictor.info()["best_model_score_val"] * 100, 1),
                "saved": model_path,
            }
    except ImportError:
        logger.warning("AutoGluon not installed")
        results["autogluon"] = {"error": "Not installed"}

    return results
