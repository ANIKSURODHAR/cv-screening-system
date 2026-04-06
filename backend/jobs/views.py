"""
Views for job management.
- Recruiter: create, update, list own jobs
- Candidate: browse approved jobs
- Admin: approve/reject, list all jobs
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Job, HardRequirement
from .serializers import (
    JobListSerializer,
    JobCreateSerializer,
    JobApprovalSerializer,
    HardRequirementSerializer,
)
from accounts.permissions import IsAdmin, IsRecruiter, IsCandidate, IsAdminOrRecruiter


# ─── Recruiter Views ─────────────────────────────────────────

class RecruiterJobListView(generics.ListAPIView):
    """GET /api/jobs/my-jobs/ — Recruiter's own jobs."""

    serializer_class = JobListSerializer
    permission_classes = [IsRecruiter]

    def get_queryset(self):
        return Job.objects.filter(recruiter=self.request.user)


class RecruiterJobCreateView(generics.CreateAPIView):
    """POST /api/jobs/create/ — Recruiter creates a job (pending approval)."""

    serializer_class = JobCreateSerializer
    permission_classes = [IsRecruiter]


class RecruiterJobUpdateView(generics.UpdateAPIView):
    """PUT /api/jobs/<id>/edit/ — Recruiter edits own job."""

    serializer_class = JobCreateSerializer
    permission_classes = [IsRecruiter]

    def get_queryset(self):
        return Job.objects.filter(recruiter=self.request.user)


# ─── Candidate Views ─────────────────────────────────────────

class ApprovedJobListView(generics.ListAPIView):
    """GET /api/jobs/approved/ — All approved/live jobs for candidates."""

    serializer_class = JobListSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["title", "company", "description"]

    def get_queryset(self):
        return Job.objects.filter(status=Job.Status.APPROVED)


class JobDetailView(generics.RetrieveAPIView):
    """GET /api/jobs/<id>/ — Job details."""

    serializer_class = JobListSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Job.objects.all()


# ─── Admin Views ──────────────────────────────────────────────

class AdminJobListView(generics.ListAPIView):
    """GET /api/jobs/admin/all/ — Admin sees all jobs."""

    serializer_class = JobListSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["status", "recruiter"]
    search_fields = ["title", "company"]

    def get_queryset(self):
        return Job.objects.all()


class AdminJobApprovalView(generics.UpdateAPIView):
    """PATCH /api/jobs/admin/<id>/approve/ — Admin approves/rejects a job."""

    serializer_class = JobApprovalSerializer
    permission_classes = [IsAdmin]
    queryset = Job.objects.all()

    def partial_update(self, request, *args, **kwargs):
        job = self.get_object()
        serializer = self.get_serializer(job, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": f"Job '{job.title}' has been {job.status}.",
                "job": JobListSerializer(job).data,
            }
        )


class AdminPendingJobsView(generics.ListAPIView):
    """GET /api/jobs/admin/pending/ — Admin sees pending jobs."""

    serializer_class = JobListSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return Job.objects.filter(status=Job.Status.PENDING)
