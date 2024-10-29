from django.db import models
import re
from ckeditor.fields import RichTextField

class Information(models.Model):
    pdf = models.FileField(blank=True, null=True)