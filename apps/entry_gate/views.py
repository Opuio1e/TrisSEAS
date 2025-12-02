from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attendance.models import AttendanceRecord
from apps.students.models import Student

from .models import GateEvent
from .serializers import GateEventSerializer
from .services import enroll_student_face, recognize_student_from_image


class EnrollView(APIView):
    """Enroll a student's face for biometric recognition."""

    def post(self, request):
        student_id = request.data.get("student_id")
        image = request.FILES.get("image")

        if not student_id or not image:
            return Response(
                {"detail": "student_id and image are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student = get_object_or_404(Student, id=student_id)

        try:
            enroll_student_face(student, image)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"detail": "Face enrolled successfully."})


class ScanView(APIView):
    """
    Process gate scan according to flowchart:
    1. Student approaches gate
    2. ID Card or Face Scan verification
    3. Validate match (>= 80% for face, exact for RFID)
    4. Grant or deny access
    5. Log entry time
    6. Send parent notification
    """

    def post(self, request):
        image = request.FILES.get("image")
        rfid_tag = request.data.get("rfid_tag")
        action = request.data.get("action", GateEvent.ENTRY)

        student = None
        verification_method = None
        success = False
        reason = ""

        if image:
            try:
                student = recognize_student_from_image(image)
                if student:
                    verification_method = "face_scan"
                    success = True
                    reason = "Biometric match"
            except Exception as exc:  # pragma: no cover - defensive
                reason = f"Face recognition error: {exc}"

        if not student and rfid_tag:
            try:
                student = Student.objects.get(rfid_tag=rfid_tag)
                verification_method = "rfid"
                success = True
                reason = "RFID validated"
            except Student.DoesNotExist:
                reason = "Invalid RFID tag"

        if not student:
            return Response(
                {
                    "detail": "No matching student found.",
                    "success": False,
                    "reason": reason or "No matching student found",
                    "action_required": "manual_check_in",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        event = GateEvent.objects.create(
            student=student,
            action=action,
            success=success,
            reason=reason,
        )

        today = timezone.localdate()
        attendance, _ = AttendanceRecord.objects.get_or_create(
            student=student, date=today, defaults={"present": True}
        )

        if action == GateEvent.ENTRY:
            if not attendance.first_entry_time:
                attendance.first_entry_time = event.timestamp
            attendance.present = True
        elif action == GateEvent.EXIT:
            attendance.last_exit_time = event.timestamp

        attendance.save()

        response_data = GateEventSerializer(event).data
        response_data["verification_method"] = verification_method
        response_data["attendance_updated"] = True

        return Response(response_data)


class RFIDScanView(APIView):
    """
    Dedicated RFID scan endpoint for card readers.
    Follows the ID Card branch of the flowchart.
    """

    def post(self, request):
        rfid_tag = request.data.get("rfid_tag")
        action = request.data.get("action", GateEvent.ENTRY)

        if not rfid_tag:
            return Response(
                {"detail": "rfid_tag is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            student = Student.objects.get(rfid_tag=rfid_tag)

            event = GateEvent.objects.create(
                student=student,
                action=action,
                success=True,
                reason="RFID validated",
            )

            today = timezone.localdate()
            attendance, _ = AttendanceRecord.objects.get_or_create(
                student=student, date=today, defaults={"present": True}
            )

            if action == GateEvent.ENTRY:
                if not attendance.first_entry_time:
                    attendance.first_entry_time = event.timestamp
                attendance.present = True
            elif action == GateEvent.EXIT:
                attendance.last_exit_time = event.timestamp

            attendance.save()

            response_data = GateEventSerializer(event).data
            response_data["verification_method"] = "rfid"
            response_data["attendance_updated"] = True

            return Response(response_data)

        except Student.DoesNotExist:
            return Response(
                {
                    "detail": "Invalid RFID tag.",
                    "success": False,
                    "reason": "RFID not found in system",
                    "action_required": "manual_check_in",
                },
                status=status.HTTP_404_NOT_FOUND,
            )


class ManualCheckInView(APIView):
    """
    Manual check-in for admin when automated verification fails.
    Follows the "Access Denied - Notify Admin" branch leading to
    "Student Directed to Manual Check-in"
    """

    def post(self, request):
        student_id = request.data.get("student_id")
        action = request.data.get("action", GateEvent.ENTRY)
        reason = request.data.get("reason", "Manual override")

        if not student_id:
            return Response(
                {"detail": "student_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            student = Student.objects.get(student_id=student_id)

            event = GateEvent.objects.create(
                student=student,
                action=action,
                success=True,
                reason=f"Manual check-in: {reason}",
            )

            today = timezone.localdate()
            attendance, _ = AttendanceRecord.objects.get_or_create(
                student=student, date=today, defaults={"present": True}
            )

            if action == GateEvent.ENTRY:
                if not attendance.first_entry_time:
                    attendance.first_entry_time = event.timestamp
                attendance.present = True
            elif action == GateEvent.EXIT:
                attendance.last_exit_time = event.timestamp

            attendance.override_reason = reason
            attendance.save()

            response_data = GateEventSerializer(event).data
            response_data["verification_method"] = "manual"
            response_data["attendance_updated"] = True

            return Response(response_data)

        except Student.DoesNotExist:
            return Response(
                {"detail": "Student not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
