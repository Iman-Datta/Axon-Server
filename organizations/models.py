import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Organization(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=50, blank=True)
    description = models.TextField(blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.SET_NULL, null=True, related_name="created_organizations")
    created_at = models.DateTimeField(auto_now_add= True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug

            while Organization.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

            self.slug = slug
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
class OrganizationMember(models.Model):

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organization_memberships")
    role = models.CharField(max_length=20, choices= Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "user"
                ],
                name="unique_organization_member"
            )
        ]
        
    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.organization.name}"
        )