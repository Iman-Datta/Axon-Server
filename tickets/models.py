from django.db import models
from django.conf import settings
from projects.models import Project


class Epic(models.Model):
    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name="epics",)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7,default="#3B82F6",help_text="Hex color code",)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,related_name="created_epics",)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"],
                name="unique_epic_name_per_project",
            )
        ]

    def __str__(self):
        return self.name

class Ticket(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        OPEN = "OPEN", "Open"
        BLOCKED = "BLOCKED", "Blocked"
        DONE = "DONE", "Done"
        CANCELLED = "CANCELLED", "Cancelled"

    class KanbanColumn(models.TextChoices):
        TODO = "TODO", "To Do"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        REVIEW = "REVIEW", "Review"
        DONE = "DONE", "Done"

    class Type(models.TextChoices):
        TASK = "TASK", "Task"
        BUG = "BUG", "Bug"
        STORY = "STORY", "Story"
        FEATURE = "FEATURE", "Feature"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    STORY_POINT_CHOICES = [
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (5, "5"),
        (8, "8"),
        (13, "13"),
        (21, "21"),
        (34, "34"),
    ]

    project = models.ForeignKey(Project,on_delete=models.CASCADE,related_name="tickets")
    epic = models.ForeignKey(Epic,on_delete=models.SET_NULL,null=True,blank=True,related_name="tickets")

    ticket_number = models.CharField(max_length=20,editable=False,db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20,choices=Type.choices,default=Type.TASK,db_index=True,)

    status = models.CharField(max_length=20,choices=Status.choices,default=Status.DRAFT,db_index=True,)
    kanban_column = models.CharField(max_length=20,choices=KanbanColumn.choices,default=KanbanColumn.TODO,db_index=True)

    priority = models.CharField(max_length=20,choices=Priority.choices,default=Priority.MEDIUM,db_index=True,)
    story_points = models.PositiveSmallIntegerField(choices=STORY_POINT_CHOICES,default=1)

    estimated_hours = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)

    due_date = models.DateTimeField(null=True,blank=True)
    order = models.PositiveIntegerField(default=0)

    creator = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="created_tickets")
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="assigned_tickets")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["project", "priority"]),
            models.Index(fields=["project", "assignee"]),
            models.Index(fields=["project", "kanban_column", "order"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "ticket_number"],
                name="unique_ticket_number_per_project",
            )
        ]

    def __str__(self):
        return self.ticket_number