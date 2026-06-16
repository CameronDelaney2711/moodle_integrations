from django.db import models

# Create your models here.

class PasswordResetRequest(models.Model):
    student_id       = models.IntegerField()
    student_username = models.CharField(max_length=150)
    student_name     = models.CharField(max_length=255)
    teacher_id       = models.IntegerField()
    requested_at     = models.DateTimeField(auto_now_add=True)
    resolved         = models.BooleanField(default=False)
    resolved_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.student_username} → teacher {self.teacher_id}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'School Admin'),
    ]
    moodle_user_id = models.IntegerField(unique=True)
    username       = models.CharField(max_length=150, unique=True)
    role           = models.CharField(max_length=10, choices=ROLE_CHOICES)
    token          = models.CharField(max_length=64, blank=True)
    token_created_at = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class ActivationCode(models.Model):
    username   = models.CharField(max_length=150, unique=True)
    code       = models.CharField(max_length=8)
    used       = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at    = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.username} — {'used' if self.used else 'pending'}"

class StudentRegistrationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    firstname    = models.CharField(max_length=150)
    lastname     = models.CharField(max_length=150)
    email        = models.CharField(max_length=255, unique=True)
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    resolved_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.firstname} {self.lastname} ({self.status})"
