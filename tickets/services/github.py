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
    ref_type = payload.get("ref_type")
    if ref_type != "branch":
        return
    
    branch_name = payload.get("ref")
    if not branch_name:
        return

    ticket = Ticket.objects.filter(project = integration.project, ticket_number = branch_name).first()
    if not ticket:
        return

    ticket.kanban_column = Ticket.KanbanColumn.IN_PROGRESS
    ticket.save(update_fields=["kanban_column"])
    
def handle_pull_request_opened(integration, payload):
    ref_type = payload.get("ref_type")
    if ref_type != "branch":
        return
    
    branch_name = payload.get("ref")
    if not branch_name:
        return

    ticket = Ticket.objects.filter(project = integration.project, ticket_number = branch_name).first()
    if not ticket:
        return
    
    if ticket.kanban_column == Ticket.KanbanColumn.IN_PROGRESS or ticket.kanban_column == Ticket.KanbanColumn.TODO:
        ticket.kanban_column = Ticket.KanbanColumn.REVIEW
        ticket.save(update_fields=["kanban_column"])

    
def handle_pull_request_closed():
    pass