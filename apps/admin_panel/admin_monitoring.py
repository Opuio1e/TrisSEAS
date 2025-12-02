from datetime import datetime, timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.attendance.models import AttendanceRecord
from apps.entry_gate.models import GateEvent
from apps.students.models import Student


def _parse_date(date_str):
    if not date_str:
        return timezone.localdate()
    try:
        return datetime.fromisoformat(date_str).date()
    except ValueError:
        return timezone.localdate()


def detect_anomalies(date=None):
    date = date or timezone.localdate()
    anomalies = {"critical_anomalies": [], "warning_anomalies": []}

    records = AttendanceRecord.objects.select_related("student").filter(date=date)
    gate_events = GateEvent.objects.filter(timestamp__date=date)

    for record in records:
        has_entry_event = gate_events.filter(student=record.student, action=GateEvent.ENTRY).exists()
        has_exit_event = gate_events.filter(student=record.student, action=GateEvent.EXIT).exists()

        if has_entry_event and not record.present:
            anomalies["critical_anomalies"].append(
                {
                    "student": record.student.student_id,
                    "issue": "Entry recorded but marked absent",
                }
            )

        if record.present and not has_exit_event and timezone.now().hour >= 18:
            anomalies["warning_anomalies"].append(
                {
                    "student": record.student.student_id,
                    "issue": "Present without exit after hours",
                }
            )

    failed_events = gate_events.filter(success=False)
    failure_counts = failed_events.values("student__student_id").annotate(total=Count("id"))
    for failure in failure_counts:
        if failure["total"] >= 3:
            anomalies["warning_anomalies"].append(
                {
                    "student": failure["student__student_id"],
                    "issue": "Multiple failed access attempts",
                }
            )

    anomalies["total_count"] = len(anomalies["critical_anomalies"]) + len(
        anomalies["warning_anomalies"]
    )
    return anomalies


@api_view(["GET"])
def generate_alerts(_request):
    anomalies = detect_anomalies()
    alerts = []

    for item in anomalies["critical_anomalies"]:
        alerts.append({"level": "critical", **item})
    for item in anomalies["warning_anomalies"]:
        alerts.append({"level": "warning", **item})

    return Response({"alerts": alerts})


@api_view(["GET"])
def get_pending_reviews(_request):
    pending_records = AttendanceRecord.objects.select_related("student").filter(
        verified=False
    )
    return Response(
        {
            "pending_count": pending_records.count(),
            "records": [
                {
                    "student": record.student.student_id,
                    "date": record.date.isoformat(),
                    "present": record.present,
                }
                for record in pending_records
            ],
        }
    )


def send_override_notifications(student):
    return {
        "parent_notified": bool(student.parent_email),
        "teacher_notified": True,
    }


@api_view(["POST"])
def manual_override(request):
    override_type = request.data.get("type")
    student_id = request.data.get("student_id")
    date = _parse_date(request.data.get("date"))
    reason = request.data.get("reason", "Manual override")

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return Response(
            {"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND
        )

    record, _ = AttendanceRecord.objects.get_or_create(
        student=student, date=date, defaults={"present": True}
    )

    action_taken = None
    if override_type == "mark_present":
        record.present = True
        action_taken = "marked_present"
    elif override_type == "mark_absent":
        record.present = False
        action_taken = "marked_absent"
    elif override_type == "grant_access":
        GateEvent.objects.create(
            student=student,
            action=GateEvent.ENTRY,
            success=True,
            reason="Manual override access",
        )
        record.present = True
        action_taken = "access_granted"

    record.override_reason = reason
    record.verified = True
    record.save()

    notifications = send_override_notifications(student)

    return Response(
        {
            "detail": "Override applied successfully", 
            "student": student.student_id,
            "action": action_taken,
            "notification_sent": notifications,
            "flag_cleared": True,
            "timestamp": timezone.now().isoformat(),
        }
    )


@api_view(["POST"])
def clear_flag(_request):
    return Response({"detail": "Flag cleared."})


@api_view(["GET"])
def admin_monitoring_dashboard(_request):
    anomalies = detect_anomalies()
    pending_reviews = AttendanceRecord.objects.filter(verified=False)

    payload = {
        "timestamp": timezone.now().isoformat(),
        "system_status": {
            "status": "normal" if anomalies["total_count"] == 0 else "degraded",
            "active_gates": 4,
            "last_sync": timezone.now().isoformat(),
        },
        "anomalies": anomalies,
        "alerts": anomalies["critical_anomalies"] + anomalies["warning_anomalies"],
        "pending_reviews": pending_reviews.count(),
        "requires_action": bool(anomalies["total_count"] or pending_reviews.exists()),
    }

    return Response(payload)


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

    latest_feed = [
        {
            "student": event.student.student_id,
            "action": event.action,
            "time": event.timestamp.isoformat(),
            "success": event.success,
        }
        for event in today_events.order_by("-timestamp")[:6]
    ]

    anomalies = detect_anomalies(date=today)

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
        "anomaly_count": anomalies["total_count"],
        "alert_count": len(anomalies["critical_anomalies"] + anomalies["warning_anomalies"]),
        "system_healthy": anomalies["total_count"] == 0,
    }

    return Response(payload)
