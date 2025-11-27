from django.contrib import admin

from .models import AttendanceRecord


@admin.action(description="Mark selected as present")
def mark_present(modeladmin, request, queryset):
    queryset.update(present=True)


@admin.action(description="Mark selected as absent")
def mark_absent(modeladmin, request, queryset):
    queryset.update(present=False)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "first_entry_time", "last_exit_time", "present")
    list_filter = ("present", "date")
    search_fields = (
        "student__student_id",
        "student__user__first_name",
        "student__user__last_name",
        "student__user__email",
    )
    ordering = ("-date", "student__student_id")
    date_hierarchy = "date"
    actions = (mark_present, mark_absent)

    fieldsets = (
        (None, {"fields": ("student", "date", "present")}),
        (
            "Entry & exit times",
            {"fields": ("first_entry_time", "last_exit_time"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ()
