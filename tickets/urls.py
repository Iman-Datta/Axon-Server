from django.urls import path

from .views.epic import (create_epic,update_epic,list_epics,delete_epic)
from .views.ticket import (
    create_ticket,
    update_ticket,
    list_tickets,
    retrieve_ticket,
    delete_ticket,
    assign_ticket,
)

rlpatterns = [
    path("", list_epics, name="list_epics"),
    path("", create_epic, name="create_epic"),          # POST
    path("<int:epic_id>/", update_epic, name="update_epic"),   # PATCH
    path("<int:epic_id>/", delete_epic, name="delete_epic"),   # DELETE

    path("", list_tickets, name="list_tickets"),          # GET
    path("create/", create_ticket, name="create_ticket"), # POST
    path("<int:ticket_id>/", retrieve_ticket, name="retrieve_ticket"),  # GET
    path("<int:ticket_id>/update/", update_ticket, name="update_ticket"),# PATCH
    path("<int:ticket_id>/delete/", delete_ticket, name="delete_ticket"),# DELETE
    path("<int:ticket_id>/assign/", assign_ticket, name="assign_ticket"),# PATCH
]