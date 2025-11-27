from django.db import models
from apps.students.models import Student

class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    first_entry_time = models.DateTimeField(null=True, blank=True)
    last_exit_time = models.DateTimeField(null=True, blank=True)
    present = models.BooleanField(default=False)

    class Meta:
        unique_together = ("student", "date")
