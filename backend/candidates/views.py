"""
Candidate application views — apply, list, score details.
Scoring runs synchronously (direct) or via Celery (if available).
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response

from .models import Application, ScreeningScore
from .serializers import (
    ApplicationListSerializer,
    ApplicationDetailSerializer,
    ApplicationCreateSerializer,
    ApplicationStatusSerializer,
)
from accounts.permissions import IsAdmin, IsRecruiter, IsCandidate, IsAdminOrRecruiter


# ─── Candidate Views ─────────────────────────────────────────

class CandidateApplyView(generics.CreateAPIView):
    """POST /api/candidates/apply/ — Apply to a job with CV."""

    serializer_class = ApplicationCreateSerializer
    permission_classes = [IsCandidate]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        # Run scoring directly (skip Celery on macOS)
        try:
            from ml_engine.pipeline import run_scoring_pipeline
            run_scoring_pipeline(application.id)
        except Exception as e:
            print(f"Scoring error: {e}")

        return Response(
            {
                "message": "Application submitted! AI scoring in progress...",
                "application_id": application.id,
                "scoring_method": scoring_method,
            },
            status=status.HTTP_201_CREATED,
        )


class CandidateApplicationsView(generics.ListAPIView):
    """GET /api/candidates/my-applications/"""

    serializer_class = ApplicationListSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Application.objects.filter(
            candidate=self.request.user
        ).select_related("job", "score")


class CandidateApplicationDetailView(generics.RetrieveAPIView):
    """GET /api/candidates/my-applications/<id>/"""

    serializer_class = ApplicationDetailSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Application.objects.filter(
            candidate=self.request.user
        ).select_related("job", "cv_text", "score")


# ─── Recruiter Views ─────────────────────────────────────────

class RecruiterApplicantsView(generics.ListAPIView):
    """GET /api/candidates/job/<job_id>/applicants/"""

    serializer_class = ApplicationListSerializer
    permission_classes = [IsAdminOrRecruiter]

    def get_queryset(self):
        job_id = self.kwargs["job_id"]
        qs = Application.objects.filter(
            job_id=job_id
        ).select_related("candidate", "job", "score")
        if self.request.user.is_recruiter:
            qs = qs.filter(job__recruiter=self.request.user)
        return qs.order_by("-score__overall_score")


class RecruiterApplicantDetailView(generics.RetrieveAPIView):
    """GET /api/candidates/applicant/<id>/"""

    serializer_class = ApplicationDetailSerializer
    permission_classes = [IsAdminOrRecruiter]

    def get_queryset(self):
        qs = Application.objects.select_related("job", "cv_text", "score")
        if self.request.user.is_recruiter:
            qs = qs.filter(job__recruiter=self.request.user)
        return qs


class RecruiterUpdateStatusView(generics.UpdateAPIView):
    """PATCH /api/candidates/applicant/<id>/status/"""

    serializer_class = ApplicationStatusSerializer
    permission_classes = [IsAdminOrRecruiter]

    def get_queryset(self):
        qs = Application.objects.all()
        if self.request.user.is_recruiter:
            qs = qs.filter(job__recruiter=self.request.user)
        return qs


# ─── Admin Views ──────────────────────────────────────────────

class AdminAllApplicationsView(generics.ListAPIView):
    """GET /api/candidates/admin/all/"""

    serializer_class = ApplicationListSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["status", "job"]

    def get_queryset(self):
        return Application.objects.all().select_related(
            "candidate", "job", "score"
        )
