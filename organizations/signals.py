from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Organization
from users.models import Workspace

# Automatically create an Organization Workspace
# whenever a new Organization is created.

@receiver(post_save, sender=Organization)
def create_organization_workspace(sender, instance, created, **kwargs):
    if not created:
        return

    # Skip workspace creation if the user already has one.
    if hasattr(instance, "workspace"):
        return

    with transaction.atomic():
        Workspace.objects.create(
            type=Workspace.Type.ORGANIZATION,
            organization=instance,
        )