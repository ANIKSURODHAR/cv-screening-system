"""
ML Engine API views.
- Check scoring status
- Admin: view model info, trigger re-scoring
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from accounts.permissions import IsAdmin
from candidates.models import Application


@api_view(["GET"])
def score_status(request, application_id):
    """GET /api/ml/status/<application_id>/ — Check scoring progress."""
    try:
        app = Application.objects.select_related("score").get(
            id=application_id, candidate=request.user
        )
    except Application.DoesNotExist:
        return Response({"error": "Application not found"}, status=404)

    if app.status == Application.Status.PROCESSING:
        return Response({"status": "processing", "message": "AI scoring in progress..."})

    try:
        score = app.score
        return Response({
            "status": "scored",
            "overall_score": score.overall_score,
            "label": score.label,
            "hard_req_score": score.hard_req_score,
            "ensemble_score": score.ensemble_score,
        })
    except Exception:
        return Response({"status": "processing", "message": "Score not yet available"})


@api_view(["POST"])
@permission_classes([IsAdmin])
def rescore_job(request, job_id):
    """POST /api/ml/rescore/<job_id>/ — Admin: re-score all applications for a job."""
    from .tasks import bulk_rescore_job
    bulk_rescore_job.delay(job_id)
    return Response({"message": f"Re-scoring triggered for job {job_id}"})


@api_view(["GET"])
@permission_classes([IsAdmin])
def model_info(request):
    """GET /api/ml/models/ — Admin: view loaded model info."""
    import os
    from django.conf import settings
    from .ml_models import MODEL_FILES, MODEL_WEIGHTS

    models = []
    for name, filename in MODEL_FILES.items():
        path = os.path.join(settings.ML_MODELS_DIR, filename)
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        models.append({
            "name": name,
            "file": filename,
            "loaded": exists,
            "size_mb": round(size / 1024 / 1024, 2),
            "weight": MODEL_WEIGHTS.get(name, 0),
        })

    return Response({"models": models})
