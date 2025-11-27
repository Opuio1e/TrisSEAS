from datetime import timedelta

from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.attendance.models import AttendanceRecord
from apps.entry_gate.models import GateEvent
from apps.students.models import Student


class GateConsoleView(TemplateView):
    template_name = "gate_console.html"


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["snapshot"] = _build_snapshot()
        return context


def _build_snapshot():
    today = timezone.localdate()

    total_students = Student.objects.count()
    total_events = GateEvent.objects.count()
    today_events = GateEvent.objects.filter(timestamp__date=today)
    entries_today = today_events.filter(action=GateEvent.ENTRY).count()
    exits_today = today_events.filter(action=GateEvent.EXIT).count()

    present_records = AttendanceRecord.objects.filter(date=today, present=True).count()
    attendance_rate = 0
    if total_students:
        attendance_rate = round((present_records / total_students) * 100, 1)

    recent_events = (
        GateEvent.objects.select_related("student", "student__user")
        .order_by("-timestamp")[:5]
    )

    return {
        "today": today.isoformat(),
        "total_students": total_students,
        "total_events": total_events,
        "entries_today": entries_today,
        "exits_today": exits_today,
        "present_records": present_records,
        "attendance_rate": attendance_rate,
        "recent_events": [
            {
                "student_id": event.student.student_id,
                "name": event.student.user.get_full_name(),
                "action": event.action,
                "timestamp": event.timestamp.isoformat(),
            }
            for event in recent_events
        ],
    }


class AdminPanelView(TemplateView):
    template_name = "admin_panel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        snapshot = _build_snapshot()

        weekly_events = (
            GateEvent.objects.filter(timestamp__date__gte=timezone.localdate() - timedelta(days=7))
            .values("action")
            .annotate(count=Count("id"))
        )
        context.update(
            snapshot=snapshot,
            weekly_events=list(weekly_events),
        )
        return context


class LiveSnapshotView(View):
    def get(self, request):
        return JsonResponse(_build_snapshot())
