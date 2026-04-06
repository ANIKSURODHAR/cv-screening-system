"""
Celery tasks for async ML scoring.
CV scoring can take 10-30 seconds — must run async.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def score_application(self, application_id: int):
    """
    Async task: Run full scoring pipeline for an application.

    Triggered when a candidate applies to a job.
    Retries up to 3 times on failure.
    """
    logger.info(f"Celery task: scoring application {application_id}")

    try:
        from .pipeline import run_scoring_pipeline
        result = run_scoring_pipeline(application_id)

        if "error" in result:
            logger.error(f"Pipeline error: {result['error']}")
            raise Exception(result["error"])

        logger.info(
            f"Scoring complete: application={application_id}, "
            f"score={result['overall_score']}% ({result['label']})"
        )
        return result

    except Exception as exc:
        logger.error(f"Scoring task failed: {exc}")
        self.retry(exc=exc)


@shared_task
def bulk_rescore_job(job_id: int):
    """
    Re-score all applications for a job.
    Useful when job requirements are updated.
    """
    from candidates.models import Application

    applications = Application.objects.filter(job_id=job_id)
    logger.info(f"Re-scoring {applications.count()} applications for job {job_id}")

    for app in applications:
        score_application.delay(app.id)
