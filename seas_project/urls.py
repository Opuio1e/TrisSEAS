from django.contrib import admin
from django.urls import path, include
from apps.admin_panel.views import AdminPanelView, GateConsoleView, HomeView, LiveSnapshotView
from apps.analytics.views import AnalyticsView
from apps.notifications.views import NotificationCenterView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("admin/panel/", AdminPanelView.as_view(), name="admin-panel"),
    path("analytics/", AnalyticsView.as_view(), name="analytics"),
    path("notifications/", NotificationCenterView.as_view(), name="notifications"),
    path("console/", GateConsoleView.as_view(), name="gate-console"),
    path("api/students/", include("apps.students.urls")),
    path("api/entry-gate/", include("apps.entry_gate.urls")),
    path("api/attendance/", include("apps.attendance.urls")),
    path("api/live-snapshot/", LiveSnapshotView.as_view(), name="live-snapshot"),
]
