"""
Views for candidate applications:
- Candidate: apply to job, view own applications + scores
- Recruiter: view applicants for own jobs, shortlist/reject
- Admin: view all applications
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
    """POST /api/candidates/apply/ — Candidate applies to a job with CV."""

    serializer_class = ApplicationCreateSerializer
    permission_classes = [IsCandidate]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        # Trigger async ML scoring pipeline
        from ml_engine.tasks import score_application
        score_application.delay(application.id)

        return Response(
            {
                "message": "Application submitted! AI scoring in progress...",
                "application_id": application.id,
            },
            status=status.HTTP_201_CREATED,
        )


class CandidateApplicationsView(generics.ListAPIView):
    """GET /api/candidates/my-applications/ — Candidate's own applications."""

    serializer_class = ApplicationListSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Application.objects.filter(
            candidate=self.request.user
        ).select_related("job", "score")


class CandidateApplicationDetailView(generics.RetrieveAPIView):
    """GET /api/candidates/my-applications/<id>/ — Full score breakdown."""

    serializer_class = ApplicationDetailSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Application.objects.filter(
            candidate=self.request.user
        ).select_related("job", "cv_text", "score")


# ─── Recruiter Views ─────────────────────────────────────────

class RecruiterApplicantsView(generics.ListAPIView):
    """GET /api/candidates/job/<job_id>/applicants/ — Applicants for a recruiter's job."""

    serializer_class = ApplicationListSerializer
    permission_classes = [IsAdminOrRecruiter]

    def get_queryset(self):
        job_id = self.kwargs["job_id"]
        qs = Application.objects.filter(
            job_id=job_id
        ).select_related("candidate", "job", "score")

        # Recruiter can only see their own jobs
        if self.request.user.is_recruiter:
            qs = qs.filter(job__recruiter=self.request.user)

        # Sort by overall score descending (AI ranking)
        return qs.order_by("-score__overall_score")


class RecruiterApplicantDetailView(generics.RetrieveAPIView):
    """GET /api/candidates/applicant/<id>/ — Full applicant score detail."""

    serializer_class = ApplicationDetailSerializer
    permission_classes = [IsAdminOrRecruiter]

    def get_queryset(self):
        qs = Application.objects.select_related("job", "cv_text", "score")
        if self.request.user.is_recruiter:
            qs = qs.filter(job__recruiter=self.request.user)
        return qs


class RecruiterUpdateStatusView(generics.UpdateAPIView):
    """PATCH /api/candidates/applicant/<id>/status/ — Shortlist/reject."""

    serializer_class = ApplicationStatusSerializer
    permission_classes = [IsAdminOrRecruiter]

    def get_queryset(self):
        qs = Application.objects.all()
        if self.request.user.is_recruiter:
            qs = qs.filter(job__recruiter=self.request.user)
        return qs


# ─── Admin Views ──────────────────────────────────────────────

class AdminAllApplicationsView(generics.ListAPIView):
    """GET /api/candidates/admin/all/ — Admin sees all applications."""

    serializer_class = ApplicationListSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["status", "job"]

    def get_queryset(self):
        return Application.objects.all().select_related(
            "candidate", "job", "score"
        )
