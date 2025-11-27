from datetime import timedelta
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.attendance.models import AttendanceRecord
from apps.entry_gate.models import GateEvent
from apps.students.models import Student


class Command(BaseCommand):
    help = "Create a demo-ready dataset with sample users, students, attendance, and gate events."

    def handle(self, *args, **options):
        User = get_user_model()

        admin_user, created_admin = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created_admin:
            admin_user.set_password("admin")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user (admin/admin)."))
        else:
            self.stdout.write(self.style.WARNING("Admin user already exists; leaving credentials unchanged."))

        roster = [
            ("STU-1001", "Taylor", "Reed", "1001-0001"),
            ("STU-1002", "Morgan", "Lee", "1002-0002"),
            ("STU-1003", "Avery", "Patel", "1003-0003"),
            ("STU-1004", "Jordan", "Kim", "1004-0004"),
            ("STU-1005", "Charlie", "Ramirez", "1005-0005"),
            ("STU-1006", "Riley", "Singh", "1006-0006"),
        ]

        students = []
        for idx, (student_id, first_name, last_name, rfid_tag) in enumerate(roster, start=1):
            user, _ = User.objects.get_or_create(
                username=student_id.lower(),
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
                },
            )

            student, created_student = Student.objects.get_or_create(
                student_id=student_id,
                defaults={
                    "user": user,
                    "rfid_tag": rfid_tag,
                    "parent_email": f"parent+{student_id.lower()}@example.com",
                },
            )

            if not created_student:
                student.rfid_tag = rfid_tag
                student.parent_email = f"parent+{student_id.lower()}@example.com"
                student.user = user
                student.save(update_fields=["rfid_tag", "parent_email", "user"])

            students.append(student)

        if students:
            self.stdout.write(self.style.SUCCESS(f"Provisioned {len(students)} demo students."))
        else:
            self.stdout.write(self.style.WARNING("No students were created."))

        today = timezone.localdate()
        now = timezone.now()

        if AttendanceRecord.objects.filter(date=today).exists():
            self.stdout.write(self.style.WARNING("Attendance records already exist for today; leaving them intact."))
        else:
            for offset, student in enumerate(students):
                entry_time = now.replace(hour=7, minute=30, second=0, microsecond=0) + timedelta(
                    minutes=offset * 7
                )
                exit_time = entry_time + timedelta(hours=8, minutes=random.randint(-20, 35))

                AttendanceRecord.objects.create(
                    student=student,
                    date=today,
                    first_entry_time=entry_time,
                    last_exit_time=exit_time,
                    present=True,
                )
            self.stdout.write(self.style.SUCCESS("Seeded attendance records for today."))

        if GateEvent.objects.filter(timestamp__date=today).exists():
            self.stdout.write(self.style.WARNING("Gate events already exist for today; leaving them intact."))
        else:
            for offset, student in enumerate(students):
                base_time = now - timedelta(hours=4, minutes=offset * 5)
                entry_event = GateEvent.objects.create(
                    student=student,
                    action=GateEvent.ENTRY,
                    timestamp=base_time,
                    success=True,
                    reason="Biometric match",
                )

                exit_event = GateEvent.objects.create(
                    student=student,
                    action=GateEvent.EXIT,
                    timestamp=base_time + timedelta(hours=8, minutes=random.randint(-15, 20)),
                    success=random.choice([True, True, True, False]),
                    reason="",
                )

                self.stdout.write(
                    self.style.NOTICE(
                        f"Logged {entry_event.action}/{exit_event.action} events for {student.student_id}."
                    )
                )

            self.stdout.write(self.style.SUCCESS("Demo gate activity created for the last 24 hours."))

        self.stdout.write(self.style.SUCCESS("Demo dataset ready. Log in at /admin with admin/admin."))
