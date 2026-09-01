from django.contrib import admin

from .models import Application, Grant


@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    list_display = ("name", "deadline", "is_open")
    list_filter = ("is_open",)
    search_fields = ("name", "description")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("applicant_name", "grant", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("applicant_name", "applicant_email", "grant__name")
