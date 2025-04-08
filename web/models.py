from django.db import models
import re
# from ckeditor.fields import RichTextField

class Information(models.Model):
    pdf = models.FileField(blank=True, null=True)

class RegistrationInfo(models.Model):
    STUDENT_STATUS_CHOICES = [
        (0, 'Student'),
        (1, 'Non-Student'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(primary_key=True)
    paper_title = models.CharField(max_length=255, blank=True, null=True)
    paper_number = models.CharField(max_length=50, blank=True, null=True)
    number_of_papers = models.IntegerField(default=1)
    student_status = models.IntegerField(choices=STUDENT_STATUS_CHOICES)
    payment_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True) 
