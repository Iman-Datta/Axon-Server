import re

from django.db import models
from django.utils.text import slugify
from users.models import Workspace
from django.conf import settings

_STOPWORDS = {"the", "a", "an", "and", "or", "of", "for", "to", "in", "on"}

def generate_project_key(name):

    words = re.findall(r"[A-Za-z0-9]+", name)
    words = [w for w in words if w.lower() not in _STOPWORDS]

    if not words:
        return "PRJ"

    if len(words) == 1:
        return words[0][:4].upper()

    key = "".join(w[0] for w in words).upper()

    if len(key) < 2:
        key = (key + words[0][1:]).upper()

    return key[:4]


class Project(models.Model):
    VISIBILITY_CHOICES = [
        ("public", "Public"),
        ("private", "Private"),
    ]

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="projects")

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, editable=False)

    # Short unique prefix used for ticket numbers, e.g. "AB" -> AB-001, AB-002
    # Fully auto-generated on save. Never user-editable.
    key = models.CharField(max_length=8, editable=False)

    # Per-project counter. Incremented under a row lock whenever a ticket
    # is created, so two simultaneous requests can never get the same number.
    ticket_sequence = models.PositiveIntegerField(default=0)

    description = models.TextField(blank=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default="private")

    website = models.URLField(blank=True)

    is_archived = models.BooleanField(default=False)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "slug"],
                name="unique_project_slug_per_workspace",
            ),
            models.UniqueConstraint(
                fields=["workspace", "key"],
                name="unique_project_key_per_workspace",
            ),
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

        if not self.key:
            base_key = generate_project_key(self.name)
            key = base_key
            counter = 1
            while Project.objects.filter(
                workspace=self.workspace,
                key=key
            ).exclude(pk=self.pk).exists():
                suffix = str(counter)
                key = (base_key[: 8 - len(suffix)] + suffix)
                counter += 1
            self.key = key

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProjectMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        LEAD = "LEAD", "Lead"
        DEVELOPER = "DEVELOPER", "Developer"
        VIEWER = "VIEWER", "Viewer"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "user"],
                name="unique_project_member"
            )
        ]

class GitHubIntegration(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="github_integration")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="github_integrations")

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