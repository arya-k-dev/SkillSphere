from django.contrib import admin

from .models import Session, SessionFeedback


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("title", "mentor", "learner", "scheduled_date", "scheduled_time", "status")
    list_filter = ("status", "format", "scheduled_date")
    search_fields = ("title", "mentor__username", "learner__username", "description")


@admin.register(SessionFeedback)
class SessionFeedbackAdmin(admin.ModelAdmin):
    list_display = ("session", "given_by", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("given_by__username", "comments", "session__title", "session__topics_covered")
