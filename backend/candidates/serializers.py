"""
Serializers for Application, CVText, and ScreeningScore.
"""
from rest_framework import serializers
from django.conf import settings

from .models import Application, CVText, ScreeningScore
from jobs.serializers import JobListSerializer


class CVTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVText
        fields = [
            "skills_extracted", "education_extracted",
            "experience_years", "extraction_method", "extracted_at",
        ]


class ScreeningScoreSerializer(serializers.ModelSerializer):
    """Full score breakdown with all model scores + SHAP."""

    class Meta:
        model = ScreeningScore
        fields = [
            "hard_req_score", "hard_req_passed", "hard_req_details",
            "logistic_regression_score", "naive_bayes_score",
            "knn_score", "decision_tree_score", "random_forest_score",
            "svm_score", "xgboost_score", "autogluon_score",
            "ensemble_score", "overall_score", "label",
            "shap_explanation", "scored_at",
        ]


class ApplicationListSerializer(serializers.ModelSerializer):
    """Application list with basic score info."""

    job = JobListSerializer(read_only=True)
    candidate_name = serializers.CharField(
        source="candidate.get_full_name", read_only=True
    )
    candidate_email = serializers.CharField(
        source="candidate.email", read_only=True
    )
    overall_score = serializers.FloatField(
        source="score.overall_score", read_only=True, default=0
    )
    score_label = serializers.CharField(
        source="score.label", read_only=True, default="pending"
    )

    class Meta:
        model = Application
        fields = [
            "id", "candidate_name", "candidate_email", "job",
            "status", "overall_score", "score_label", "applied_at",
        ]


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """Full application detail with CV data and scores."""

    job = JobListSerializer(read_only=True)
    candidate_name = serializers.CharField(
        source="candidate.get_full_name", read_only=True
    )
    cv_text = CVTextSerializer(read_only=True)
    score = ScreeningScoreSerializer(read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "candidate_name", "job", "cv_file",
            "status", "cv_text", "score", "applied_at",
        ]


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Create an application (candidate applies to a job with CV)."""

    class Meta:
        model = Application
        fields = ["id", "job", "cv_file"]

    def validate_cv_file(self, value):
        if value.size > settings.MAX_CV_FILE_SIZE:
            raise serializers.ValidationError("CV file must be under 10MB.")
        if not value.name.lower().endswith(".pdf"):
            raise serializers.ValidationError("Only PDF files are accepted.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        job = attrs["job"]
        # Check job is approved
        if job.status != "approved":
            raise serializers.ValidationError("This job is not accepting applications.")
        # Check not already applied
        if Application.objects.filter(candidate=user, job=job).exists():
            raise serializers.ValidationError("You have already applied to this job.")
        return attrs

    def create(self, validated_data):
        application = Application.objects.create(
            candidate=self.context["request"].user,
            **validated_data,
        )
        return application


class ApplicationStatusSerializer(serializers.ModelSerializer):
    """Recruiter/Admin update application status (shortlist, reject)."""

    class Meta:
        model = Application
        fields = ["id", "status"]

    def validate_status(self, value):
        allowed = [
            Application.Status.SHORTLISTED,
            Application.Status.REJECTED,
            Application.Status.HIRED,
        ]
        if value not in allowed:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(allowed)}"
            )
        return value
