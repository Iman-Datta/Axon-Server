from django.db import transaction
from ..models import Ticket

from activity.services import log_activity
from activity.models import Activity

def handle_create_event(integration, payload):
    ref_type = payload.get("ref_type")
    if ref_type != "branch":
        return

    branch_name = payload.get("ref")
    if not branch_name:
        return

    ticket = Ticket.objects.filter(project=integration.project, ticket_number=branch_name).first()
    if not ticket:
        return

    old_column = ticket.kanban_column

    with transaction.atomic():
        if ticket.kanban_column == Ticket.KanbanColumn.TODO:
            ticket.kanban_column = Ticket.KanbanColumn.IN_PROGRESS
            ticket.save(update_fields=["kanban_column"])

            log_activity(
                project=integration.project,
                ticket=ticket,
                actor=None,  # System/Automation actor
                verb=Activity.Verb.TICKET_COLUMN_CHANGED,
                metadata={
                    "ticket_number": ticket.ticket_number,
                    "ticket_title": ticket.title,
                    "old_column": old_column,
                    "new_column": ticket.kanban_column,
                    "trigger": "github_branch_created",
                    "branch_name": branch_name,
                }
            )

def handle_push_event(integration, payload):
    ref = payload.get("ref")
    if not ref or not ref.startswith("refs/heads/"):
        return

    branch_name = ref.replace("refs/heads/", "")
    ticket = Ticket.objects.filter(project=integration.project, ticket_number=branch_name).first()
    if not ticket:
        return

    commits = payload.get("commits", [])
    commit_count = len(commits)
    head_commit = payload.get("head_commit", {})

    old_column = ticket.kanban_column

    with transaction.atomic():
        # Update column if applicable
        if ticket.kanban_column not in (Ticket.KanbanColumn.REVIEW, Ticket.KanbanColumn.DONE):
            ticket.kanban_column = Ticket.KanbanColumn.IN_PROGRESS
            ticket.save(update_fields=["kanban_column"])

        # Always log the push activity
        log_activity(
            project=integration.project,
            ticket=ticket,
            actor=None,
            verb=Activity.Verb.TICKET_GITHUB_PUSH,
            metadata={
                "ticket_number": ticket.ticket_number,
                "ticket_title": ticket.title,
                "branch_name": branch_name,
                "commit_count": commit_count,
                "head_commit_message": head_commit.get("message", "").split("\n")[0],
                "head_commit_url": head_commit.get("url"),
                "pusher_username": payload.get("pusher", {}).get("name"),
                "column_changed": old_column != ticket.kanban_column,
                "old_column": old_column,
                "new_column": ticket.kanban_column,
            }
        )

def handle_pull_request_opened(integration, payload):
    pull_request = payload.get("pull_request", {})
    head = pull_request.get("head", {})
    branch_name = head.get("ref")

    if not branch_name:
        return

    ticket = Ticket.objects.filter(project=integration.project, ticket_number=branch_name).first()
    if not ticket:
        return

    old_column = ticket.kanban_column

    with transaction.atomic():
        if ticket.kanban_column in (Ticket.KanbanColumn.TODO, Ticket.KanbanColumn.IN_PROGRESS):
            ticket.kanban_column = Ticket.KanbanColumn.REVIEW
            ticket.save(update_fields=["kanban_column"])

        log_activity(
            project=integration.project,
            ticket=ticket,
            actor=None,
            verb=Activity.Verb.TICKET_GITHUB_PR_OPENED,
            metadata={
                "ticket_number": ticket.ticket_number,
                "ticket_title": ticket.title,
                "pr_number": pull_request.get("number"),
                "pr_title": pull_request.get("title"),
                "pr_url": pull_request.get("html_url"),
                "sender_username": payload.get("sender", {}).get("login"),
                "old_column": old_column,
                "new_column": ticket.kanban_column,
            }
        )

def handle_pull_request_closed(integration, payload):
    pull_request = payload.get("pull_request", {})
    head = pull_request.get("head", {})
    branch_name = head.get("ref")

    if not branch_name:
        return

    ticket = Ticket.objects.filter(project=integration.project, ticket_number=branch_name).first()
    if not ticket:
        return

    merged = pull_request.get("merged", False)
    old_column = ticket.kanban_column

    with transaction.atomic():
        if merged:
            ticket.kanban_column = Ticket.KanbanColumn.DONE
            verb = Activity.Verb.TICKET_GITHUB_PR_MERGED
        else:
            ticket.kanban_column = Ticket.KanbanColumn.IN_PROGRESS
            verb = Activity.Verb.TICKET_COLUMN_CHANGED  # Log general column update if PR closed without merging

        ticket.save(update_fields=["kanban_column"])

        log_activity(
            project=integration.project,
            ticket=ticket,
            actor=None,
            verb=verb,
            metadata={
                "ticket_number": ticket.ticket_number,
                "ticket_title": ticket.title,
                "pr_number": pull_request.get("number"),
                "pr_title": pull_request.get("title"),
                "pr_url": pull_request.get("html_url"),
                "merged": merged,
                "merged_by": pull_request.get("merged_by", {}).get("login") if merged else None,
                "old_column": old_column,
                "new_column": ticket.kanban_column,
            }
        )