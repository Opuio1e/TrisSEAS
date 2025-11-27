from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.attendance.models import AttendanceRecord
from apps.entry_gate.models import GateEvent
from apps.students.models import Student
from apps.users.models import User


class LiveStatsViewTests(TestCase):
    def setUp(self):
        self.student = self._create_student("S100", "student-one")
        self.second_student = self._create_student("S200", "student-two")

    def _create_student(self, student_id: str, username: str) -> Student:
        user = User.objects.create(
            username=username,
            first_name="First",
            last_name="Last",
            email=f"{username}@example.com",
        )
        return Student.objects.create(
            user=user,
            student_id=student_id,
            rfid_tag=f"RFID-{student_id}",
            parent_email="parent@example.com",
        )

    def test_live_stats_summarizes_recent_activity(self):
        now = timezone.now()
        today = timezone.localdate()

        recent_entry = GateEvent.objects.create(
            student=self.student,
            action=GateEvent.ENTRY,
            success=True,
        )
        GateEvent.objects.filter(pk=recent_entry.pk).update(
            timestamp=now - timedelta(hours=1)
        )

        recent_exit = GateEvent.objects.create(
            student=self.student,
            action=GateEvent.EXIT,
            success=False,
        )
        GateEvent.objects.filter(pk=recent_exit.pk).update(
            timestamp=now - timedelta(hours=2)
        )

        older_entry = GateEvent.objects.create(
            student=self.second_student,
            action=GateEvent.ENTRY,
            success=True,
        )
        GateEvent.objects.filter(pk=older_entry.pk).update(
            timestamp=now - timedelta(days=2)
        )

        AttendanceRecord.objects.create(
            student=self.student,
            date=today,
            present=True,
            first_entry_time=now - timedelta(hours=2),
        )
        AttendanceRecord.objects.create(
            student=self.second_student,
            date=today,
            present=False,
        )

        response = self.client.get(reverse("live-stats"))
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        per_gate_totals = {entry["action"]: entry["total"] for entry in payload["per_gate"]}

        self.assertEqual(payload["students"], 2)
        self.assertEqual(payload["events_24h"], 2)
        self.assertEqual(payload["events_today"], 2)
        self.assertEqual(payload["present_today"], 1)
        self.assertEqual(payload["success_rate"], 50.0)
        self.assertTrue(payload["has_events_today"])
        self.assertEqual(len(payload["live_feed"]), 2)
        self.assertEqual(per_gate_totals[GateEvent.ENTRY], 1)
        self.assertEqual(per_gate_totals[GateEvent.EXIT], 1)
