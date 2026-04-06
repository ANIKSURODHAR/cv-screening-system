from django.contrib import admin
from .models import Application, CVText, ScreeningScore


class CVTextInline(admin.StackedInline):
    model = CVText
    extra = 0
    readonly_fields = ["extraction_method", "skills_extracted", "experience_years"]


class ScreeningScoreInline(admin.StackedInline):
    model = ScreeningScore
    extra = 0
    readonly_fields = ["overall_score", "label", "ensemble_score", "hard_req_passed"]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["candidate", "job", "status", "get_score", "applied_at"]
    list_filter = ["status", "applied_at"]
    search_fields = ["candidate__username", "candidate__email", "job__title"]
    inlines = [CVTextInline, ScreeningScoreInline]

    def get_score(self, obj):
        try:
            return f"{obj.score.overall_score}% ({obj.score.label})"
        except ScreeningScore.DoesNotExist:
            return "Pending"
    get_score.short_description = "Score"
