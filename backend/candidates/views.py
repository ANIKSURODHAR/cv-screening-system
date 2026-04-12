"""
Views for candidate applications + notifications.
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes as perm
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Application, ScreeningScore, Notification
from .serializers import (
    ApplicationListSerializer,
    ApplicationDetailSerializer,
    ApplicationCreateSerializer,
    ApplicationStatusSerializer,
    NotificationSerializer,
)
from accounts.permissions import IsAdmin, IsRecruiter, IsCandidate, IsAdminOrRecruiter


# ─── Candidate Views ─────────────────────────────────────────

class CandidateApplyView(generics.CreateAPIView):
    serializer_class = ApplicationCreateSerializer
    permission_classes = [IsCandidate]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        # Run scoring directly
        try:
            from ml_engine.pipeline import run_scoring_pipeline
            run_scoring_pipeline(application.id)
        except Exception as e:
            print(f"Scoring error: {e}")

        return Response(
            {"message": "Application submitted!", "application_id": application.id},
            status=status.HTTP_201_CREATED,
        )


class CandidateApplicationsView(generics.ListAPIView):
    serializer_class = ApplicationListSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user).select_related("job", "score")


class CandidateApplicationDetailView(generics.RetrieveAPIView):
    serializer_class = ApplicationDetailSerializer
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user).select_related("job", "cv_text", "score")


# ─── Recruiter Views ─────────────────────────────────────────

class RecruiterApplicantsView(generics.ListAPIView):
    serializer_class = ApplicationListSerializer
    permission_classes = [IsAdminOrRecruiter]

    def get_queryset(self):
        job_id = self.kwargs["job_id"]
        qs = Application.objects.filter(job_id=job_id).select_related("candidate", "job", "score")
        if self.request.user.is_recruiter:
            qs = qs.filter(job__recruiter=self.request.user)
        return qs.order_by("-score__overall_score")


class RecruiterApplicantDetailView(generics.RetrieveAPIView):
    serializer_class = ApplicationDetailSerializer
    permission_classes = [IsAdminOrRecruiter]

    def get_queryset(self):
        qs = Application.objects.select_related("job", "cv_text", "score")
        if self.request.user.is_recruiter:
            qs = qs.filter(job__recruiter=self.request.user)
        return qs


class RecruiterUpdateStatusView(generics.UpdateAPIView):
    serializer_class = ApplicationStatusSerializer
    permission_classes = [IsAdminOrRecruiter]

    def get_queryset(self):
        qs = Application.objects.all()
        if self.request.user.is_recruiter:
            qs = qs.filter(job__recruiter=self.request.user)
        return qs

    def perform_update(self, serializer):
        application = serializer.save()
        st = application.status
        job_title = application.job.title
        company = application.job.company

        if st == "shortlisted":
            Notification.objects.create(
                user=application.candidate,
                title=f"Shortlisted for {job_title}!",
                message=f"Congratulations! You've been shortlisted for '{job_title}' at {company}. The recruiter was impressed with your profile!",
                notification_type="shortlisted",
                application=application,
            )
        elif st == "rejected":
            Notification.objects.create(
                user=application.candidate,
                title=f"Update: {job_title}",
                message=f"Your application for '{job_title}' at {company} has been reviewed. Unfortunately, the team decided to move forward with other candidates. Check your score details for improvement tips!",
                notification_type="rejected",
                application=application,
            )
        elif st == "hired":
            Notification.objects.create(
                user=application.candidate,
                title=f"Hired for {job_title}!",
                message=f"Amazing news! You've been selected for '{job_title}' at {company}. Congratulations!",
                notification_type="hired",
                application=application,
            )


# ─── Admin Views ──────────────────────────────────────────────

class AdminAllApplicationsView(generics.ListAPIView):
    serializer_class = ApplicationListSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["status", "job"]

    def get_queryset(self):
        return Application.objects.all().select_related("candidate", "job", "score")


# ─── Notification Views ──────────────────────────────────────

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@api_view(["POST"])
@perm([IsAuthenticated])
def mark_notification_read(request, pk):
    try:
        n = Notification.objects.get(id=pk, user=request.user)
        n.is_read = True
        n.save()
        return Response({"status": "read"})
    except Notification.DoesNotExist:
        return Response({"error": "Not found"}, status=404)


@api_view(["POST"])
@perm([IsAuthenticated])
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({"status": "all read"})


@api_view(["GET"])
@perm([IsAuthenticated])
def unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({"count": count})
