from django.utils import timezone
from django.views.generic import TemplateView

from apps.entry_gate.models import GateEvent


class NotificationCenterView(TemplateView):
    template_name = "notifications.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        events = GateEvent.objects.select_related("student", "student__user").order_by("-timestamp")[:12]
        notifications = []

        for event in events:
            hour = timezone.localtime(event.timestamp).hour
            severity = "info"
            title = "Entry confirmed" if event.action == GateEvent.ENTRY else "Exit recorded"
            if not event.success:
                severity = "error"
                title = "Gate blocked"
            elif hour >= 19 or hour < 6:
                severity = "warning"
                title = "After-hours activity"

            notifications.append(
                {
                    "id": event.id,
                    "title": title,
                    "severity": severity,
                    "student_id": event.student.student_id,
                    "name": event.student.user.get_full_name(),
                    "timestamp": event.timestamp,
                    "message": event.reason or "Logged from smart gate sensor.",
                }
            )

        context.update(
            notifications=notifications,
            has_activity=bool(events),
        )
        return context
