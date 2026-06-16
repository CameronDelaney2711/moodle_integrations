import logging
import random
import string
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import PasswordResetRequest, UserProfile, ActivationCode, StudentRegistrationRequest
from .services.moodle_service import (
    create_user, trigger_password_reset, login_user,
    get_user_details, get_teacher_students, reset_student_password,
    get_student_teacher, verify_teacher_token, get_user_role,
    get_all_courses, get_all_teachers, get_all_students,
    create_moodle_user, enrol_student_in_course
)
logger = logging.getLogger(__name__)


def get_token_from_request(request):
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return None


def require_role(*allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            token = get_token_from_request(request)
            if not token:
                return Response({"error": "Authentication required."}, status=401)
            try:
                profile = UserProfile.objects.get(token=token)
            except UserProfile.DoesNotExist:
                return Response({"error": "Invalid token."}, status=401)
            if profile.role not in allowed_roles:
                return Response({"error": "Forbidden."}, status=403)
            request.user_profile = profile
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

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
    user_id = user_info.get("id")
    role = get_user_role(user_id)

    UserProfile.objects.update_or_create(
        moodle_user_id=user_id,
        defaults={
            "username": user_info.get("username"),
            "role": role,
            "token": token,
            "token_created_at": timezone.now(),
        }
    )

    return Response({
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": user_id,
            "username": user_info.get("username"),
            "firstname": user_info.get("firstname"),
            "lastname": user_info.get("lastname"),
            "email": user_info.get("email"),
            "role": role,
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
@require_role("teacher", "admin")
def teacher_students(request):
    teacher_id = request.query_params.get("teacher_id")
    if not teacher_id:
        return Response({"error": "teacher_id is required."}, status=400)
    students = get_teacher_students(teacher_id)
    return Response({"students": students}, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
@require_role("teacher", "admin")
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
@require_role("teacher", "admin")
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
@require_role("teacher", "admin")
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

@api_view(["GET"])
@permission_classes([AllowAny])
@require_role("admin")
def admin_overview(request):
    courses = get_all_courses()
    teachers = get_all_teachers()
    students = get_all_students()

    return Response({
        "total_courses": len(courses),
        "total_teachers": len(teachers),
        "total_students": len(students),
    }, status=200)

@api_view(["GET"])
@permission_classes([AllowAny])
@require_role("admin")
def admin_teachers(request):
    teachers = get_all_teachers()
    return Response({"teachers": teachers}, status=200)

@api_view(["POST"])
@permission_classes([AllowAny])
@require_role("admin")
def admin_create_student(request):
    username  = request.data.get("username", "").strip()
    firstname = request.data.get("firstname", "").strip()
    lastname  = request.data.get("lastname", "").strip()
    email     = request.data.get("email", "").strip()

    if not all([username, firstname, lastname, email]):
        return Response({"error": "All fields are required."}, status=400)

    if ActivationCode.objects.filter(username=username).exists():
        return Response({"error": "A student with this username already exists."}, status=400)

    result = create_moodle_user(username, firstname, lastname, email)
    if not result.get("success"):
        return Response({"error": result.get("error", "Failed to create student.")}, status=500)

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    ActivationCode.objects.create(username=username, code=code)

    return Response({
        "message": "Student created successfully.",
        "username": username,
        "activation_code": code,
    }, status=201)


@api_view(["POST"])
@permission_classes([AllowAny])
@require_role("admin")
def admin_enrol_student(request):
    username  = request.data.get("username", "").strip()
    course_id = request.data.get("course_id")

    if not username or not course_id:
        return Response({"error": "username and course_id are required."}, status=400)

    user_info = get_user_details(username)
    if not user_info or not user_info.get("id"):
        return Response({"error": "Student not found in Moodle."}, status=404)

    result = enrol_student_in_course(user_info.get("id"), course_id)
    if not result.get("success"):
        return Response({"error": result.get("error", "Enrolment failed.")}, status=500)

    return Response({"message": f"{username} enrolled successfully."}, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
def activate_account(request):
    username = request.data.get("username", "").strip()
    code     = request.data.get("code", "").strip().upper()
    password = request.data.get("password", "").strip()

    if not all([username, code, password]):
        return Response({"error": "Username, activation code, and password are required."}, status=400)

    if len(password) < 8:
        return Response({"error": "Password must be at least 8 characters."}, status=400)

    try:
        activation = ActivationCode.objects.get(username=username, code=code)
    except ActivationCode.DoesNotExist:
        return Response({"error": "Invalid username or activation code."}, status=400)

    if activation.used:
        return Response({"error": "This activation code has already been used."}, status=400)

    user_info = get_user_details(username)
    if not user_info or not user_info.get("id"):
        return Response({"error": "Student account not found."}, status=404)

    result = reset_student_password(user_info.get("id"), password)
    if not result.get("success"):
        return Response({"error": result.get("error", "Failed to set password.")}, status=500)

    activation.used = True
    activation.used_at = timezone.now()
    activation.save()

    return Response({"message": "Account activated successfully. You can now log in."}, status=200)

@api_view(["POST"])
@permission_classes([AllowAny])
def register_request(request):
    firstname = request.data.get("firstname", "").strip()
    lastname  = request.data.get("lastname", "").strip()
    email     = request.data.get("email", "").strip()

    if not all([firstname, lastname, email]):
        return Response({"error": "All fields are required."}, status=400)

    if StudentRegistrationRequest.objects.filter(email=email).exists():
        return Response({"error": "A request with this email already exists."}, status=400)

    StudentRegistrationRequest.objects.create(
        firstname=firstname,
        lastname=lastname,
        email=email,
    )
    return Response({"message": "Registration request submitted. Your school admin will be in touch."}, status=201)


@api_view(["GET"])
@permission_classes([AllowAny])
@require_role("admin")
def admin_registration_requests(request):
    status_filter = request.query_params.get("status", "pending")
    requests_qs = StudentRegistrationRequest.objects.filter(status=status_filter)
    data = [{
        "id": r.id,
        "firstname": r.firstname,
        "lastname": r.lastname,
        "email": r.email,
        "status": r.status,
        "requested_at": r.requested_at.strftime("%d %b %Y, %H:%M"),
    } for r in requests_qs]
    return Response({"requests": data, "count": len(data)}, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
@require_role("admin")
def admin_approve_student(request):
    request_id = request.data.get("request_id")
    username   = request.data.get("username", "").strip()

    if not request_id or not username:
        return Response({"error": "request_id and username are required."}, status=400)

    try:
        reg = StudentRegistrationRequest.objects.get(id=request_id, status="pending")
    except StudentRegistrationRequest.DoesNotExist:
        return Response({"error": "Registration request not found or already resolved."}, status=404)

    if ActivationCode.objects.filter(username=username).exists():
        return Response({"error": "A student with this username already exists."}, status=400)

    result = create_moodle_user(username, reg.firstname, reg.lastname, reg.email)
    if not result.get("success"):
        return Response({"error": result.get("error", "Failed to create student.")}, status=500)

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    ActivationCode.objects.create(username=username, code=code)

    reg.status = "approved"
    reg.resolved_at = timezone.now()
    reg.save()

    return Response({
        "message": "Student approved and account created.",
        "username": username,
        "activation_code": code,
    }, status=201)


@api_view(["POST"])
@permission_classes([AllowAny])
@require_role("admin")
def admin_reject_student(request):
    request_id = request.data.get("request_id")

    if not request_id:
        return Response({"error": "request_id is required."}, status=400)

    try:
        reg = StudentRegistrationRequest.objects.get(id=request_id, status="pending")
    except StudentRegistrationRequest.DoesNotExist:
        return Response({"error": "Registration request not found or already resolved."}, status=404)

    reg.status = "rejected"
    reg.resolved_at = timezone.now()
    reg.save()

    return Response({"message": "Registration request rejected."}, status=200)

@api_view(["GET"])
@permission_classes([AllowAny])
@require_role("admin")
def admin_courses(request):
    courses = get_all_courses()
    data = [{"id": c.get("id"), "name": c.get("fullname")} for c in courses]
    return Response({"courses": data}, status=200)
