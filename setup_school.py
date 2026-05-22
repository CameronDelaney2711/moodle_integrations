import requests

MOODLE_URL = "http://34.244.255.166"
ADMIN_TOKEN = "django_api_token_2024abcd"
API = "http://localhost:8000/api"

def moodle(function, params):
    params.update({
        "wstoken": ADMIN_TOKEN,
        "wsfunction": function,
        "moodlewsrestformat": "json"
    })
    res = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", data=params)
    return res.json()

# ── Step 1: Create 10 teachers ──────────────────────────────────────────
print("\n── Creating 10 teachers ──")
teachers = []
for i in range(1, 11):
    params = {
        "users[0][username]": f"teacher{i:02d}",
        "users[0][password]": "Teacher@1234",
        "users[0][email]": f"teacher{i:02d}@school.ie",
        "users[0][firstname]": "Teacher",
        "users[0][lastname]": f"{i:02d}",
    }
    result = moodle("core_user_create_users", params)
    if isinstance(result, list) and result:
        teacher_id = result[0].get("id")
        teachers.append({"id": teacher_id, "username": f"teacher{i:02d}"})
        print(f"✅ teacher{i:02d} (id={teacher_id})")
    else:
        print(f"❌ teacher{i:02d}: {result}")

# ── Step 2: Create 50 students ──────────────────────────────────────────
print("\n── Creating 50 students ──")
students = []
for i in range(1, 51):
    params = {
        "users[0][username]": f"student{i:02d}",
        "users[0][password]": "Student@1234",
        "users[0][email]": f"student{i:02d}@school.ie",
        "users[0][firstname]": "Student",
        "users[0][lastname]": f"{i:02d}",
    }
    result = moodle("core_user_create_users", params)
    if isinstance(result, list) and result:
        student_id = result[0].get("id")
        students.append({"id": student_id, "username": f"student{i:02d}"})
        print(f"✅ student{i:02d} (id={student_id})")
    else:
        print(f"❌ student{i:02d}: {result}")

# ── Step 3: Create 10 courses ────────────────────────────────────────────
print("\n── Creating 10 courses ──")
courses = []
subjects = [
    "Mathematics", "English", "Science", "History",
    "Geography", "Art", "Music", "Physical Education",
    "Computer Science", "Business Studies"
]
for i, subject in enumerate(subjects, 1):
    params = {
        "courses[0][fullname]": subject,
        "courses[0][shortname]": subject.lower().replace(" ", "")[:10] + str(i),
        "courses[0][categoryid]": 1,
    }
    result = moodle("core_course_create_courses", params)
    if isinstance(result, list) and result:
        course_id = result[0].get("id")
        courses.append({"id": course_id, "name": subject})
        print(f"✅ {subject} (id={course_id})")
    else:
        print(f"❌ {subject}: {result}")

# ── Step 4: Enrol teachers (1 per course) ────────────────────────────────
print("\n── Enrolling teachers ──")
for i, course in enumerate(courses):
    if i >= len(teachers):
        break
    teacher = teachers[i]
    params = {
        "enrolments[0][roleid]": 3,  # editingteacher
        "enrolments[0][userid]": teacher["id"],
        "enrolments[0][courseid]": course["id"],
        "enrolments[0][sendcoursewelcomemessage]": 0,
    }
    result = moodle("enrol_manual_enrol_users", params)
    if result is None or result == []:
        print(f"✅ {teacher['username']} → {course['name']}")
    else:
        print(f"❌ {teacher['username']} → {course['name']}: {result}")

# ── Step 5: Enrol students (5 per course) ────────────────────────────────
print("\n── Enrolling students ──")
for i, course in enumerate(courses):
    course_students = students[i*5:(i+1)*5]
    for student in course_students:
        params = {
            "enrolments[0][roleid]": 5,  # student
            "enrolments[0][userid]": student["id"],
            "enrolments[0][courseid]": course["id"],
            "enrolments[0][sendcoursewelcomemessage]": 0,
        }
        result = moodle("enrol_manual_enrol_users", params)
        if result is None or result == []:
            print(f"✅ {student['username']} → {course['name']}")
        else:
            print(f"❌ {student['username']} → {course['name']}: {result}")

print("\n── Setup complete! ──")
print(f"Teachers: {len(teachers)}")
print(f"Students: {len(students)}")
print(f"Courses:  {len(courses)}")
print("\nTeacher login: teacher01 / Teacher@1234")
print("Student login: student01 / Student@1234")
