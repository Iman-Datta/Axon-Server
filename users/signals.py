from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, Workspace

# Automatically create a Personal Workspace
# whenever a new User is created.

@receiver(post_save, sender=User)
def create_personal_workspace(sender, instance, created, **kwargs):
    if not created:
        return

    # Skip workspace creation if the user already has one.
    if hasattr(instance, "workspace"):
        return

    with transaction.atomic():
        Workspace.objects.create(
            type=Workspace.Type.PERSONAL,
            owner=instance,
        )