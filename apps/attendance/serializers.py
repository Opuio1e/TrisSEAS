from rest_framework import serializers
from .models import AttendanceRecord
from apps.students.serializers import StudentSerializer


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = "__all__"
