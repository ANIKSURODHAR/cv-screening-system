from django.urls import path
from . import views

urlpatterns = [
    # Candidate
    path("apply/", views.CandidateApplyView.as_view(), name="apply"),
    path("my-applications/", views.CandidateApplicationsView.as_view(), name="my-apps"),
    path("my-applications/<int:pk>/", views.CandidateApplicationDetailView.as_view(), name="my-app-detail"),
    # Recruiter
    path("job/<int:job_id>/applicants/", views.RecruiterApplicantsView.as_view(), name="job-applicants"),
    path("applicant/<int:pk>/", views.RecruiterApplicantDetailView.as_view(), name="applicant-detail"),
    path("applicant/<int:pk>/status/", views.RecruiterUpdateStatusView.as_view(), name="applicant-status"),
    # Admin
    path("admin/all/", views.AdminAllApplicationsView.as_view(), name="admin-applications"),
]
