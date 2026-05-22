from django.urls import path
from .views import (
    register, forgot_password, login, logout,
    teacher_students, teacher_reset_password,
    teacher_notifications, resolve_notification
)

urlpatterns = [
    path('register/', register),
    path('login/', login),
    path('logout/', logout),
    path('forgot-password/', forgot_password),
    path('teacher/students/', teacher_students),
    path('teacher/reset-password/', teacher_reset_password),
    path('teacher/notifications/', teacher_notifications),
    path('teacher/notifications/resolve/', resolve_notification),
]
