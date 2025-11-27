from rest_framework import status, viewsets
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Student
from .serializers import StudentRegistrationSerializer, StudentSerializer


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer


class StudentRegistrationView(APIView):
    """Register a student with RFID metadata and a face capture."""

    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.save()

        return Response(
            StudentSerializer(student).data, status=status.HTTP_201_CREATED
        )
