from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "user", "rfid_tag", "parent_email")
    search_fields = ("student_id", "user__username", "user__first_name", "user__last_name", "rfid_tag")
    list_filter = ("rfid_tag",)
    ordering = ("student_id",)
    fieldsets = (
        (None, {"fields": ("user", "student_id", "rfid_tag")}),
        ("Contact", {"fields": ("parent_email",)}),
    )
