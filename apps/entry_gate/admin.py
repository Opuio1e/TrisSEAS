from django.contrib import admin

from .models import GateEvent


@admin.register(GateEvent)
class GateEventAdmin(admin.ModelAdmin):
    list_display = ("student", "action", "timestamp", "success", "reason")
    list_filter = ("action", "success", "timestamp")
    search_fields = ("student__student_id", "student__user__first_name", "student__user__last_name")
    ordering = ("-timestamp",)
    readonly_fields = ("timestamp",)
    fieldsets = (
        (None, {"fields": ("student", "action", "success", "reason")}),
        ("Log", {"fields": ("timestamp",)}),
    )
