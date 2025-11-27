from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import GateEvent
from apps.students.models import Student
from .serializers import GateEventSerializer
from .services import enroll_student_face, recognize_student_from_image

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

        try:
            enroll_student_face(student, image)
        except ValueError as exc:  # raised when no face is detected
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"detail": "Face enrolled successfully."})


class ScanView(APIView):
    def post(self, request):
        image = request.FILES.get("image")
        action = request.data.get("action", GateEvent.ENTRY)

        if not image:
            return Response({"detail": "image is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        valid_actions = {choice[0] for choice in GateEvent.ACTION_CHOICES}
        if action not in valid_actions:
            return Response(
                {"detail": f"Invalid action. Use one of: {', '.join(valid_actions)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = recognize_student_from_image(image)

        if student is None:
            return Response(
                {"detail": "No matching student found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        event = GateEvent.objects.create(
            student=student,
            action=action or "entry",
            success=True
        )

        return Response(GateEventSerializer(event).data)
