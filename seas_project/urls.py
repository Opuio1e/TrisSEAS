from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.views.generic import TemplateView

from apps.admin_panel.views import (
    AdminDashboardView,
    AnalyticsView,
    GateConsoleView,
    NotificationsView,
    ParentDashboardView,
    StudentDashboardView,
    live_stats,
)

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),

    # Friendly redirect for older bookmarks/shared links
    path(
        "admin/advancedattendance/advancedrecord/",
        lambda request: redirect("admin:attendance_attendancerecord_changelist"),
    ),

    path("admin/", admin.site.urls),
    path("console/", GateConsoleView.as_view(), name="gate-console"),
    path("ops/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("notifications/", NotificationsView.as_view(), name="notifications"),
    path("student/", StudentDashboardView.as_view(), name="student-dashboard"),
    path("parent/", ParentDashboardView.as_view(), name="parent-dashboard"),
    path("api/live-stats/", live_stats, name="live-stats"),
    path("api/students/", include("apps.students.urls")),
    path("api/entry-gate/", include("apps.entry_gate.urls")),
    path("api/attendance/", include("apps.attendance.urls")),
]
