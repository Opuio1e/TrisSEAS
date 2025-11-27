from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import GateEvent
from apps.students.models import Student
from apps.students.face import FaceRecognition  # adjust if different path
from .serializers import GateEventSerializer

face = FaceRecognition()

class EnrollView(APIView):
    def post(self, request):
        student_id = request.data.get("student_id")
        image = request.FILES.get("image")

        if not student_id or not image:
            return Response(
                {"detail": "student_id and image are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        student = get_object_or_404(Student, id=student_id)

        # Enroll
        face.enroll(student_id, image)

        return Response({"detail": "Face enrolled successfully."})


class ScanView(APIView):
    def post(self, request):
        image = request.FILES.get("image")
        action = request.data.get("action")

        if not image:
            return Response({"detail": "image is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        student_id = face.identify(image)

        if student_id is None:
            return Response(
                {"detail": "No matching student found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        student = Student.objects.get(id=student_id)

        event = GateEvent.objects.create(
            student=student,
            action=action or "entry",
            success=True
        )

        return Response(GateEventSerializer(event).data)
