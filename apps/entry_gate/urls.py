from django.urls import path
from .views import EnrollView, ScanView

urlpatterns = [
    path("enroll/", EnrollView.as_view(), name="enroll"),
    path("scan/", ScanView.as_view(), name="scan"),
]
