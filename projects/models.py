from django.db import models
from organizations.models import Organization

class Project(models.Model):
    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(max=100)