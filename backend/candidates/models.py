"""
Candidate models: Application (links candidate → job), stores CV file,
extracted text, ML scores, and SHAP explanations.
"""
import os
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


def cv_upload_path(instance, filename):
    """Upload CVs to media/cvs/<user_id>/<filename>"""
    return os.path.join("cvs", str(instance.candidate.id), filename)


class Application(models.Model):
    """
    A candidate's application to a specific job.
    One candidate can apply to multiple jobs.
    Each application stores its own score independently.
    """

    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        SCORED = "scored", "Scored"
        SHORTLISTED = "shortlisted", "Shortlisted"
        REJECTED = "rejected", "Rejected"
        HIRED = "hired", "Hired"

    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
        limit_choices_to={"role": "candidate"},
    )
    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    cv_file = models.FileField(
        upload_to=cv_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
        help_text="PDF only, max 10MB",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_at"]
        unique_together = ["candidate", "job"]  # One application per job

    def __str__(self):
        return f"{self.candidate.get_full_name()} → {self.job.title}"


class CVText(models.Model):
    """
    Extracted text from candidate's CV.
    Stores outputs from all 3 extraction methods + the best one selected.
    """

    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="cv_text",
    )
    # Text from each extraction method
    pdfminer_text = models.TextField(blank=True, default="")
    pymupdf_text = models.TextField(blank=True, default="")
    ocr_text = models.TextField(blank=True, default="")
    # Best text selected by quality heuristics
    best_text = models.TextField(blank=True, default="")
    extraction_method = models.CharField(max_length=20, blank=True, default="")
    # NLP-processed data (JSON)
    skills_extracted = models.JSONField(default=list, blank=True)
    education_extracted = models.JSONField(default=list, blank=True)
    experience_years = models.FloatField(default=0)
    extracted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CV Text for {self.application}"


class ScreeningScore(models.Model):
    """
    ML screening scores for a candidate-job pair.
    Stores individual model scores + ensemble + SHAP explanation.
    """

    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name="score",
    )
    # Hard requirement check
    hard_req_score = models.FloatField(default=0, help_text="0-100 percentage")
    hard_req_passed = models.BooleanField(default=False)
    hard_req_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Per-requirement match details",
    )

    # Individual ML model scores (0-100)
    logistic_regression_score = models.FloatField(default=0)
    naive_bayes_score = models.FloatField(default=0)
    knn_score = models.FloatField(default=0)
    decision_tree_score = models.FloatField(default=0)
    random_forest_score = models.FloatField(default=0)
    svm_score = models.FloatField(default=0)
    xgboost_score = models.FloatField(default=0)
    autogluon_score = models.FloatField(default=0)

    # Ensemble
    ensemble_score = models.FloatField(default=0, help_text="Weighted average 0-100")
    overall_score = models.FloatField(default=0, help_text="Final combined score 0-100")

    # Classification
    LABEL_CHOICES = [("high", "High"), ("medium", "Medium"), ("low", "Low")]
    label = models.CharField(max_length=10, choices=LABEL_CHOICES, default="low")

    # SHAP explanation (JSON)
    shap_explanation = models.JSONField(
        default=dict,
        blank=True,
        help_text="Feature importance + positive/negative factors",
    )

    scored_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-overall_score"]

    def __str__(self):
        return f"Score {self.overall_score}% ({self.label}) for {self.application}"

    def calculate_label(self):
        """Set label based on overall score."""
        if self.overall_score >= 80:
            self.label = "high"
        elif self.overall_score >= 60:
            self.label = "medium"
        else:
            self.label = "low"
        return self.label


class Notification(models.Model):
    """Notification sent to candidate when recruiter shortlists/rejects."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ("shortlisted", "Shortlisted"),
            ("rejected", "Rejected"),
            ("scored", "Scored"),
            ("hired", "Hired"),
            ("info", "Info"),
        ],
        default="info",
    )
    is_read = models.BooleanField(default=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} → {self.user.username}"
