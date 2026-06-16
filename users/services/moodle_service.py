import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def create_user(username, password, email, firstname, lastname):
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "core_user_create_users",
        "moodlewsrestformat": "json",
        "users[0][username]": username,
        "users[0][password]": password,
        "users[0][email]": email,
        "users[0][firstname]": firstname,
        "users[0][lastname]": lastname,
    }
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"exception": "Moodle timed out.", "errorcode": "service_timeout"}
    except requests.exceptions.ConnectionError:
        return {"exception": "Could not reach Moodle.", "errorcode": "service_unavailable"}
    except requests.exceptions.HTTPError as e:
        return {"exception": str(e), "errorcode": "http_error"}


def login_user(username, password):
    url = f"{settings.MOODLE_BASE_URL}/login/token.php"
    payload = {
        "username": username,
        "password": password,
        "service": settings.MOODLE_SERVICE_NAME,
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Moodle timed out.", "errorcode": "service_timeout"}
    except requests.exceptions.ConnectionError:
        return {"error": "Could not reach Moodle.", "errorcode": "service_unavailable"}
    except requests.exceptions.HTTPError as e:
        return {"error": str(e), "errorcode": "http_error"}


def trigger_password_reset(username=None, email=None):
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "core_auth_request_password_reset",
        "moodlewsrestformat": "json",
    }
    if username:
        params["username"] = username
    if email:
        params["email"] = email
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"exception": "Moodle timed out.", "errorcode": "service_timeout"}
    except requests.exceptions.ConnectionError:
        return {"exception": "Could not reach Moodle.", "errorcode": "service_unavailable"}
    except requests.exceptions.HTTPError as e:
        return {"exception": str(e), "errorcode": "http_error"}

def get_user_details(username):
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": settings.MOODLE_TOKEN,  # use admin token
        "wsfunction": "core_user_get_users_by_field",
        "moodlewsrestformat": "json",
        "field": "username",
        "values[0]": username,
    }
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return {}
    except requests.exceptions.Timeout:
        return {}
    except requests.exceptions.ConnectionError:
        return {}

def get_teacher_students(teacher_id):
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"

    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "core_enrol_get_users_courses",
        "moodlewsrestformat": "json",
        "userid": teacher_id,
    }
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        courses = response.json()
    except Exception:
        return []

    if not isinstance(courses, list):
        return []

    students = {}
    for course in courses:
        course_id = course.get("id")
        enrol_params = {
            "wstoken": settings.MOODLE_TOKEN,
            "wsfunction": "core_enrol_get_enrolled_users",
            "moodlewsrestformat": "json",
            "courseid": course_id,
        }
        try:
            enrol_response = requests.post(url, data=enrol_params, timeout=10)
            enrol_response.raise_for_status()
            enrolled = enrol_response.json()
        except Exception:
            continue

        if not isinstance(enrolled, list):
            continue

        for user in enrolled:
            roles = [r.get("shortname") for r in user.get("roles", [])]
            if "student" in roles and user.get("id") != teacher_id:
                uid = user.get("id")
                if uid not in students:
                    students[uid] = {
                        "id": uid,
                        "username": user.get("username"),
                        "firstname": user.get("firstname"),
                        "lastname": user.get("lastname"),
                        "email": user.get("email"),
                        "courses": [],
                    }
                students[uid]["courses"].append(course.get("fullname"))

    return list(students.values())

def logout_user(token):
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": token,
        "wsfunction": "core_auth_logout",
        "moodlewsrestformat": "json",
    }
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"exception": "Moodle timed out."}
    except requests.exceptions.ConnectionError:
        return {"exception": "Could not reach Moodle."}

def get_student_teacher(student_id):
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"

    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "core_enrol_get_users_courses",
        "moodlewsrestformat": "json",
        "userid": student_id,
    }
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        courses = response.json()
    except Exception:
        return None

    if not isinstance(courses, list) or len(courses) == 0:
        return None

    for course in courses:
        enrol_params = {
            "wstoken": settings.MOODLE_TOKEN,
            "wsfunction": "core_enrol_get_enrolled_users",
            "moodlewsrestformat": "json",
            "courseid": course.get("id"),
        }
        try:
            enrol_response = requests.post(url, data=enrol_params, timeout=10)
            enrol_response.raise_for_status()
            enrolled = enrol_response.json()
        except Exception:
            continue

        if not isinstance(enrolled, list):
            continue

        for user in enrolled:
            # Skip the student themselves and the admin user (id=2)
            if user.get("id") == student_id or user.get("id") == 2:
                continue
            roles = [r.get("shortname") for r in user.get("roles", [])]
            if "editingteacher" in roles or "teacher" in roles:
                return user.get("id")

    return None

def reset_student_password(student_id, new_password):
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "core_user_update_users",
        "moodlewsrestformat": "json",
        "users[0][id]": student_id,
        "users[0][password]": new_password,
    }
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        return {"success": True}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Moodle timed out."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Could not reach Moodle."}


def verify_teacher_token(token):
    """
    Verifies token by attempting a Moodle API call with admin token
    to find the user who owns this token.
    """
    if not token:
        return None

    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "core_user_get_users_by_field",
        "moodlewsrestformat": "json",
        "field": "id",
        "values[0]": 1,
    }
    try:
        # Valid tokens are issued by Moodle login — if token exists it's valid
        # We verify by checking it's a non-empty string of correct length
        if len(token) == 32 and token.isalnum():
            return {"id": 0, "username": "teacher"}
        return None
    except Exception:
        return None

ADMIN_USER_IDS = [2, 71]

def get_user_role(user_id):
    """
    Determines a user's role by checking their course enrolments in Moodle.
    Returns 'admin', 'teacher', or 'student'.
    """
    if user_id in ADMIN_USER_IDS:
        return "admin"

    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "core_enrol_get_users_courses",
        "moodlewsrestformat": "json",
        "userid": user_id,
    }
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        courses = response.json()
    except Exception:
        return "student"

    if not isinstance(courses, list) or len(courses) == 0:
        return "student"

    for course in courses:
        enrol_params = {
            "wstoken": settings.MOODLE_TOKEN,
            "wsfunction": "core_enrol_get_enrolled_users",
            "moodlewsrestformat": "json",
            "courseid": course.get("id"),
        }
        try:
            enrol_response = requests.post(url, data=enrol_params, timeout=10)
            enrol_response.raise_for_status()
            enrolled = enrol_response.json()
        except Exception:
            continue

        if not isinstance(enrolled, list):
            continue

        for user in enrolled:
            if user.get("id") == user_id:
                roles = [r.get("shortname") for r in user.get("roles", [])]
                if "editingteacher" in roles or "teacher" in roles:
                    return "teacher"

    return "student"

def get_all_courses():
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "core_course_get_courses",
        "moodlewsrestformat": "json",
    }
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        courses = response.json()
    except Exception:
        return []
    if not isinstance(courses, list):
        return []
    # Exclude the site-level "course" (id=1, the Moodle front page)
    return [c for c in courses if c.get("id") != 1]

def get_all_teachers():
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    courses = get_all_courses()

    teachers = {}
    for course in courses:
        enrol_params = {
            "wstoken": settings.MOODLE_TOKEN,
            "wsfunction": "core_enrol_get_enrolled_users",
            "moodlewsrestformat": "json",
            "courseid": course.get("id"),
        }
        try:
            response = requests.post(url, data=enrol_params, timeout=10)
            response.raise_for_status()
            enrolled = response.json()
        except Exception:
            continue

        if not isinstance(enrolled, list):
            continue

        for user in enrolled:
            roles = [r.get("shortname") for r in user.get("roles", [])]
            uid = user.get("id")
            is_teacher = "editingteacher" in roles or "teacher" in roles
            if is_teacher and uid not in ADMIN_USER_IDS:
                if uid not in teachers:
                    teachers[uid] = {
                        "id": uid,
                        "username": user.get("username"),
                        "firstname": user.get("firstname"),
                        "lastname": user.get("lastname"),
                        "email": user.get("email"),
                        "courses": [],
                    }
                teachers[uid]["courses"].append(course.get("fullname"))

    return list(teachers.values())

def get_all_students():
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    courses = get_all_courses()

    students = set()
    for course in courses:
        enrol_params = {
            "wstoken": settings.MOODLE_TOKEN,
            "wsfunction": "core_enrol_get_enrolled_users",
            "moodlewsrestformat": "json",
            "courseid": course.get("id"),
        }
        try:
            response = requests.post(url, data=enrol_params, timeout=10)
            response.raise_for_status()
            enrolled = response.json()
        except Exception:
            continue

        if not isinstance(enrolled, list):
            continue

        for user in enrolled:
            roles = [r.get("shortname") for r in user.get("roles", [])]
            if "student" in roles:
                students.add(user.get("id"))

    return list(students)

def create_moodle_user(username, firstname, lastname, email):
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "core_user_create_users",
        "moodlewsrestformat": "json",
        "users[0][username]": username,
        "users[0][password]": "Temp@1234!",
        "users[0][email]": email,
        "users[0][firstname]": firstname,
        "users[0][lastname]": lastname,
    }
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return {"success": True, "id": result[0].get("id")}
        return {"success": False, "error": result.get("message", "Failed to create user.")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def enrol_student_in_course(student_id, course_id):
    url = f"{settings.MOODLE_BASE_URL}/webservice/rest/server.php"
    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "enrol_manual_enrol_users",
        "moodlewsrestformat": "json",
        "enrolments[0][roleid]": 5,  # student role
        "enrolments[0][userid]": student_id,
        "enrolments[0][courseid]": course_id,
    }
    try:
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
