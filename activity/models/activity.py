from django.db import models
from django.conf import settings
from projects.models import Project
from tickets.models import Ticket


class Activity(models.Model):

    class Verb(models.TextChoices):
        # Project-level
        PROJECT_CREATED = "PROJECT_CREATED", "Project Created"
        MEMBER_ADDED = "MEMBER_ADDED", "Member Added"
        MEMBER_REMOVED = "MEMBER_REMOVED", "Member Removed"
        MEMBER_ROLE_CHANGED = "MEMBER_ROLE_CHANGED", "Member Role Changed"
        EPIC_CREATED = "EPIC_CREATED", "Epic Created"
        EPIC_DELETED = "EPIC_DELETED", "Epic Deleted"
        GITHUB_CONNECTED = "GITHUB_CONNECTED", "GitHub Connected"
        GITHUB_DISCONNECTED = "GITHUB_DISCONNECTED", "GitHub Disconnected"

        # Ticket-level
        TICKET_CREATED = "TICKET_CREATED", "Ticket Created"
        TICKET_ASSIGNED = "TICKET_ASSIGNED", "Ticket Assigned"
        TICKET_UNASSIGNED = "TICKET_UNASSIGNED", "Ticket Unassigned"
        TICKET_STATUS_CHANGED = "TICKET_STATUS_CHANGED", "Ticket Status Changed"
        TICKET_COLUMN_CHANGED = "TICKET_COLUMN_CHANGED", "Ticket Column Changed"
        TICKET_PRIORITY_CHANGED = "TICKET_PRIORITY_CHANGED", "Ticket Priority Changed"
        TICKET_DUE_DATE_CHANGED = "TICKET_DUE_DATE_CHANGED", "Ticket Due Date Changed"
        TICKET_EPIC_CHANGED = "TICKET_EPIC_CHANGED", "Ticket Epic Changed"
        TICKET_STORY_POINTS_CHANGED = "TICKET_STORY_POINTS_CHANGED", "Story Points Changed"
        TICKET_COMMENTED = "TICKET_COMMENTED", "Ticket Commented"
        TICKET_GITHUB_PUSH = "TICKET_GITHUB_PUSH", "GitHub Push Linked"
        TICKET_GITHUB_PR_OPENED = "TICKET_GITHUB_PR_OPENED", "GitHub PR Opened"
        TICKET_GITHUB_PR_MERGED = "TICKET_GITHUB_PR_MERGED", "GitHub PR Merged"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="activities", db_index=True
    )

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, null=True, blank=True,
        related_name="activities", db_index=True,
    )

    verb = models.CharField(max_length=40, choices=Verb.choices, db_index=True)

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name="activities",
    )

    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name="targeted_activities",
    )

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["ticket", "-created_at"]),
            models.Index(fields=["project", "verb", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.verb} · project={self.project_id} ticket={self.ticket_id}"