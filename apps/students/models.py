from django.db import models
from django.conf import settings

class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    student_id = models.CharField(max_length=20, unique=True)
    rfid_tag = models.CharField(max_length=64, unique=True, null=True, blank=True)
    parent_email = models.EmailField()

    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name()}"
