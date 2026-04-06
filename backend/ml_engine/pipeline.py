"""
PIPELINE ORCHESTRATOR — Runs the complete 6-step scoring pipeline.

Step 1: CV Upload (handled by Django view)
Step 2: Text Extraction (text_extractor.py)
Step 3: NLP Processing (nlp_processor.py)
Step 4: Feature Engineering (feature_engineer.py)
Step 5: Hard Requirement Check (hard_req_checker.py)
Step 6: ML Ensemble (ml_models.py) + Explanation (explainer.py)
"""
import logging
from typing import Dict

from candidates.models import Application, CVText, ScreeningScore
from jobs.models import HardRequirement

from .text_extractor import extract_text_from_cv
from .nlp_processor import process_with_spacy, process_cv_text
from .feature_engineer import build_feature_vector
from .hard_req_checker import check_hard_requirements
from .ml_models import run_ensemble, calculate_overall_score
from .explainer import build_human_explanation

logger = logging.getLogger(__name__)


def run_scoring_pipeline(application_id: int) -> Dict:
    """
    Run the complete 6-step ML scoring pipeline for an application.

    Args:
        application_id: ID of the Application to score

    Returns:
        Dict with score results and explanation
    """
    logger.info(f"=== Starting scoring pipeline for application {application_id} ===")

    try:
        application = Application.objects.select_related(
            "candidate", "job"
        ).get(id=application_id)
    except Application.DoesNotExist:
        logger.error(f"Application {application_id} not found")
        return {"error": "Application not found"}

    job = application.job
    cv_path = application.cv_file.path

    # ─── Step 2: Text Extraction ─────────────────────────
    logger.info("Step 2: Extracting text from CV...")
    try:
        best_text, method, all_results = extract_text_from_cv(cv_path)
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        application.status = Application.Status.PROCESSING
        application.save()
        return {"error": f"Text extraction failed: {e}"}

    # Save extracted text
    cv_text_obj, _ = CVText.objects.update_or_create(
        application=application,
        defaults={
            "pdfminer_text": all_results.get("pdfminer", {}).get("text", ""),
            "pymupdf_text": all_results.get("pymupdf", {}).get("text", ""),
            "ocr_text": all_results.get("ocr", {}).get("text", ""),
            "best_text": best_text,
            "extraction_method": method,
        },
    )

    if not best_text or len(best_text) < 50:
        logger.warning("Extracted text too short, might be a bad PDF")

    # ─── Step 3: NLP Processing ──────────────────────────
    logger.info("Step 3: NLP processing...")
    try:
        nlp_data = process_with_spacy(best_text)
    except Exception:
        nlp_data = process_cv_text(best_text)

    # Update CV text record with NLP results
    cv_text_obj.skills_extracted = nlp_data.get("skills", [])
    cv_text_obj.education_extracted = nlp_data.get("education", [])
    cv_text_obj.experience_years = nlp_data.get("experience_years", 0)
    cv_text_obj.save()

    # ─── Step 4: Feature Engineering ─────────────────────
    logger.info("Step 4: Feature engineering...")
    job_text = f"{job.title} {job.description}"
    hard_reqs_data = list(
        HardRequirement.objects.filter(job=job).values(
            "requirement_type", "description", "keywords", "min_years", "is_mandatory"
        )
    )

    feature_vector = build_feature_vector(
        cv_text=best_text,
        job_text=job_text,
        nlp_data=nlp_data,
        job_hard_reqs=hard_reqs_data,
    )

    # ─── Step 5: Hard Requirement Check ──────────────────
    logger.info("Step 5: Checking hard requirements...")
    hard_req_result = check_hard_requirements(
        nlp_data=nlp_data,
        cv_text=best_text,
        hard_requirements=hard_reqs_data,
    )

    # ─── Step 6: ML Ensemble ─────────────────────────────
    logger.info("Step 6: Running ML ensemble...")
    ensemble_result = run_ensemble(feature_vector)

    # Calculate overall score
    overall_score = calculate_overall_score(
        hard_req_score=hard_req_result["score"],
        ensemble_score=ensemble_result["ensemble_score"],
        hard_req_passed=hard_req_result["passed"],
    )

    # Determine label
    if overall_score >= 80:
        label = "high"
    elif overall_score >= 60:
        label = "medium"
    else:
        label = "low"

    # ─── Generate Explanation ────────────────────────────
    logger.info("Generating explanation...")
    explanation = build_human_explanation(
        nlp_data=nlp_data,
        hard_req_result=hard_req_result,
        ensemble_result=ensemble_result,
        overall_score=overall_score,
        label=label,
    )

    # ─── Save Score ──────────────────────────────────────
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

    logger.info(
        f"=== Pipeline complete: score={overall_score}% ({label}) ==="
    )

    return {
        "application_id": application_id,
        "overall_score": overall_score,
        "label": label,
        "hard_req_score": hard_req_result["score"],
        "ensemble_score": ensemble_result["ensemble_score"],
        "explanation": explanation,
    }
