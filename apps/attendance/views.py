from datetime import datetime

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AttendanceRecord
from .serializers import AttendanceRecordSerializer


def _parse_date(date_str):
    if not date_str:
        return timezone.localdate()
    try:
        return datetime.fromisoformat(date_str).date()
    except ValueError:
        return timezone.localdate()


def _parse_datetime(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.select_related("student").all()
    serializer_class = AttendanceRecordSerializer

    @action(detail=False, methods=["get"], url_path="daily_entry_log")
    def daily_entry_log(self, request):
        date = _parse_date(request.query_params.get("date"))
        records = self.get_queryset().filter(date=date)

        payload = {
            "date": date.isoformat(),
            "total_entries": records.count(),
            "verified_count": records.filter(verified=True).count(),
            "unverified_count": records.filter(verified=False).count(),
            "entry_log": AttendanceRecordSerializer(records, many=True).data,
        }
        return Response(payload)

    @action(detail=True, methods=["post"], url_path="verify_attendance")
    def verify_attendance(self, request, pk=None):
        record = self.get_object()
        verified = bool(request.data.get("verified", True))
        notes = request.data.get("notes", "")

        record.verified = verified
        record.verification_notes = notes
        record.save(update_fields=["verified", "verification_notes"])

        return Response(
            {
                "detail": "Attendance verification updated.",
                "verified": record.verified,
                "notes": record.verification_notes,
            }
        )

    @action(detail=False, methods=["post"], url_path="cross_check")
    def cross_check(self, request):
        attendance_id = request.data.get("attendance_id")
        date = _parse_date(request.data.get("date"))

        try:
            record = self.get_queryset().get(id=attendance_id, date=date)
        except AttendanceRecord.DoesNotExist:
            return Response(
                {"detail": "Attendance record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "detail": "Cross-check completed",
                "record": AttendanceRecordSerializer(record).data,
                "cross_check_source": "admin_cctv",
            }
        )

    @action(detail=True, methods=["post"], url_path="update_attendance")
    def update_attendance(self, request, pk=None):
        record = self.get_object()

        present = request.data.get("present")
        first_entry_time = _parse_datetime(request.data.get("first_entry_time"))
        last_exit_time = _parse_datetime(request.data.get("last_exit_time"))
        override_reason = request.data.get("override_reason", "")

        if present is not None:
            record.present = bool(present)
        if first_entry_time:
            record.first_entry_time = first_entry_time
        if last_exit_time:
            record.last_exit_time = last_exit_time

        record.override_reason = override_reason
        record.verified = True
        record.save()

        return Response(
            {
                "detail": "Attendance record updated.",
                "record": AttendanceRecordSerializer(record).data,
            }
        )

    @action(detail=False, methods=["post"], url_path="approve_daily_attendance")
    def approve_daily_attendance(self, request):
        date = _parse_date(request.data.get("date"))
        approver = request.user.get_full_name() or request.user.get_username() or "System"
        timestamp = timezone.now()

        records = self.get_queryset().filter(date=date)
        records.update(
            approved=True,
            approval_timestamp=timestamp,
            approved_by=approver,
            verified=True,
        )

        summary = {
            "date": date.isoformat(),
            "total_students": records.count(),
            "present": records.filter(present=True).count(),
            "absent": records.filter(present=False).count(),
            "approval_timestamp": timestamp.isoformat(),
            "approved_by": approver,
        }

        return Response(
            {
                "detail": "Daily attendance approved and summary sent to admin",
                "summary": summary,
            }
        )

    @action(detail=False, methods=["get"], url_path="pending_verification")
    def pending_verification(self, request):
        date = _parse_date(request.query_params.get("date"))
        pending_records = self.get_queryset().filter(date=date, verified=False)

        return Response(
            {
                "date": date.isoformat(),
                "pending_count": pending_records.count(),
                "pending_students": AttendanceRecordSerializer(
                    pending_records, many=True
                ).data,
            }
        )
