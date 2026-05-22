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
