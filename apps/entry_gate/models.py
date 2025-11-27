from django.db import models
from apps.students.models import Student


class GateEvent(models.Model):
    ENTRY = "entry"
    EXIT = "exit"
    ACTION_CHOICES = [
        (ENTRY, "Entry"),
        (EXIT, "Exit"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    reason = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.student.student_id} {self.action} @ {self.timestamp}"
