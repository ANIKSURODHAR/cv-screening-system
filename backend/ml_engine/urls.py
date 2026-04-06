from django.urls import path
from . import views

urlpatterns = [
    path("status/<int:application_id>/", views.score_status, name="score-status"),
    path("rescore/<int:job_id>/", views.rescore_job, name="rescore-job"),
    path("models/", views.model_info, name="model-info"),
]
