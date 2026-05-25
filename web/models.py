from django.db import models


class Information(models.Model):
    pdf = models.FileField(blank=True, null=True)


class RegistrationInfo(models.Model):
    REGISTRATION_TYPE_CHOICES = [
        ('regular', 'Regular Registration'),
        ('src', 'SRC Registration'),
        ('attendee', 'Attendee / Non-Author Registration'),
        ('phd', 'PhD Research Track'),
        ('secondary', 'Supplementary Registration'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(primary_key=True)
    paper_title = models.CharField(max_length=255, blank=True, null=True)
    paper_number = models.CharField(max_length=50, blank=True, null=True)
    number_of_papers = models.IntegerField(default=1)
    registration_type = models.CharField(
        max_length=20,
        choices=REGISTRATION_TYPE_CHOICES,
        default='regular',
    )
    affiliation = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
