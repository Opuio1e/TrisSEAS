from datetime import datetime

from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.entry_gate.models import GateEvent
from .models import AttendanceRecord
from .serializers import AttendanceRecordSerializer


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.select_related("student").all()
    serializer_class = AttendanceRecordSerializer

    def _get_target_date(self, date_str: str | None) -> datetime.date:
        """Parse a date string (YYYY-MM-DD) or return today's date."""
        if not date_str:
            return timezone.localdate()

        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return timezone.localdate()

    @action(detail=False, methods=["get"], url_path="daily_entry_log")
    def daily_entry_log(self, request):
        target_date = self._get_target_date(request.query_params.get("date"))
        records = self.queryset.filter(date=target_date)

        payload = {
            "date": target_date.isoformat(),
            "total_entries": records.count(),
            "verified_count": records.filter(present=True).count(),
            "unverified_count": records.filter(present=False).count(),
            "entry_log": AttendanceRecordSerializer(records, many=True).data,
        }
        return Response(payload)

    @action(detail=True, methods=["post"], url_path="verify_attendance")
    def verify_attendance(self, request, pk=None):
        record = self.get_object()
        verified = request.data.get("verified", True)
        notes = request.data.get("notes", "")

        if isinstance(verified, str):
            verified_flag = verified.lower() in ("1", "true", "yes", "on")
        else:
            verified_flag = bool(verified)

        record.present = verified_flag
        if verified_flag and not record.first_entry_time:
            record.first_entry_time = timezone.now()
        record.save(update_fields=["present", "first_entry_time", "last_exit_time"])

        serializer = self.get_serializer(record)
        return Response(
            {
                "detail": "Attendance verified",
                "notes": notes,
                "record": serializer.data,
            }
        )

    @action(detail=False, methods=["post"], url_path="cross_check")
    def cross_check(self, request):
        attendance_id = request.data.get("attendance_id")
        target_date = self._get_target_date(request.data.get("date"))

        try:
            record = self.queryset.get(id=attendance_id, date=target_date)
        except AttendanceRecord.DoesNotExist:
            return Response(
                {"detail": "Attendance record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        events = GateEvent.objects.filter(
            student=record.student, timestamp__date=target_date
        ).order_by("timestamp")

        comparison = {
            "attendance_id": record.id,
            "student": record.student.student_id,
            "date": target_date.isoformat(),
            "gate_events": [
                {
                    "action": event.action,
                    "time": event.timestamp.isoformat(),
                    "success": event.success,
                    "reason": event.reason,
                }
                for event in events
            ],
            "status_match": record.present or events.filter(success=True).exists(),
            "notes": request.data.get("notes", "Cross-check completed"),
        }

        return Response(comparison)

    @action(detail=True, methods=["post"], url_path="update_attendance")
    def update_attendance(self, request, pk=None):
        record = self.get_object()
        present = request.data.get("present")
        first_entry_time = request.data.get("first_entry_time")
        last_exit_time = request.data.get("last_exit_time")
        override_reason = request.data.get("override_reason", "")

        if present is not None:
            if isinstance(present, str):
                record.present = present.lower() in ("1", "true", "yes", "on")
            else:
                record.present = bool(present)

        if first_entry_time:
            try:
                record.first_entry_time = datetime.fromisoformat(first_entry_time)
            except ValueError:
                pass

        if last_exit_time:
            try:
                record.last_exit_time = datetime.fromisoformat(last_exit_time)
            except ValueError:
                pass

        record.save()

        serializer = self.get_serializer(record)
        return Response(
            {
                "detail": "Attendance updated",
                "override_reason": override_reason,
                "record": serializer.data,
            }
        )

    @action(detail=False, methods=["post"], url_path="approve_daily_attendance")
    def approve_daily_attendance(self, request):
        target_date = self._get_target_date(request.data.get("date"))
        records = self.queryset.filter(date=target_date)

        summary = {
            "date": target_date.isoformat(),
            "total_students": records.count(),
            "present": records.filter(present=True).count(),
            "absent": records.filter(present=False).count(),
            "approval_timestamp": timezone.now().isoformat(),
            "approved_by": request.user.get_full_name() or request.user.username,
        }

        return Response(
            {
                "detail": "Daily attendance approved and summary sent to admin",
                "summary": summary,
            }
        )

    @action(detail=False, methods=["get"], url_path="pending_verification")
    def pending_verification(self, request):
        target_date = self._get_target_date(request.query_params.get("date"))
        pending_records = self.queryset.filter(
            date=target_date,
            Q(present=False) | Q(first_entry_time__isnull=True),
        )

        data = {
            "date": target_date.isoformat(),
            "pending_count": pending_records.count(),
            "pending_students": AttendanceRecordSerializer(
                pending_records, many=True
            ).data,
        }
        return Response(data)
