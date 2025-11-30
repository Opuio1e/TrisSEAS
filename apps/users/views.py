from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


class RoleBasedLoginView(LoginView):
    template_name = "login.html"
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to

        role = (getattr(self.request.user, "role", "") or "").lower()
        role_paths = {
            "admin": reverse_lazy("admin-dashboard"),
            "teacher": reverse_lazy("analytics"),
            "student": reverse_lazy("student-dashboard"),
            "parent": reverse_lazy("parent-dashboard"),
        }

        return role_paths.get(role, reverse_lazy("analytics"))
