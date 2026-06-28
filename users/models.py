from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from ..organizations.models import Organization
from django.core.exceptions import ValidationError

class User(AbstractUser):
    username = models.CharField(unique=True, max_length=30, db_index=True)

    email = models.EmailField(unique=True, null=True, blank=True, db_index=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    

    avatar = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True)

    is_profile_completed = models.BooleanField(default=False, db_index=True)
    is_username_set = models.BooleanField(default=False,db_index=True)
    is_email_verified = models.BooleanField(default=False, db_index=True)

    github_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    github_username = models.CharField(max_length=255, blank=True)
    github_profile = models.URLField(blank=True)

    linkedin_profile = models.URLField(blank=True)
    portfolio_website = models.URLField(blank=True)

    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_verification_expire = models.DateTimeField(blank=True, null=True)

    refresh_token_hash = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    email_otp_hash = models.CharField(max_length=255, blank=True, null=True)
    email_otp_expire = models.DateTimeField(blank=True, null=True)
    pending_email = models.EmailField(blank=True, null=True)
    oauth_state = models.CharField(max_length=255,blank=True,null=True)
    oauth_state_expire = models.DateTimeField(blank=True,null=True)

    # username, first_name, last_name, password, is_active,
    # last_login, date_joined, groups, user_permissions

class Workspace(models.Model):
    WORKSPACE_TYPES = [
        ("personal", "Personal"),
        ("organization", "Organization"),
    ]
    
    type = models.CharField(max_length=20,choices=WORKSPACE_TYPES,)
    
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace",
        null=True,
        blank=True,
    )

    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="workspace",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )


    def clean(self):
        if self.type == "personal":
            if not self.owner:
                raise ValidationError(
                    "Personal workspace must have an owner."
                )

            if self.organization:
                raise ValidationError(
                    "Personal workspace cannot have an organization."
                )

        elif self.type == "organization":
            if not self.organization:
                raise ValidationError(
                    "Organization workspace must have an organization."
                )

            if self.owner:
                raise ValidationError(
                    "Organization workspace cannot have an owner."
                )

    def __str__(self):
        if self.type == "personal":
            return self.owner.username

        return self.organization.name

