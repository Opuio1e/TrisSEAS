from datetime import timedelta

from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.attendance.models import AttendanceRecord
from apps.entry_gate.models import GateEvent
from apps.students.models import Student


class GateConsoleView(LoginRequiredMixin, TemplateView):
    template_name = "gate_console.html"


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "admin_dashboard.html"


class AnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = "analytics.html"


class NotificationsView(LoginRequiredMixin, TemplateView):
    template_name = "notifications.html"


class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "student_dashboard.html"


class ParentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "parent_dashboard.html"


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

    payload = {
        "students": Student.objects.count(),
        "active_gates": 4,
        "events_24h": recent_events.count(),
        "events_today": total_events,
        "success_rate": success_rate,
        "present_today": AttendanceRecord.objects.filter(
            date=today, present=True
        ).count(),
        "average_scan_time": 1.2,
        "live_feed": latest_feed,
        "last_updated": now.isoformat(),
        "has_events_today": bool(total_events),
        "per_gate": list(
            today_events.values("action").annotate(total=Count("id")).order_by("action")
        ),
    }

    return JsonResponse(payload)
