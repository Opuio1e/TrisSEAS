from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from apps.students.models import Student
from apps.students.serializers import StudentRegistrationSerializer
from apps.users.models import User


def generate_test_image(name="face.jpg"):
    file = BytesIO()
    image = Image.new("RGB", (10, 10), color="red")
    image.save(file, "JPEG")
    file.seek(0)
    return SimpleUploadedFile(name, file.read(), content_type="image/jpeg")


class StudentRegistrationSerializerTests(TestCase):
    def test_create_student_with_face_and_rfid(self):
        payload = {
            "student_id": "S001",
            "rfid_tag": "RFID-123",
            "parent_email": "parent@example.com",
            "face_image": generate_test_image(),
            "user": {
                "username": "jdoe",
                "first_name": "John",
                "last_name": "Doe",
                "email": "jdoe@example.com",
            },
        }

        with patch("apps.students.serializers.enroll_student_face") as enroll_mock:
            serializer = StudentRegistrationSerializer(data=payload)
            self.assertTrue(serializer.is_valid(), serializer.errors)

            student = serializer.save()

        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(student.student_id, "S001")
        enroll_mock.assert_called_once_with(student, payload["face_image"])

    def test_rfid_is_required_for_registration(self):
        payload = {
            "student_id": "S002",
            "parent_email": "parent@example.com",
            "face_image": generate_test_image("face2.jpg"),
            "user": {
                "username": "asmith",
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "asmith@example.com",
            },
        }

        serializer = StudentRegistrationSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("rfid_tag", serializer.errors)

    def test_face_image_is_required_for_registration(self):
        payload = {
            "student_id": "S003",
            "rfid_tag": "RFID-456",
            "parent_email": "parent@example.com",
            "user": {
                "username": "bwayne",
                "first_name": "Bruce",
                "last_name": "Wayne",
                "email": "bwayne@example.com",
            },
        }

        serializer = StudentRegistrationSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn("face_image", serializer.errors)
