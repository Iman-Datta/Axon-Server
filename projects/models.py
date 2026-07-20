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
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Project.objects.filter(
                workspace=self.workspace,
                slug=slug
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class ProjectMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        LEAD = "LEAD", "Lead"
        DEVELOPER = "DEVELOPER", "Developer"
        VIEWER = "VIEWER", "Viewer"

    project = models.ForeignKey(Project, on_delete=models.CASCADE,related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships"
    )
    role = models.CharField(max_length=20, choices= Role.choices, default=Role.VIEWER)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project","user"],
                name="unique_project_member"
            )
        ]

class GitHubIntegration(models.Model):
    project = models.OneToOneField(Project,on_delete=models.CASCADE,related_name="github_integration")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.SET_NULL, null=True, related_name="github_integrations")

    repository_id = models.BigIntegerField(unique=True)
    repository_name = models.CharField(max_length=300)
    repository_full_name = models.CharField(max_length=300)

    default_branch = models.CharField(max_length=100)

    webhook_id = models.BigIntegerField(null=True, blank=True)
    webhook_secret = models.CharField(max_length=255, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'github_integrations'
    
    def __str__(self):
        return self.repository_full_name
