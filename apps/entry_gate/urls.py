from django.urls import path
from .views import (
    EnrollView,
    ScanView,
    RFIDScanView,
    ManualCheckInView,
)

urlpatterns = [
    path("enroll/", EnrollView.as_view(), name="enroll"),
    path("scan/", ScanView.as_view(), name="scan"),
    path("rfid-scan/", RFIDScanView.as_view(), name="rfid-scan"),
    path("manual-checkin/", ManualCheckInView.as_view(), name="manual-checkin"),
]
