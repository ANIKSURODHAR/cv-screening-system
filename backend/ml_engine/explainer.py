"""
Explainability Module — SHAP-based explanations for ML scores.

Generates human-readable explanations of WHY a candidate scored
high, medium, or low for a particular job.

Uses:
  - SHAP values (when models support it)
  - Feature importance from tree models
  - Rule-based explanations from hard requirement check
"""
import logging
import numpy as np
from typing import Dict, List

logger = logging.getLogger(__name__)


def generate_shap_explanation(
    features: np.ndarray,
    model_name: str = "xgboost",
) -> Dict:
    """
    Generate SHAP explanation for a prediction.
    Uses XGBoost model by default (best SHAP support).
    """
    try:
        import shap
        from .ml_models import load_model

        model = load_model(model_name)
        if model is None:
            return {"error": "Model not available for SHAP"}

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(features.reshape(1, -1))

        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Positive class

        shap_flat = shap_values.flatten()

        # Get top positive and negative features
        top_positive_idx = np.argsort(shap_flat)[-5:][::-1]
        top_negative_idx = np.argsort(shap_flat)[:5]

        return {
            "shap_values": shap_flat.tolist(),
            "top_positive_indices": top_positive_idx.tolist(),
            "top_negative_indices": top_negative_idx.tolist(),
            "base_value": float(explainer.expected_value)
            if not isinstance(explainer.expected_value, np.ndarray)
            else float(explainer.expected_value[1]),
        }

    except Exception as e:
        logger.warning(f"SHAP explanation failed: {e}")
        return {"error": str(e)}


def build_human_explanation(
    nlp_data: Dict,
    hard_req_result: Dict,
    ensemble_result: Dict,
    overall_score: float,
    label: str,
) -> Dict:
    """
    Build a human-readable explanation of the score.

    This is the main explainability function that combines
    all scoring signals into a clear explanation.
    """
    explanation = {
        "score": overall_score,
        "label": label,
        "positive_factors": [],
        "negative_factors": [],
        "improvement_suggestions": [],
        "model_breakdown": {},
    }

    # ─── Skills Analysis ─────────────────────────────────
    skills = nlp_data.get("skills", [])
    skill_categories = {}
    for s in skills:
        cat = s.get("category", "other")
        skill_categories.setdefault(cat, []).append(s["skill"])

    if len(skills) >= 10:
        explanation["positive_factors"].append({
            "factor": f"Strong skill profile ({len(skills)} relevant skills found)",
            "impact": "+15%",
            "details": [f"{cat}: {', '.join(sk)}" for cat, sk in skill_categories.items()],
        })
    elif len(skills) >= 5:
        explanation["positive_factors"].append({
            "factor": f"Adequate skills ({len(skills)} found)",
            "impact": "+8%",
        })
    else:
        explanation["negative_factors"].append({
            "factor": f"Limited skills detected ({len(skills)} found)",
            "impact": "-12%",
        })
        explanation["improvement_suggestions"].append(
            "Add more relevant technical skills to your CV"
        )

    # ─── Experience Analysis ─────────────────────────────
    exp_years = nlp_data.get("experience_years", 0)
    if exp_years >= 5:
        explanation["positive_factors"].append({
            "factor": f"{exp_years} years of experience detected",
            "impact": f"+{min(int(exp_years * 3), 20)}%",
        })
    elif exp_years >= 2:
        explanation["positive_factors"].append({
            "factor": f"{exp_years} years of experience",
            "impact": f"+{int(exp_years * 2)}%",
        })
    else:
        explanation["negative_factors"].append({
            "factor": f"Limited experience ({exp_years} years found)",
            "impact": "-10%",
        })
        explanation["improvement_suggestions"].append(
            "Highlight more work experience, internships, or project experience"
        )

    # ─── Education Analysis ──────────────────────────────
    education = nlp_data.get("education", [])
    if education:
        highest = education[0]
        level = highest.get("level", "unknown")
        level_names = {"phd": "PhD", "masters": "Master's", "bachelors": "Bachelor's", "diploma": "Diploma"}
        explanation["positive_factors"].append({
            "factor": f"{level_names.get(level, level)} degree found",
            "impact": f"+{highest.get('numeric_level', 1) * 5}%",
        })
    else:
        explanation["negative_factors"].append({
            "factor": "No education information detected",
            "impact": "-5%",
        })
        explanation["improvement_suggestions"].append(
            "Add your educational qualifications clearly to your CV"
        )

    # ─── Hard Requirements Analysis ──────────────────────
    hard_details = hard_req_result.get("details", [])
    for detail in hard_details:
        if detail.get("matched"):
            explanation["positive_factors"].append({
                "factor": f"✓ Hard req matched: {detail['requirement']}",
                "impact": "+5%",
            })
        elif detail.get("partial_match"):
            explanation["positive_factors"].append({
                "factor": f"△ Partial match: {detail['requirement']}",
                "impact": "+2%",
            })
        else:
            explanation["negative_factors"].append({
                "factor": f"✗ Missing: {detail['requirement']}",
                "impact": "-8%",
                "is_mandatory": detail.get("is_mandatory", True),
            })
            if detail.get("is_mandatory"):
                explanation["improvement_suggestions"].append(
                    f"Add or highlight: {detail['requirement']}"
                )

    # ─── ML Model Breakdown ──────────────────────────────
    individual = ensemble_result.get("individual_scores", {})
    for model_name, score in individual.items():
        pretty_name = model_name.replace("_", " ").title()
        explanation["model_breakdown"][pretty_name] = {
            "score": score,
            "label": "high" if score >= 80 else "medium" if score >= 60 else "low",
        }

    # ─── Summary ─────────────────────────────────────────
    if label == "high":
        explanation["summary"] = (
            "Strong match! Your profile aligns well with the job requirements. "
            "Key strengths include your technical skills and experience."
        )
    elif label == "medium":
        explanation["summary"] = (
            "Moderate match. You meet several requirements but there are gaps. "
            "Consider the improvement suggestions below to strengthen your application."
        )
    else:
        explanation["summary"] = (
            "Below threshold. Your profile has significant gaps compared to the "
            "job requirements. Focus on the areas listed below to improve your match."
        )

    return explanation
