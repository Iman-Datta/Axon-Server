from django.urls import path

from .views.epic import create_epic, update_epic, list_epics, delete_epic, epic_details_view
from .views.ticket import (create_ticket,update_ticket,list_tickets,retrieve_ticket,delete_ticket,assign_ticket, update_board)

urlpatterns = [
    # Epic
    path("epics/", list_epics, name="list_epics"),
    path("epics/create/", create_epic, name="create_epic"),
    path("epic/<int:epic_id>/update/", update_epic, name="update_epic"),
    path("epic/<int:epic_id>/delete/", delete_epic, name="delete_epic"),
    path("epic/<int:epic_id>", epic_details_view, name="epic_details"),

    # Ticket
    path("", list_tickets, name="list_tickets"),
    path("create/", create_ticket, name="create_ticket"),
    path("<int:ticket_id>/", retrieve_ticket, name="retrieve_ticket"),
    path("<int:ticket_id>/update/", update_ticket, name="update_ticket"),
    path("<int:ticket_id>/delete/", delete_ticket, name="delete_ticket"),
    path("<int:ticket_id>/assign/", assign_ticket, name="assign_ticket"),
    path("board/",update_board, name="update-board"),
]