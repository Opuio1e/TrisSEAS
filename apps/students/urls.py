from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentRegistrationView, StudentViewSet

router = DefaultRouter()
router.register(r"", StudentViewSet, basename="students")

urlpatterns = [
    path("register/", StudentRegistrationView.as_view(), name="student-register"),
    path("", include(router.urls)),
]
