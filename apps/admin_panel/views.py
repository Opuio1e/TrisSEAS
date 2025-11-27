from django.views.generic import TemplateView


class GateConsoleView(TemplateView):
    template_name = "gate_console.html"
