"""
Job model with hard requirements and admin approval workflow.
Flow: Recruiter posts → status='pending' → Admin approves → status='approved' → goes live
"""
from django.db import models
from django.conf import settings


class Job(models.Model):
    """Job posting created by a recruiter, requires admin approval."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CLOSED = "closed", "Closed"

    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posted_jobs",
        limit_choices_to={"role": "recruiter"},
    )
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True, default="")
    salary_range = models.CharField(max_length=100, blank=True, default="")
    job_type = models.CharField(
        max_length=20,
        choices=[
            ("full_time", "Full Time"),
            ("part_time", "Part Time"),
            ("contract", "Contract"),
            ("remote", "Remote"),
        ],
        default="full_time",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    # Admin feedback when rejecting
    admin_notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} @ {self.company} [{self.status}]"

    @property
    def applicant_count(self):
        return self.applications.count()


class HardRequirement(models.Model):
    """
    Hard requirements set by recruiter.
    Candidates MUST match these before ML scoring kicks in.
    """

    class ReqType(models.TextChoices):
        SKILL = "skill", "Skill"
        EXPERIENCE = "experience", "Years of Experience"
        EDUCATION = "education", "Education Level"
        CERTIFICATION = "certification", "Certification"
        OTHER = "other", "Other"

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="hard_requirements",
    )
    requirement_type = models.CharField(
        max_length=20,
        choices=ReqType.choices,
        default=ReqType.SKILL,
    )
    description = models.CharField(max_length=300)
    # Keywords to search for in CV text
    keywords = models.CharField(
        max_length=500,
        help_text="Comma-separated keywords to match in CV (e.g., 'python,django,flask')",
    )
    # Minimum years (for experience type)
    min_years = models.IntegerField(default=0)
    # Is this mandatory or preferred?
    is_mandatory = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_mandatory", "requirement_type"]

    def __str__(self):
        prefix = "MUST" if self.is_mandatory else "PREF"
        return f"[{prefix}] {self.description}"
