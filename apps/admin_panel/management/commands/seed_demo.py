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

        demo_accounts = [
            {
                "username": "admin@example.com",
                "email": "admin@example.com",
                "password": "AdminPass123",
                "first_name": "Admin",
                "last_name": "User",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
                "label": "admin",
            },
            {
                "username": "teacher@example.com",
                "email": "teacher@example.com",
                "password": "TeacherPass123",
                "first_name": "Taylor",
                "last_name": "Teacher",
                "role": "teacher",
                "is_staff": False,
                "is_superuser": False,
                "label": "teacher",
            },
            {
                "username": "student@example.com",
                "email": "student@example.com",
                "password": "StudentPass123",
                "first_name": "Sam",
                "last_name": "Student",
                "role": "student",
                "is_staff": False,
                "is_superuser": False,
                "label": "student",
            },
        ]

        demo_users = {}
        for account in demo_accounts:
            user, created_user = User.objects.get_or_create(
                username=account["username"],
                defaults={
                    "email": account["email"],
                    "first_name": account["first_name"],
                    "last_name": account["last_name"],
                    "role": account["role"],
                    "is_staff": account["is_staff"],
                    "is_superuser": account["is_superuser"],
                },
            )

            updated_fields = []
            for field in [
                "email",
                "first_name",
                "last_name",
                "role",
                "is_staff",
                "is_superuser",
            ]:
                if getattr(user, field) != account[field]:
                    setattr(user, field, account[field])
                    updated_fields.append(field)

            user.set_password(account["password"])
            updated_fields.append("password")
            if updated_fields:
                user.save(update_fields=updated_fields)

            demo_users[account["label"]] = user
            status_method = self.style.SUCCESS if created_user else self.style.WARNING
            self.stdout.write(
                status_method(
                    f"{account['label'].capitalize()} user ready (username/email: {account['email']}, password: {account['password']})."
                )
            )

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
            if idx == 1:
                user = demo_users.get("student")
            else:
                user, _ = User.objects.get_or_create(
                    username=student_id.lower(),
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
                        "role": "student",
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

        self.stdout.write(
            self.style.SUCCESS(
                "Demo dataset ready. Example logins: admin@example.com/AdminPass123, "
                "teacher@example.com/TeacherPass123, student@example.com/StudentPass123."
            )
        )
