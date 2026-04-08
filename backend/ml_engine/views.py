"""
ML Engine API views — scoring status, model info, genetic algorithm.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from accounts.permissions import IsAdmin, IsAdminOrRecruiter
from candidates.models import Application


@api_view(["GET"])
def score_status(request, application_id):
    """GET /api/ml/status/<id>/ — Check scoring progress."""
    try:
        app = Application.objects.select_related("score").get(
            id=application_id, candidate=request.user
        )
    except Application.DoesNotExist:
        return Response({"error": "Not found"}, status=404)

    if app.status == Application.Status.PROCESSING:
        return Response({"status": "processing"})

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
        return Response({"status": "processing"})


@api_view(["POST"])
@permission_classes([IsAdmin])
def rescore_job(request, job_id):
    """POST /api/ml/rescore/<job_id>/ — Re-score all applications."""
    from .tasks import bulk_rescore_job
    bulk_rescore_job.delay(job_id)
    return Response({"message": f"Re-scoring triggered for job {job_id}"})


@api_view(["GET"])
@permission_classes([IsAdmin])
def model_info(request):
    """GET /api/ml/models/ — View loaded model info."""
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
            "loaded": exists,
            "size_mb": round(size / 1024 / 1024, 2),
            "weight": MODEL_WEIGHTS.get(name, 0),
        })

    # Check feature method
    method_path = os.path.join(settings.ML_MODELS_DIR, "feature_method.txt")
    feature_method = "unknown"
    if os.path.exists(method_path):
        with open(method_path) as f:
            feature_method = f.read().strip()

    return Response({
        "models": models,
        "feature_method": feature_method,
        "total_models": len([m for m in models if m["loaded"]]),
    })


@api_view(["POST"])
@permission_classes([IsAdminOrRecruiter])
def run_genetic_optimization(request, job_id=None):
    """POST /api/ml/optimize/ — Run genetic algorithm for job matching."""
    from .genetic_algorithm import optimize_job_assignments
    result = optimize_job_assignments(job_id)
    return Response(result)
