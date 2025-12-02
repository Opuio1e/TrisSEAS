from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import path, include

from apps.admin_panel.views import (
    AnalyticsView,
    GateConsoleView,
    NotificationsView,
    ParentDashboardView,
    StudentDashboardView,
)
from apps.admin_panel.admin_monitoring import (
    AdminDashboardView,
    admin_monitoring_dashboard,
    manual_override,
    clear_flag,
    live_stats,
)
from apps.users.views import RoleBasedLoginView

urlpatterns = [
    # Authentication
    path("", RoleBasedLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Admin
    path("admin/", admin.site.urls),
    path(
        "admin/advancedattendance/advancedrecord/",
        lambda request: redirect("admin:attendance_attendancerecord_changelist"),
    ),

    # Dashboards
    path("console/", GateConsoleView.as_view(), name="gate-console"),
    path("ops/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("notifications/", NotificationsView.as_view(), name="notifications"),
    path("student/", StudentDashboardView.as_view(), name="student-dashboard"),
    path("parent/", ParentDashboardView.as_view(), name="parent-dashboard"),

    # API Endpoints
    path("api/live-stats/", live_stats, name="live-stats"),
    path("api/admin/monitoring/", admin_monitoring_dashboard, name="admin-monitoring"),
    path("api/admin/manual-override/", manual_override, name="manual-override"),
    path("api/admin/clear-flag/", clear_flag, name="clear-flag"),

    # App APIs
    path("api/students/", include("apps.students.urls")),
    path("api/entry-gate/", include("apps.entry_gate.urls")),
    path("api/attendance/", include("apps.attendance.urls")),
]
