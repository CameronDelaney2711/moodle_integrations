from django.urls import path
from .views import (
    register, forgot_password, login, logout,
    teacher_students, teacher_reset_password,
    teacher_notifications, resolve_notification,
    admin_overview, admin_teachers,
    admin_create_student, admin_enrol_student,
    admin_registration_requests, admin_approve_student, admin_reject_student,
    activate_account, register_request
)
urlpatterns = [
    path('register/', register),
    path('login/', login),
    path('logout/', logout),
    path('forgot-password/', forgot_password),
    path('activate/', activate_account),
    path('register-request/', register_request),
    path('teacher/students/', teacher_students),
    path('teacher/reset-password/', teacher_reset_password),
    path('teacher/notifications/', teacher_notifications),
    path('teacher/notifications/resolve/', resolve_notification),
    path('admin/overview/', admin_overview),
    path('admin/teachers/', admin_teachers),
    path('admin/create-student/', admin_create_student),
    path('admin/enrol-student/', admin_enrol_student),
    path('admin/registration-requests/', admin_registration_requests),
    path('admin/approve-student/', admin_approve_student),
    path('admin/reject-student/', admin_reject_student),
]
