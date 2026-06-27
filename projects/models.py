from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from organizations.models import Organization


class Workspace(models.Model):
    WORKSPACE_TYPES = [
        ("personal", "Personal"),
        ("organization", "Organization"),
    ]
    
    type = models.CharField(
        max_length=20,
        choices=WORKSPACE_TYPES,
    )

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


class Project(models.Model):
    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
    ]

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="projects",
    )

    name = models.CharField(
        max_length=100,
    )

    slug = models.SlugField(
        max_length=100,
        editable=False,
    )

    description = models.TextField(blank=True,)
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default="private",
    )

    github_repository = models.URLField(blank=True)
    website = models.URLField(blank=True)
    is_archived = models.BooleanField(default=False,)
    created_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True,)

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "slug"],
                name="unique_project_slug_per_workspace",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name