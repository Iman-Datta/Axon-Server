
from django.db import models
from django.utils.text import slugify
from ..users.models import Workspace
from django.conf import settings


class Project(models.Model):
    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
    ]

    workspace = models.ForeignKey(Workspace,on_delete=models.CASCADE,related_name="projects",)

    name = models.CharField(max_length=100,)
    slug = models.SlugField(max_length=100,editable=False,)
    description = models.TextField(blank=True,)
    visibility = models.CharField(max_length=10,choices=VISIBILITY_CHOICES,default="private",)

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
    
class ProjectMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        VIEWER = "VIEWER", "Viewer"
        EDITOR = "EDITOR", "Editor"

    project = models.ForeignKey(Project, on_delete=models.CASCADE,related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships"
    )
    role = models.CharField(max_length=20, choices= Role.choices, default=Role.VIEWER)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project","user"],
                name="unique_project_member"
            )
        ]