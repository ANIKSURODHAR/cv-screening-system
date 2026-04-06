from django.urls import path
from . import views

urlpatterns = [
    # Candidate — browse approved jobs
    path("approved/", views.ApprovedJobListView.as_view(), name="approved-jobs"),
    path("<int:pk>/", views.JobDetailView.as_view(), name="job-detail"),
    # Recruiter — manage own jobs
    path("my-jobs/", views.RecruiterJobListView.as_view(), name="my-jobs"),
    path("create/", views.RecruiterJobCreateView.as_view(), name="job-create"),
    path("<int:pk>/edit/", views.RecruiterJobUpdateView.as_view(), name="job-edit"),
    # Admin — approve/reject, list all
    path("admin/all/", views.AdminJobListView.as_view(), name="admin-jobs"),
    path("admin/pending/", views.AdminPendingJobsView.as_view(), name="admin-pending"),
    path("admin/<int:pk>/approve/", views.AdminJobApprovalView.as_view(), name="admin-approve"),
]
