from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from apps.admin_panel.views import GateConsoleView

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("admin/", admin.site.urls),
    path("console/", GateConsoleView.as_view(), name="gate-console"),
    path("api/students/", include("apps.students.urls")),
    path("api/entry-gate/", include("apps.entry_gate.urls")),
    path("api/attendance/", include("apps.attendance.urls")),
]
