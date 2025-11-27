from rest_framework import serializers

from apps.entry_gate.services import enroll_student_face
from apps.users.models import User
from .models import Student


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    face_image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Student
        fields = [
            "id",
            "student_id",
            "rfid_tag",
            "parent_email",
            "face_image",
            "user",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)

        # Enforce RFID availability when creating new students so scanners can be used
        # immediately after registration.
        if self.instance is None and not attrs.get("rfid_tag"):
            raise serializers.ValidationError(
                {"rfid_tag": "RFID tag is required for registration."}
            )

        return attrs

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        face_image = validated_data.pop("face_image", None)

        user = User.objects.create(**user_data)
        student = Student.objects.create(user=user, **validated_data)

        if face_image:
            try:
                enroll_student_face(student, face_image)
            except ValueError as exc:
                raise serializers.ValidationError({"face_image": str(exc)}) from exc

        return student


class StudentRegistrationSerializer(StudentSerializer):
    face_image = serializers.ImageField(write_only=True, required=True)
    rfid_tag = serializers.CharField(required=True, allow_blank=False)

    class Meta(StudentSerializer.Meta):
        fields = StudentSerializer.Meta.fields

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if attrs.get("face_image") is None:
            raise serializers.ValidationError(
                {"face_image": "A face capture is required for registration."}
            )

        return attrs
