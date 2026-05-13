from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(unique=True, max_length=30)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True) # Pillow is needed for image field
    bio = models.TextField(blank=True)

    is_email_verified = models.BooleanField(default=False)
    is_profile_completed = models.BooleanField(default=False)

    google_id = models.CharField(max_length=255,blank=True, null=True)

    github_profile = models.URLField(blank=True)
    linkedin_profile = models.URLField(blank=True)
    portfolio_website = models.URLField(blank=True)

    # username, first_name, last_name, password, is_active, last_login, date_joined, groups, user_permissions, 