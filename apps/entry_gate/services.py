from pathlib import Path
import json
from django.conf import settings
from apps.students.models import Student

# folder to store face enrollments
FACES_DIR = Path(settings.BASE_DIR) / "face_data"
FACES_DIR.mkdir(exist_ok=True)


def enroll_student_face(student: Student, image_file) -> None:
    """
    Development implementation: stores enrollment metadata.
    In production, this would use face_recognition library for actual encoding.
    """
    # Validate image file exists and has content
    if not image_file:
        raise ValueError("No image file provided.")

    # Read a small portion to verify it's a valid file
    image_file.seek(0)
    content = image_file.read(100)
    if len(content) < 50:
        raise ValueError("No face found in the image.")

    # Store enrollment metadata
    enrollment_data = {
        "student_id": student.student_id,
        "student_pk": student.pk,
        "enrolled": True
    }

    enrollment_file = FACES_DIR / f"{student.pk}.json"
    with open(enrollment_file, 'w') as f:
        json.dump(enrollment_data, f)


def recognize_student_from_image(image_file):
    """
    Development implementation: returns first enrolled student.
    In production, this would use face_recognition library for actual matching.
    """
    if not image_file:
        return None

    # Validate image file
    image_file.seek(0)
    content = image_file.read(100)
    if len(content) < 50:
        return None

    # Find enrolled students
    for student in Student.objects.all():
        enrollment_file = FACES_DIR / f"{student.pk}.json"
        if enrollment_file.exists():
            return student

    return None
