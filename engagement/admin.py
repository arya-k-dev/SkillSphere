from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_id", "user", "certificate_type", "skill", "issued_date", "verification_code")
    list_filter = ("certificate_type", "issued_date")
    search_fields = ("user__username", "certificate_id", "verification_code", "skill__name")
