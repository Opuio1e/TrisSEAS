from rest_framework import serializers
from .models import GateEvent
from apps.students.serializers import StudentSerializer


class GateEventSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)

    class Meta:
        model = GateEvent
        fields = ["id", "student", "action", "timestamp", "success", "reason"]
