from .models.activity import Activity

def log_activity(
    *,
    project,
    verb,
    actor=None,
    ticket=None,
    target_user=None,
    metadata=None
):
    if verb.startswith("TICKET_") and not ticket:
        raise ValueError(f"Verb '{verb}' requires a ticket object.")

    return Activity.objects.create(
        project=project,
        ticket=ticket,
        verb=verb,
        actor=actor,
        target_user=target_user,
        metadata=metadata or {},
    )