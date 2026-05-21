from django.contrib import admin

from .models import Achievement, Certificate, UserAchievement


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "points", "target_value", "icon_label")
    search_fields = ("name", "code", "description")


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "unlocked_at", "progress_value", "target_value")
    list_filter = ("achievement", "unlocked_at")
    search_fields = ("user__username", "achievement__name")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_id", "user", "certificate_type", "skill", "issued_date", "verification_code")
    list_filter = ("certificate_type", "issued_date")
    search_fields = ("user__username", "certificate_id", "verification_code", "skill__name")
