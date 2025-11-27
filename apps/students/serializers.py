from rest_framework import serializers
from .models import Student
from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Student
        fields = ["id", "student_id", "rfid_tag", "parent_email", "user"]

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user = User.objects.create(**user_data)
        student = Student.objects.create(user=user, **validated_data)
        return student
