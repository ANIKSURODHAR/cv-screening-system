"""
EXPLAINABLE AI MODULE — SHAP + LIME

Generates clear, human-readable explanations:
  ✔ Selected because: Java skill (+30%), Experience (+25%)
  ❌ Rejected because: No React (-20%)

Uses:
  - SHAP (SHapley Additive exPlanations) for tree-based models
  - LIME (Local Interpretable Model-agnostic Explanations) as fallback
  - Rule-based explanations from hard requirement matching

Output format designed for recruiter dashboard display.
"""
import logging
import numpy as np
from typing import Dict, List

logger = logging.getLogger(__name__)


def generate_shap_explanation(features: np.ndarray, model_name: str = "random_forest") -> Dict:
    """
    Generate SHAP values for a prediction.
    Works best with tree models (Random Forest, XGBoost, Decision Tree).
    """
    try:
        import shap
        from .ml_models import load_model

        model = load_model(model_name)
        if model is None:
            return _generate_fallback_explanation(features)

        # TreeExplainer for tree-based models
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(features.reshape(1, -1))
        except Exception:
            # KernelExplainer for non-tree models (slower but universal)
            try:
                background = np.zeros((10, len(features)))
                explainer = shap.KernelExplainer(model.predict_proba, background)
                shap_values = explainer.shap_values(features.reshape(1, -1))
            except Exception as e:
                logger.warning(f"SHAP failed completely: {e}")
                return _generate_fallback_explanation(features)

        # Handle multi-class SHAP values
        if isinstance(shap_values, list):
            shap_flat = shap_values[1].flatten() if len(shap_values) > 1 else shap_values[0].flatten()
        elif shap_values.ndim == 3:
            shap_flat = shap_values[0, :, 1] if shap_values.shape[2] > 1 else shap_values[0, :, 0]
        else:
            shap_flat = shap_values.flatten()

        # Top positive and negative features
        top_positive = np.argsort(shap_flat)[-5:][::-1]
        top_negative = np.argsort(shap_flat)[:5]

        return {
            "method": "SHAP",
            "shap_values": shap_flat.tolist()[:50],  # Truncate for storage
            "top_positive_indices": top_positive.tolist(),
            "top_negative_indices": top_negative.tolist(),
            "top_positive_values": [float(shap_flat[i]) for i in top_positive],
            "top_negative_values": [float(shap_flat[i]) for i in top_negative],
        }

    except ImportError:
        logger.warning("SHAP not installed, using fallback explanation")
        return _generate_fallback_explanation(features)
    except Exception as e:
        logger.warning(f"SHAP explanation failed: {e}")
        return _generate_fallback_explanation(features)


def generate_lime_explanation(features: np.ndarray, cv_text: str, model_name: str = "random_forest") -> Dict:
    """
    Generate LIME explanation for text-based prediction.
    LIME perturbs the input and observes how predictions change.
    """
    try:
        from lime.lime_text import LimeTextExplainer
        from .ml_models import load_model
        import pickle
        import os
        from django.conf import settings

        model = load_model(model_name)
        if model is None:
            return {"method": "LIME", "error": "Model not available"}

        # Check if we have a TF-IDF vectorizer for text transformation
        tfidf_path = os.path.join(settings.ML_MODELS_DIR, "tfidf_vectorizer.pkl")
        if os.path.exists(tfidf_path):
            with open(tfidf_path, "rb") as f:
                vectorizer = pickle.load(f)

            def predict_fn(texts):
                vectors = vectorizer.transform(texts).toarray()
                return model.predict_proba(vectors)

            explainer = LimeTextExplainer(class_names=["Low Match", "High Match"])
            exp = explainer.explain_instance(
                cv_text[:3000],
                predict_fn,
                num_features=10,
                num_samples=100,
            )

            word_weights = exp.as_list()

            positive_words = [(w, round(s * 100, 1)) for w, s in word_weights if s > 0]
            negative_words = [(w, round(s * 100, 1)) for w, s in word_weights if s < 0]

            return {
                "method": "LIME",
                "positive_words": positive_words[:5],
                "negative_words": negative_words[:5],
                "all_weights": word_weights,
            }
        else:
            return {"method": "LIME", "note": "Text explainer requires TF-IDF vectorizer"}

    except ImportError:
        logger.warning("LIME not installed")
        return {"method": "LIME", "error": "LIME not installed"}
    except Exception as e:
        logger.warning(f"LIME failed: {e}")
        return {"method": "LIME", "error": str(e)}


def _generate_fallback_explanation(features: np.ndarray) -> Dict:
    """Fallback when SHAP/LIME unavailable — uses feature magnitude analysis."""
    nonzero = np.nonzero(features)[0]
    magnitudes = np.abs(features)
    top_indices = np.argsort(magnitudes)[-10:][::-1]

    return {
        "method": "feature_analysis",
        "top_feature_indices": top_indices.tolist(),
        "top_feature_values": [float(features[i]) for i in top_indices],
        "active_features": len(nonzero),
        "total_features": len(features),
    }


def build_human_explanation(
    nlp_data: Dict,
    hard_req_result: Dict,
    ensemble_result: Dict,
    overall_score: float,
    label: str,
    shap_result: Dict = None,
    lime_result: Dict = None,
    bias_result: Dict = None,
) -> Dict:
    """
    Build a complete, human-readable explanation.

    Output format:
    {
        "score": 87.5,
        "label": "high",
        "summary": "Strong match — ...",
        "selected_because": [
            {"factor": "Python 6 years", "impact": "+18%", "type": "skill"},
            {"factor": "TensorFlow certified", "impact": "+15%", "type": "skill"},
        ],
        "rejected_because": [
            {"factor": "No PhD", "impact": "-8%", "type": "education"},
        ],
        "improvement_suggestions": ["Add PhD to gain +8%"],
        "model_breakdown": {"XGBoost": {"score": 89, "label": "high"}, ...},
        "bias_info": {"items_removed": [...], "risk_score": 0.25},
        "explainability": {"method": "SHAP", ...},
    }
    """
    explanation = {
        "score": overall_score,
        "label": label,
        "selected_because": [],
        "rejected_because": [],
        "improvement_suggestions": [],
        "model_breakdown": {},
        "bias_info": None,
        "explainability_method": "SHAP + Rule-based",
    }

    # ─── Skills Analysis ─────────────────────────────
    skills = nlp_data.get("skills", [])
    skill_categories = {}
    for s in skills:
        cat = s.get("category", "other")
        skill_categories.setdefault(cat, []).append(s["skill"])

    if len(skills) >= 10:
        explanation["selected_because"].append({
            "factor": f"Strong skill profile — {len(skills)} relevant skills",
            "impact": "+15%",
            "type": "skill",
            "details": [f"{cat}: {', '.join(sk)}" for cat, sk in skill_categories.items()],
        })
    elif len(skills) >= 5:
        explanation["selected_because"].append({
            "factor": f"Good skills — {len(skills)} found",
            "impact": "+8%",
            "type": "skill",
        })
    else:
        explanation["rejected_because"].append({
            "factor": f"Limited skills detected — only {len(skills)} found",
            "impact": "-12%",
            "type": "skill",
        })
        explanation["improvement_suggestions"].append(
            "Add more technical skills to your CV with specific technologies and tools"
        )

    # ─── Experience ──────────────────────────────────
    exp_years = nlp_data.get("experience_years", 0)
    if exp_years >= 5:
        explanation["selected_because"].append({
            "factor": f"{exp_years} years of experience",
            "impact": f"+{min(int(exp_years * 3), 20)}%",
            "type": "experience",
        })
    elif exp_years >= 2:
        explanation["selected_because"].append({
            "factor": f"{exp_years} years of experience",
            "impact": f"+{int(exp_years * 2)}%",
            "type": "experience",
        })
    else:
        explanation["rejected_because"].append({
            "factor": f"Limited experience — {exp_years} years detected",
            "impact": "-10%",
            "type": "experience",
        })
        explanation["improvement_suggestions"].append(
            "Include internships, freelance work, and project experience with dates"
        )

    # ─── Education ───────────────────────────────────
    education = nlp_data.get("education", [])
    if education:
        highest = education[0]
        level = highest.get("level", "unknown")
        level_names = {"phd": "PhD", "masters": "Master's", "bachelors": "Bachelor's", "diploma": "Diploma"}
        explanation["selected_because"].append({
            "factor": f"{level_names.get(level, level)} degree detected",
            "impact": f"+{highest.get('numeric_level', 1) * 5}%",
            "type": "education",
        })
    else:
        explanation["rejected_because"].append({
            "factor": "No education information detected",
            "impact": "-5%",
            "type": "education",
        })
        explanation["improvement_suggestions"].append(
            "Add your educational qualifications with degree name, institution, and graduation year"
        )

    # ─── Hard Requirements ───────────────────────────
    hard_details = hard_req_result.get("details", [])
    for detail in hard_details:
        if detail.get("matched"):
            explanation["selected_because"].append({
                "factor": f"Requirement matched: {detail['requirement']}",
                "impact": "+5%",
                "type": "hard_requirement",
            })
        elif detail.get("partial_match"):
            explanation["selected_because"].append({
                "factor": f"Partial match: {detail['requirement']}",
                "impact": "+2%",
                "type": "hard_requirement",
            })
        else:
            is_mandatory = detail.get("is_mandatory", True)
            explanation["rejected_because"].append({
                "factor": f"Missing: {detail['requirement']}",
                "impact": "-8%" if is_mandatory else "-3%",
                "type": "hard_requirement",
                "mandatory": is_mandatory,
            })
            if is_mandatory:
                explanation["improvement_suggestions"].append(
                    f"Add or highlight: {detail['requirement']}"
                )

    # ─── ML Model Breakdown ──────────────────────────
    individual = ensemble_result.get("individual_scores", {})
    for model_name, score in individual.items():
        pretty_name = model_name.replace("_", " ").title()
        explanation["model_breakdown"][pretty_name] = {
            "score": score,
            "label": "high" if score >= 80 else "medium" if score >= 60 else "low",
        }

    # ─── Bias Info ───────────────────────────────────
    if bias_result:
        explanation["bias_info"] = {
            "items_removed": bias_result.get("removed_items", []),
            "risk_score": bias_result.get("bias_risk_score", 0),
            "message": "CV was anonymized before scoring to prevent bias",
        }

    # ─── SHAP/LIME Details ───────────────────────────
    if shap_result and "error" not in shap_result:
        explanation["explainability_method"] = shap_result.get("method", "SHAP")
        explanation["shap_details"] = shap_result
    if lime_result and "error" not in lime_result:
        explanation["lime_details"] = lime_result

    # ─── Summary ─────────────────────────────────────
    pos_count = len(explanation["selected_because"])
    neg_count = len(explanation["rejected_because"])

    if label == "high":
        explanation["summary"] = (
            f"Strong match ({overall_score}%). "
            f"{pos_count} positive factors identified. "
            f"Your skills and experience align well with the requirements."
        )
    elif label == "medium":
        explanation["summary"] = (
            f"Moderate match ({overall_score}%). "
            f"{pos_count} strengths found, but {neg_count} gaps detected. "
            f"See improvement suggestions below."
        )
    else:
        explanation["summary"] = (
            f"Below threshold ({overall_score}%). "
            f"{neg_count} gaps identified. "
            f"Significant improvements needed — see suggestions below."
        )

    return explanation
