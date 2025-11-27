from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework.test import APITestCase

from apps.entry_gate.models import GateEvent
from apps.students.models import Student
from apps.users.models import User


def build_image(name="face.jpg"):
    buffer = BytesIO()
    image = Image.new("RGB", (12, 12), color="blue")
    image.save(buffer, "JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")


class EntryGateApiTests(APITestCase):
    def setUp(self):
        user = User.objects.create(
            username="gate-user",
            first_name="Gate",
            last_name="User",
            email="gate@example.com",
        )
        self.student = Student.objects.create(
            user=user,
            student_id="S500",
            rfid_tag="RFID-S500",
            parent_email="parent@example.com",
        )

    @patch("apps.entry_gate.views.recognize_student_from_image")
    @patch("apps.entry_gate.views.enroll_student_face")
    def test_enroll_and_scan_flow(self, mock_enroll, mock_recognize):
        mock_recognize.return_value = self.student

        enroll_response = self.client.post(
            reverse("enroll"),
            {"student_id": self.student.id, "image": build_image()},
            format="multipart",
        )

        self.assertEqual(enroll_response.status_code, 200)
        self.assertEqual(enroll_response.json()["detail"], "Face enrolled successfully.")
        mock_enroll.assert_called_once()
        called_student, called_image = mock_enroll.call_args[0]
        self.assertEqual(called_student, self.student)
        self.assertTrue(hasattr(called_image, "read"))

        scan_response = self.client.post(
            reverse("scan"),
            {"image": build_image("scan.jpg"), "action": GateEvent.ENTRY},
            format="multipart",
        )

        self.assertEqual(scan_response.status_code, 200)

        payload = scan_response.json()
        self.assertEqual(payload["action"], GateEvent.ENTRY)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["student"]["student_id"], self.student.student_id)
        self.assertEqual(GateEvent.objects.count(), 1)

        event = GateEvent.objects.first()
        self.assertEqual(event.student, self.student)
        self.assertEqual(event.action, GateEvent.ENTRY)

    @patch("apps.entry_gate.views.recognize_student_from_image")
    def test_scan_without_match_returns_not_found(self, mock_recognize):
        mock_recognize.return_value = None

        response = self.client.post(
            reverse("scan"),
            {"image": build_image("unknown.jpg")},
            format="multipart",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"], "No matching student found."
        )
        self.assertEqual(GateEvent.objects.count(), 0)
