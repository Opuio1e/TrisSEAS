"""Lightweight placeholder face recognition utility.

This stub keeps an in-memory mapping of enrolled student IDs and returns the
first available ID when identifying. It allows the API to operate in
development environments without external dependencies.
"""

from typing import Optional


class FaceRecognition:
    def __init__(self):
        self.registry: list[str] = []

    def enroll(self, student_id: str, image) -> None:
        if student_id not in self.registry:
            self.registry.append(student_id)

    def identify(self, image) -> Optional[str]:
        return self.registry[0] if self.registry else None
