"""
Serializers for Job and HardRequirement models.
"""
from rest_framework import serializers
from .models import Job, HardRequirement
from accounts.serializers import UserListSerializer


class HardRequirementSerializer(serializers.ModelSerializer):
    """Serialize hard requirements."""

    class Meta:
        model = HardRequirement
        fields = [
            "id", "requirement_type", "description", "keywords",
            "min_years", "is_mandatory", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class JobListSerializer(serializers.ModelSerializer):
    """Lightweight job serializer for lists."""

    recruiter_name = serializers.CharField(source="recruiter.get_full_name", read_only=True)
    applicant_count = serializers.IntegerField(read_only=True)
    hard_requirements = HardRequirementSerializer(many=True, read_only=True)

    class Meta:
        model = Job
        fields = [
            "id", "title", "company", "description", "location",
            "salary_range", "job_type", "status", "recruiter_name",
            "applicant_count", "hard_requirements", "created_at",
        ]


class JobCreateSerializer(serializers.ModelSerializer):
    """Create a job with hard requirements."""

    hard_requirements = HardRequirementSerializer(many=True, required=False)

    class Meta:
        model = Job
        fields = [
            "id", "title", "company", "description", "location",
            "salary_range", "job_type", "hard_requirements",
        ]

    def create(self, validated_data):
        hard_reqs_data = validated_data.pop("hard_requirements", [])
        # Status is always pending on creation
        job = Job.objects.create(
            **validated_data,
            recruiter=self.context["request"].user,
            status=Job.Status.PENDING,
        )
        for req_data in hard_reqs_data:
            HardRequirement.objects.create(job=job, **req_data)
        return job

    def update(self, instance, validated_data):
        hard_reqs_data = validated_data.pop("hard_requirements", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if hard_reqs_data is not None:
            instance.hard_requirements.all().delete()
            for req_data in hard_reqs_data:
                HardRequirement.objects.create(job=instance, **req_data)

        return instance


class JobApprovalSerializer(serializers.ModelSerializer):
    """Admin approve/reject a job."""

    class Meta:
        model = Job
        fields = ["id", "status", "admin_notes"]

    def validate_status(self, value):
        if value not in [Job.Status.APPROVED, Job.Status.REJECTED]:
            raise serializers.ValidationError(
                "Status must be 'approved' or 'rejected'."
            )
        return value
