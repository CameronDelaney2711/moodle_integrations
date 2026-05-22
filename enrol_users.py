import requests

MOODLE_URL = "http://34.244.255.166"
ADMIN_TOKEN = "django_api_token_2024abcd"

def moodle(function, params):
    params.update({
        "wstoken": ADMIN_TOKEN,
        "wsfunction": function,
        "moodlewsrestformat": "json"
    })
    res = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", data=params)
    return res.json()

# Known IDs from previous run
teachers = [
    {"id": 10, "username": "teacher01"},
    {"id": 11, "username": "teacher02"},
    {"id": 12, "username": "teacher03"},
    {"id": 13, "username": "teacher04"},
    {"id": 14, "username": "teacher05"},
    {"id": 15, "username": "teacher06"},
    {"id": 16, "username": "teacher07"},
    {"id": 17, "username": "teacher08"},
    {"id": 18, "username": "teacher09"},
    {"id": 19, "username": "teacher10"},
]

students = [
    {"id": 20, "username": "student01"},
    {"id": 21, "username": "student02"},
    {"id": 22, "username": "student03"},
    {"id": 23, "username": "student04"},
    {"id": 24, "username": "student05"},
    {"id": 25, "username": "student06"},
    {"id": 26, "username": "student07"},
    {"id": 27, "username": "student08"},
    {"id": 28, "username": "student09"},
    {"id": 29, "username": "student10"},
    {"id": 30, "username": "student11"},
    {"id": 31, "username": "student12"},
    {"id": 32, "username": "student13"},
    {"id": 33, "username": "student14"},
    {"id": 34, "username": "student15"},
    {"id": 35, "username": "student16"},
    {"id": 36, "username": "student17"},
    {"id": 37, "username": "student18"},
    {"id": 38, "username": "student19"},
    {"id": 39, "username": "student20"},
    {"id": 40, "username": "student21"},
    {"id": 41, "username": "student22"},
    {"id": 42, "username": "student23"},
    {"id": 43, "username": "student24"},
    {"id": 44, "username": "student25"},
    {"id": 45, "username": "student26"},
    {"id": 46, "username": "student27"},
    {"id": 47, "username": "student28"},
    {"id": 48, "username": "student29"},
    {"id": 49, "username": "student30"},
    {"id": 50, "username": "student31"},
    {"id": 51, "username": "student32"},
    {"id": 52, "username": "student33"},
    {"id": 53, "username": "student34"},
    {"id": 54, "username": "student35"},
    {"id": 55, "username": "student36"},
    {"id": 56, "username": "student37"},
    {"id": 57, "username": "student38"},
    {"id": 58, "username": "student39"},
    {"id": 59, "username": "student40"},
    {"id": 60, "username": "student41"},
    {"id": 61, "username": "student42"},
    {"id": 62, "username": "student43"},
    {"id": 63, "username": "student44"},
    {"id": 64, "username": "student45"},
    {"id": 65, "username": "student46"},
    {"id": 66, "username": "student47"},
    {"id": 67, "username": "student48"},
    {"id": 68, "username": "student49"},
    {"id": 69, "username": "student50"},
]

courses = [
    {"id": 4,  "name": "Mathematics"},
    {"id": 5,  "name": "English"},
    {"id": 6,  "name": "Science"},
    {"id": 7,  "name": "History"},
    {"id": 8,  "name": "Geography"},
    {"id": 9,  "name": "Art"},
    {"id": 10, "name": "Music"},
    {"id": 11, "name": "Physical Education"},
    {"id": 12, "name": "Computer Science"},
    {"id": 13, "name": "Business Studies"},
]

# Enrol teachers directly via database to avoid email issue
print("\n── Enrolling teachers via DB ──")
import subprocess
for i, course in enumerate(courses):
    teacher = teachers[i]
    cmd = f"/opt/bitnami/mariadb/bin/mariadb -u bn_moodle -p'De5FmF17ORX6QNJcKhoXeLzGR917BDTmhQKl05ua9kuzVC0NN7fxbMwyr9RRcuc4' bitnami_moodle -e \"INSERT IGNORE INTO mdl_user_enrolments (status, enrolid, userid, timestart, timecreated, timemodified, modifierid) SELECT 0, e.id, {teacher['id']}, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 2 FROM mdl_enrol e WHERE e.courseid={course['id']} AND e.enrol='manual' LIMIT 1;\""
    subprocess.run(cmd, shell=True)
    # Assign teacher role
    cmd2 = f"/opt/bitnami/mariadb/bin/mariadb -u bn_moodle -p'De5FmF17ORX6QNJcKhoXeLzGR917BDTmhQKl05ua9kuzVC0NN7fxbMwyr9RRcuc4' bitnami_moodle -e \"INSERT IGNORE INTO mdl_role_assignments (roleid, contextid, userid, timemodified, modifierid) SELECT 3, c.id, {teacher['id']}, UNIX_TIMESTAMP(), 2 FROM mdl_context c JOIN mdl_course co ON co.id=c.instanceid WHERE co.id={course['id']} AND c.contextlevel=50;\""
    subprocess.run(cmd2, shell=True)
    print(f"✅ {teacher['username']} → {course['name']}")

print("\n── Enrolling students via DB ──")
for i, course in enumerate(courses):
    course_students = students[i*5:(i+1)*5]
    for student in course_students:
        cmd = f"/opt/bitnami/mariadb/bin/mariadb -u bn_moodle -p'De5FmF17ORX6QNJcKhoXeLzGR917BDTmhQKl05ua9kuzVC0NN7fxbMwyr9RRcuc4' bitnami_moodle -e \"INSERT IGNORE INTO mdl_user_enrolments (status, enrolid, userid, timestart, timecreated, timemodified, modifierid) SELECT 0, e.id, {student['id']}, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 2 FROM mdl_enrol e WHERE e.courseid={course['id']} AND e.enrol='manual' LIMIT 1;\""
        subprocess.run(cmd, shell=True)
        # Assign student role
        cmd2 = f"/opt/bitnami/mariadb/bin/mariadb -u bn_moodle -p'De5FmF17ORX6QNJcKhoXeLzGR917BDTmhQKl05ua9kuzVC0NN7fxbMwyr9RRcuc4' bitnami_moodle -e \"INSERT IGNORE INTO mdl_role_assignments (roleid, contextid, userid, timemodified, modifierid) SELECT 5, c.id, {student['id']}, UNIX_TIMESTAMP(), 2 FROM mdl_context c JOIN mdl_course co ON co.id=c.instanceid WHERE co.id={course['id']} AND c.contextlevel=50;\""
        subprocess.run(cmd2, shell=True)
        print(f"✅ {student['username']} → {course['name']}")

print("\n── Done! ──")
print("Purging Moodle cache...")
subprocess.run("sudo -u daemon php /bitnami/moodle/admin/cli/purge_caches.php", shell=True)
print("All done!")
