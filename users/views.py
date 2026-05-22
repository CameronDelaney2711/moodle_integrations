import logging
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import PasswordResetRequest
from .services.moodle_service import (
    create_user, trigger_password_reset, login_user,
    get_user_details, get_teacher_students, reset_student_password,
    get_student_teacher, verify_teacher_token
)

logger = logging.getLogger(__name__)


def get_token_from_request(request):
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return None


def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        token = get_token_from_request(request)
        if not token:
            return Response({"error": "Authentication required."}, status=401)
        if len(token) != 32 or not token.isalnum():
            return Response({"error": "Invalid token."}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username  = request.data.get("username", "").strip()
    password  = request.data.get("password", "")
    email     = request.data.get("email", "").strip()
    firstname = request.data.get("firstname", "").strip()
    lastname  = request.data.get("lastname", "").strip()

    if not all([username, password, email, firstname, lastname]):
        return Response({"error": "All fields are required."}, status=400)

    result = create_user(username, password, email, firstname, lastname)

    if "exception" in result:
        return Response({"error": result.get("message", "Registration failed.")}, status=400)

    return Response({"username": username, "email": email}, status=201)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or not password:
        return Response({"error": "Username and password are required."}, status=400)

    result = login_user(username, password)

    if "token" not in result:
        error_code = result.get("errorcode", "unknown")
        if error_code in ("invalidlogin", "unknownuser"):
            return Response({"error": "Invalid username or password."}, status=401)
        return Response(
            {"error": result.get("error", "Login failed."), "errorcode": error_code},
            status=503 if "service" in error_code else 401,
        )

    token = result["token"]
    user_info = get_user_details(username)

    return Response({
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": user_info.get("id"),
            "username": user_info.get("username"),
            "firstname": user_info.get("firstname"),
            "lastname": user_info.get("lastname"),
            "email": user_info.get("email"),
        }
    }, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
def logout(request):
    token = request.data.get("token", "").strip()
    if not token:
        return Response({"error": "Token is required."}, status=400)
    return Response({"message": "Logged out successfully."}, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    username = request.data.get("username", "").strip()

    if not username:
        return Response({"error": "Username is required."}, status=400)

    user_info = get_user_details(username)
    if not user_info or not user_info.get("id"):
        return Response({"message": "If the account exists, your teacher has been notified."}, status=200)

    student_id   = user_info.get("id")
    student_name = f"{user_info.get('firstname', '')} {user_info.get('lastname', '')}".strip()

    teacher_id = get_student_teacher(student_id)
    if not teacher_id:
        return Response({"message": "If the account exists, your teacher has been notified."}, status=200)

    existing = PasswordResetRequest.objects.filter(
        student_id=student_id,
        resolved=False
    ).first()

    if not existing:
        PasswordResetRequest.objects.create(
            student_id=student_id,
            student_username=username,
            student_name=student_name,
            teacher_id=teacher_id,
        )

    return Response({"message": "If the account exists, your teacher has been notified."}, status=200)


@api_view(["GET"])
@permission_classes([AllowAny])
@teacher_required
def teacher_students(request):
    teacher_id = request.query_params.get("teacher_id")
    if not teacher_id:
        return Response({"error": "teacher_id is required."}, status=400)
    students = get_teacher_students(teacher_id)
    return Response({"students": students}, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
@teacher_required
def teacher_reset_password(request):
    student_id   = request.data.get("student_id")
    new_password = request.data.get("new_password", "").strip()
    if not student_id or not new_password:
        return Response({"error": "student_id and new_password are required."}, status=400)
    if len(new_password) < 8:
        return Response({"error": "Password must be at least 8 characters."}, status=400)
    result = reset_student_password(student_id, new_password)
    if not result.get("success"):
        return Response({"error": result.get("error", "Reset failed.")}, status=500)
    return Response({"message": "Password reset successfully."}, status=200)


@api_view(["GET"])
@permission_classes([AllowAny])
@teacher_required
def teacher_notifications(request):
    teacher_id = request.query_params.get("teacher_id")
    if not teacher_id:
        return Response({"error": "teacher_id is required."}, status=400)
    requests_qs = PasswordResetRequest.objects.filter(
        teacher_id=teacher_id,
        resolved=False
    )
    data = [{
        "id": r.id,
        "student_id": r.student_id,
        "student_username": r.student_username,
        "student_name": r.student_name,
        "requested_at": r.requested_at.strftime("%d %b %Y, %H:%M"),
    } for r in requests_qs]
    return Response({"notifications": data, "count": len(data)}, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
@teacher_required
def resolve_notification(request):
    notification_id = request.data.get("notification_id")
    if not notification_id:
        return Response({"error": "notification_id is required."}, status=400)
    try:
        reset_request = PasswordResetRequest.objects.get(id=notification_id, resolved=False)
        reset_request.resolved = True
        reset_request.resolved_at = timezone.now()
        reset_request.save()
        return Response({"message": "Notification resolved."}, status=200)
    except PasswordResetRequest.DoesNotExist:
        return Response({"error": "Notification not found."}, status=404)
