from django.db import models
from apps.students.models import Student

class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    first_entry_time = models.DateTimeField(null=True, blank=True)
    last_exit_time = models.DateTimeField(null=True, blank=True)
    present = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True)
    override_reason = models.TextField(blank=True)
    approved = models.BooleanField(default=False)
    approval_timestamp = models.DateTimeField(null=True, blank=True)
    approved_by = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("student", "date")
