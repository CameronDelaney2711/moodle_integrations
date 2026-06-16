# Moodle Django API

Django REST API connected to Moodle via REST API.

## Stack
- Django REST Framework
- Moodle on AWS EC2 (Bitnami)
- Gunicorn
- SQLite

## Setup

1. Clone the repo
2. Create virtual environment: `python -m venv env && source env/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Create `.env` file with:
   - MOODLE_BASE_URL
   - MOODLE_TOKEN
   - MOODLE_SERVICE_NAME
   - SECRET_KEY
5. Run migrations: `python manage.py migrate`
6. Start server: `gunicorn --bind 0.0.0.0:8000 config.wsgi:application`

## Endpoints
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/login/` | Login |
| POST | `/api/logout/` | Logout |
| POST | `/api/register/` | Register |
| POST | `/api/forgot-password/` | Request password reset |
| GET | `/api/teacher/students/` | Get teacher's students |
| POST | `/api/teacher/reset-password/` | Reset student password |
| GET | `/api/teacher/notifications/` | Get notifications |
| POST | `/api/teacher/notifications/resolve/` | Resolve notification |

## Frontend
- `index.html` — Student forgot password page
- `teacher.html` — Teacher dashboard
