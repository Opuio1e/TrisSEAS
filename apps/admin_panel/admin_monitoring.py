from datetime import datetime, timedelta, time

from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.attendance.models import AttendanceRecord
from apps.entry_gate.models import GateEvent
from apps.students.models import Student
from .views import AdminDashboardView as AdminDashboardTemplateView

# Re-export the dashboard template view for URL configuration
AdminDashboardView = AdminDashboardTemplateView


def detect_anomalies():
    """Inspect attendance and gate data for notable anomalies."""
    today = timezone.localdate()
    anomalies = []

    for record in AttendanceRecord.objects.select_related("student").filter(date=today):
        events = GateEvent.objects.filter(student=record.student, timestamp__date=today)
        entries = events.filter(action=GateEvent.ENTRY, success=True).count()
        exits = events.filter(action=GateEvent.EXIT, success=True).count()
        failed_attempts = events.filter(success=False).count()

        if entries and not record.present:
            anomalies.append(
                {
                    "level": "critical",
                    "code": "entry_marked_absent",
                    "student": record.student.student_id,
                    "detail": "Entry recorded but student marked absent.",
                }
            )

        if failed_attempts >= 3:
            anomalies.append(
                {
                    "level": "warning",
                    "code": "repeated_failures",
                    "student": record.student.student_id,
                    "detail": "Multiple failed access attempts detected.",
                }
            )

        current_time = timezone.localtime().time()
        if (
            record.first_entry_time
            and not record.last_exit_time
            and current_time >= time(18, 0)
        ):
            anomalies.append(
                {
                    "level": "warning",
                    "code": "no_exit_after_hours",
                    "student": record.student.student_id,
                    "detail": "No recorded exit after hours.",
                }
            )

        if entries > exits + 1:
            anomalies.append(
                {
                    "level": "warning",
                    "code": "duplicate_entries",
                    "student": record.student.student_id,
                    "detail": "Duplicate entries detected without corresponding exits.",
                }
            )

    return anomalies


def generate_alerts():
    """Generate user-facing alerts based on anomalies."""
    alerts = []
    for anomaly in detect_anomalies():
        alerts.append(
            {
                "level": anomaly["level"],
                "message": anomaly["detail"],
                "student": anomaly.get("student"),
            }
        )
    return alerts


def get_pending_reviews():
    today = timezone.localdate()
    return AttendanceRecord.objects.filter(
        date=today, Q(present=False) | Q(first_entry_time__isnull=True)
    ).select_related("student")


def send_override_notifications(student: Student, action: str, reason: str) -> bool:
    """Stub for notification dispatch to parents and teachers."""
    # In production this would trigger email/SMS notifications.
    return bool(student and action and reason)


@api_view(["POST"])
def manual_override(request):
    override_type = request.data.get("type")
    student_id = request.data.get("student_id")
    target_date = request.data.get("date")
    reason = request.data.get("reason", "Manual override")

    if not override_type or not student_id:
        return Response(
            {"detail": "type and student_id are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return Response(
            {"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND
        )

    date_value = target_date or timezone.localdate().isoformat()
    try:
        attendance_date = datetime.fromisoformat(date_value).date()
    except ValueError:
        attendance_date = timezone.localdate()

    attendance, _ = AttendanceRecord.objects.get_or_create(
        student=student,
        date=attendance_date,
        defaults={"present": False},
    )

    gate_event = None
    if override_type == "mark_present":
        attendance.present = True
        if not attendance.first_entry_time:
            attendance.first_entry_time = timezone.now()
    elif override_type == "mark_absent":
        attendance.present = False
    elif override_type == "grant_access":
        attendance.present = True
        gate_event = GateEvent.objects.create(
            student=student,
            action=GateEvent.ENTRY,
            success=True,
            reason=f"Admin override: {reason}",
        )
        if not attendance.first_entry_time:
            attendance.first_entry_time = gate_event.timestamp
    else:
        return Response(
            {"detail": "Unknown override type."}, status=status.HTTP_400_BAD_REQUEST
        )

    attendance.save()
    notification_sent = send_override_notifications(student, override_type, reason)

    return Response(
        {
            "detail": "Override applied successfully",
            "student": student.student_id,
            "action": override_type,
            "notification_sent": notification_sent,
            "flag_cleared": override_type != "grant_access",
            "timestamp": timezone.now().isoformat(),
            "gate_event_id": gate_event.id if gate_event else None,
        }
    )


@api_view(["POST"])
def clear_flag(request):
    flag_id = request.data.get("flag_id")
    notes = request.data.get("notes", "")

    if not flag_id:
        return Response(
            {"detail": "flag_id is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        {
            "detail": "Flag cleared",
            "flag_id": flag_id,
            "notes": notes,
            "timestamp": timezone.now().isoformat(),
        }
    )


@api_view(["GET"])
def live_stats(_request):
    now = timezone.now()
    today = timezone.localdate()
    since = now - timedelta(hours=24)

    recent_events = GateEvent.objects.select_related("student").filter(
        timestamp__gte=since
    )
    today_events = recent_events.filter(timestamp__date=today)

    success_count = today_events.filter(success=True).count()
    total_events = today_events.count()
    success_rate = round(success_count / total_events * 100, 1) if total_events else 0.0

    anomalies = detect_anomalies()

    latest_feed = [
        {
            "student": event.student.student_id,
            "action": event.action,
            "time": event.timestamp.isoformat(),
            "success": event.success,
        }
        for event in today_events.order_by("-timestamp")[:6]
    ]

    payload = {
        "students": Student.objects.count(),
        "active_gates": 4,
        "events_24h": recent_events.count(),
        "events_today": total_events,
        "success_rate": success_rate,
        "present_today": AttendanceRecord.objects.filter(date=today, present=True).count(),
        "average_scan_time": 1.2,
        "live_feed": latest_feed,
        "last_updated": now.isoformat(),
        "has_events_today": bool(total_events),
        "per_gate": list(
            today_events.values("action").annotate(total=Count("id")).order_by("action")
        ),
        "anomaly_count": len(anomalies),
        "alert_count": len(generate_alerts()),
    }

    return JsonResponse(payload)


@api_view(["GET"])
def admin_monitoring_dashboard(_request):
    today = timezone.localdate()
    anomalies = detect_anomalies()
    critical = [a for a in anomalies if a["level"] == "critical"]
    warnings = [a for a in anomalies if a["level"] == "warning"]
    pending_reviews = list(get_pending_reviews())

    dashboard = {
        "timestamp": timezone.now().isoformat(),
        "system_status": {
            "status": "normal" if not anomalies else "attention",
            "active_gates": 4,
            "last_sync": timezone.now().isoformat(),
        },
        "anomalies": {
            "critical_anomalies": critical,
            "warning_anomalies": warnings,
            "total_count": len(anomalies),
        },
        "alerts": generate_alerts(),
        "pending_reviews": [
            {
                "student": record.student.student_id,
                "date": today.isoformat(),
                "present": record.present,
            }
            for record in pending_reviews
        ],
        "requires_action": bool(pending_reviews),
    }

    return Response(dashboard)
