from ..models import Ticket

def handle_create_event(integration, payload):
    ref_type = payload.get("ref_type")

    if ref_type != "branch":
        return
    
    branch_name = payload.get("ref")
    if not branch_name:
        return

    ticket = Ticket.objects.filter(project = integration.project, ticket_number = branch_name).first()
    if not ticket:
        return

    if ticket.kanban_column == Ticket.KanbanColumn.TODO:
        ticket.kanban_column = Ticket.KanbanColumn.IN_PROGRESS
        ticket.save(update_fields=["kanban_column"])
    
def handle_push_event(integration, payload):
    ref = payload.get("ref")
    if not ref.startswith("refs/heads/"):
        return
    
    branch_name = ref.replace("refs/heads/", "")
    if not branch_name:
        return

    ticket = Ticket.objects.filter(project = integration.project, ticket_number = branch_name).first()
    if not ticket:
        return
    if ticket.kanban_column in (Ticket.KanbanColumn.REVIEW, Ticket.KanbanColumn.DONE):
        return
    ticket.kanban_column = Ticket.KanbanColumn.IN_PROGRESS
    ticket.save(update_fields=["kanban_column"])

def handle_pull_request_opened(integration, payload):
    pull_request = payload.get("pull_request", {})
    head = pull_request.get("head", {})
    branch_name = head.get("ref")
    if not branch_name:
        return

    ticket = Ticket.objects.filter(project = integration.project, ticket_number = branch_name).first()
    if not ticket:
        return
    
    if ticket.kanban_column not in (
    Ticket.KanbanColumn.TODO,
    Ticket.KanbanColumn.IN_PROGRESS,):
        return

    ticket.kanban_column = Ticket.KanbanColumn.REVIEW
    ticket.save(update_fields=["kanban_column"])

def handle_pull_request_closed(integration, payload):
    pull_request = payload.get("pull_request", {})
    head = pull_request.get("head", {})
    branch_name = head.get("ref")
    if not branch_name:
        return

    ticket = Ticket.objects.filter(project = integration.project, ticket_number = branch_name).first()
    if not ticket:
        return

    merged = pull_request.get("merged")

    if merged:
        ticket.kanban_column = Ticket.KanbanColumn.DONE
    else:
        ticket.kanban_column = Ticket.KanbanColumn.IN_PROGRESS

    ticket.save(update_fields=["kanban_column"])