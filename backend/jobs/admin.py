from django.contrib import admin
from .models import Job, HardRequirement


class HardRequirementInline(admin.TabularInline):
    model = HardRequirement
    extra = 1


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "recruiter", "status", "applicant_count", "created_at"]
    list_filter = ["status", "job_type", "created_at"]
    search_fields = ["title", "company", "description"]
    inlines = [HardRequirementInline]
    actions = ["approve_jobs", "reject_jobs"]

    @admin.action(description="Approve selected jobs")
    def approve_jobs(self, request, queryset):
        queryset.update(status=Job.Status.APPROVED)

    @admin.action(description="Reject selected jobs")
    def reject_jobs(self, request, queryset):
        queryset.update(status=Job.Status.REJECTED)
