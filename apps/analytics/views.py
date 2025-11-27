from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncHour
from django.utils import timezone
from django.views.generic import TemplateView

from apps.attendance.models import AttendanceRecord
from apps.entry_gate.models import GateEvent
from apps.students.models import Student


class AnalyticsView(TemplateView):
    template_name = "analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        this_week_start = today - timedelta(days=6)

        total_students = Student.objects.count()
        attendance_today = AttendanceRecord.objects.filter(date=today)
        present_today = attendance_today.filter(present=True).count()
        attendance_rate = 0
        if total_students:
            attendance_rate = round((present_today / total_students) * 100, 1)

        weekly_events = (
            GateEvent.objects.filter(timestamp__date__gte=this_week_start)
            .values("action")
            .annotate(count=Count("id"))
        )

        hourly_activity = (
            GateEvent.objects.filter(timestamp__date=today)
            .annotate(hour=TruncHour("timestamp"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )

        top_students = (
            GateEvent.objects.filter(timestamp__date__gte=this_week_start)
            .values("student__student_id", "student__user__first_name", "student__user__last_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        context.update(
            today=today,
            total_students=total_students,
            present_today=present_today,
            attendance_rate=attendance_rate,
            weekly_events=list(weekly_events),
            hourly_activity=list(hourly_activity),
            top_students=list(top_students),
        )
        return context
