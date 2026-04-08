"""
FULL SCORING PIPELINE — v2 with all advanced features

Step 1: CV Upload (Django view)
Step 2: Text Extraction (pdfminer + PyMuPDF + OCR)
Step 3: Bias Mitigation (anonymize CV) ← NEW
Step 4: NLP Processing (skills, education, experience)
Step 5: Feature Engineering (BERT embeddings) ← UPGRADED
Step 6: Hard Requirement Check (gate)
Step 7: ML Ensemble (8 models weighted vote)
Step 8: Explainable AI (SHAP + LIME) ← NEW
Step 9: Save Score + Explanation
"""
import logging
from typing import Dict

from candidates.models import Application, CVText, ScreeningScore
from jobs.models import HardRequirement

from .text_extractor import extract_text_from_cv
from .bias_mitigation import anonymize_cv
from .nlp_processor import process_with_spacy, process_cv_text
from .feature_engineer import build_feature_vector
from .hard_req_checker import check_hard_requirements
from .ml_models import run_ensemble, calculate_overall_score
from .explainer import (
    build_human_explanation,
    generate_shap_explanation,
    generate_lime_explanation,
)

logger = logging.getLogger(__name__)


def run_scoring_pipeline(application_id: int) -> Dict:
    """
    Run the complete scoring pipeline with all advanced features.
    """
    logger.info(f"=== Starting scoring pipeline v2 for application {application_id} ===")

    try:
        application = Application.objects.select_related(
            "candidate", "job"
        ).get(id=application_id)
    except Application.DoesNotExist:
        logger.error(f"Application {application_id} not found")
        return {"error": "Application not found"}

    job = application.job
    cv_path = application.cv_file.path

    # ─── Step 2: Text Extraction ─────────────────────
    logger.info("Step 2: Extracting text from CV...")
    try:
        best_text, method, all_results = extract_text_from_cv(cv_path)
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return {"error": f"Text extraction failed: {e}"}

    # ─── Step 3: Bias Mitigation (NEW) ───────────────
    logger.info("Step 3: Anonymizing CV to prevent bias...")
    bias_result = anonymize_cv(best_text)
    anonymized_text = bias_result["anonymized_text"]

    # ─── Step 4: NLP Processing ──────────────────────
    logger.info("Step 4: NLP processing...")
    try:
        nlp_data = process_with_spacy(anonymized_text)
    except Exception:
        nlp_data = process_cv_text(anonymized_text)

    # Save CV text data
    cv_text_obj, _ = CVText.objects.update_or_create(
        application=application,
        defaults={
            "pdfminer_text": all_results.get("pdfminer", {}).get("text", ""),
            "pymupdf_text": all_results.get("pymupdf", {}).get("text", ""),
            "ocr_text": all_results.get("ocr", {}).get("text", ""),
            "best_text": best_text,
            "extraction_method": method,
            "skills_extracted": nlp_data.get("skills", []),
            "education_extracted": nlp_data.get("education", []),
            "experience_years": nlp_data.get("experience_years", 0),
        },
    )

    # ─── Step 5: Feature Engineering (BERT) ──────────
    logger.info("Step 5: BERT feature engineering...")
    job_text = f"{job.title} {job.description}"
    hard_reqs_data = list(
        HardRequirement.objects.filter(job=job).values(
            "requirement_type", "description", "keywords", "min_years", "is_mandatory"
        )
    )

    feature_vector = build_feature_vector(
        cv_text=anonymized_text,
        job_text=job_text,
        nlp_data=nlp_data,
        job_hard_reqs=hard_reqs_data,
    )

    # ─── Step 6: Hard Requirement Check ──────────────
    logger.info("Step 6: Checking hard requirements...")
    hard_req_result = check_hard_requirements(
        nlp_data=nlp_data,
        cv_text=anonymized_text,
        hard_requirements=hard_reqs_data,
    )

    # ─── Step 7: ML Ensemble ─────────────────────────
    logger.info("Step 7: Running ML ensemble...")
    ensemble_result = run_ensemble(feature_vector)

    # Calculate overall score
    overall_score = calculate_overall_score(
        hard_req_score=hard_req_result["score"],
        ensemble_score=ensemble_result["ensemble_score"],
        hard_req_passed=hard_req_result["passed"],
    )

    label = "high" if overall_score >= 80 else "medium" if overall_score >= 60 else "low"

    # ─── Step 8: Explainable AI (SHAP + LIME) ────────
    logger.info("Step 8: Generating AI explanations (SHAP + LIME)...")

    # Try SHAP first (best for tree models)
    shap_result = generate_shap_explanation(feature_vector, "random_forest")

    # Try LIME for text explanation
    lime_result = generate_lime_explanation(feature_vector, anonymized_text, "random_forest")

    # Build human-readable explanation
    explanation = build_human_explanation(
        nlp_data=nlp_data,
        hard_req_result=hard_req_result,
        ensemble_result=ensemble_result,
        overall_score=overall_score,
        label=label,
        shap_result=shap_result,
        lime_result=lime_result,
        bias_result=bias_result,
    )

    # ─── Step 9: Save Score ──────────────────────────
    logger.info("Step 9: Saving score and explanation...")
    individual_scores = ensemble_result.get("individual_scores", {})

    score_obj, _ = ScreeningScore.objects.update_or_create(
        application=application,
        defaults={
            "hard_req_score": hard_req_result["score"],
            "hard_req_passed": hard_req_result["passed"],
            "hard_req_details": hard_req_result,
            "logistic_regression_score": individual_scores.get("logistic_regression", 0),
            "naive_bayes_score": individual_scores.get("naive_bayes", 0),
            "knn_score": individual_scores.get("knn", 0),
            "decision_tree_score": individual_scores.get("decision_tree", 0),
            "random_forest_score": individual_scores.get("random_forest", 0),
            "svm_score": individual_scores.get("svm", 0),
            "xgboost_score": individual_scores.get("xgboost", 0),
            "autogluon_score": individual_scores.get("autogluon", 0),
            "ensemble_score": ensemble_result["ensemble_score"],
            "overall_score": overall_score,
            "label": label,
            "shap_explanation": explanation,
        },
    )

    # Update application status
    application.status = Application.Status.SCORED
    application.save()

    logger.info(f"=== Pipeline v2 complete: {overall_score}% ({label}) ===")

    return {
        "application_id": application_id,
        "overall_score": overall_score,
        "label": label,
        "hard_req_score": hard_req_result["score"],
        "ensemble_score": ensemble_result["ensemble_score"],
        "explanation": explanation,
        "bias_mitigated": True,
        "explainability": shap_result.get("method", "fallback"),
    }
