from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/students/", include("apps.students.urls")),
    path("api/entry-gate/", include("apps.entry_gate.urls")),
    path("api/attendance/", include("apps.attendance.urls")),
]
