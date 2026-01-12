import os
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from django.core.management import execute_from_command_line

settings.configure(
    DEBUG=True,
    SECRET_KEY="secret-key",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
    MIDDLEWARE=[
        '__main__.RequestLoggingMiddleware',
    ],
)

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR")
        method = request.method
        path = request.path
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[{time}] IP: {ip} | Method: {method} | API: {path}")

        response = self.get_response(request)

        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response

def home(request):
    return JsonResponse({"message": "Home API"})

def login(request):
    return JsonResponse({"message": "Login API"})

def dashboard(request):
    return JsonResponse({"message": "Dashboard API"})

urlpatterns = [
    path("", home),
    path("login/", login),
    path("dashboard/", dashboard),
]

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "__main__")
    execute_from_command_line(["manage.py", "runserver"])
