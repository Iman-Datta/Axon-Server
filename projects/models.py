
from django.db import models
from django.utils.text import slugify
from users.models import Workspace
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

    website = models.URLField(blank=True)

    is_archived = models.BooleanField(default=False,)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.SET_NULL, null=True, related_name="created_projects")
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

class GitRepository(models.Model):

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="git_repository"
    )

    provider = models.CharField(max_length=20,default="github")
    github_repo_id = models.BigIntegerField(unique=True)
    owner = models.CharField(max_length=100)
    repo_name = models.CharField(max_length=100)
    webhook_secret = models.CharField(max_length=255)
    installation_id = models.BigIntegerField(null=True,blank=True)

    is_active = models.BooleanField(default=True)