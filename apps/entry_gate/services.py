from pathlib import Path

import numpy as np
import face_recognition
from django.conf import settings

from apps.students.models import Student

# folder to store face encodings
FACES_DIR = Path(settings.BASE_DIR) / "face_data"
FACES_DIR.mkdir(exist_ok=True)


def enroll_student_face(student: Student, image_file) -> None:
    """
    Takes an uploaded image file, extracts the face encoding and saves it
    as face_data/<student_pk>.npy
    """
    image = face_recognition.load_image_file(image_file)
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        raise ValueError("No face found in the image.")

    encoding = encodings[0]
    np.save(FACES_DIR / f"{student.pk}.npy", encoding)


def recognize_student_from_image(image_file):
    """
    Takes an uploaded image and tries to match it against saved encodings.
    Returns a Student instance or None.
    """
    image = face_recognition.load_image_file(image_file)
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        return None

    unknown_encoding = encodings[0]

    known_students = []
    known_encodings = []

    for student in Student.objects.all():
        path = FACES_DIR / f"{student.pk}.npy"
        if path.exists():
            known_students.append(student)
            known_encodings.append(np.load(path))

    if not known_encodings:
        return None

    matches = face_recognition.compare_faces(
        known_encodings, unknown_encoding, tolerance=0.5
    )

    if True not in matches:
        return None

    idx = matches.index(True)
    return known_students[idx]
