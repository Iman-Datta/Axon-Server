from django.urls import path

from .views.project import (
    create_project_view,
    list_projects_view,
    project_detail_view,
    project_update_view,
    delete_project,
)

from .views.member import (
    add_member,
    list_member,
    update_member_role,
    remove_member,
    leave_project,
)

urlpatterns = [
    # Projects
    path("workspaces/<slug:slug>/", list_projects_view),
    path("workspaces/<slug:slug>/create/", create_project_view),
    path("workspaces/<slug:slug>/projects/<slug:project_slug>/", project_detail_view),
    path("workspaces/<slug:slug>/projects/<slug:project_slug>/update/", project_update_view),
    path("workspaces/<slug:slug>/projects/<slug:project_slug>/delete/", delete_project),

    # Members
    path("workspaces/<slug:slug>/projects/<slug:project_slug>/members/", list_member),
    path("workspaces/<slug:slug>/projects/<slug:project_slug>/members/add/", add_member),
    path("workspaces/<slug:slug>/projects/<slug:project_slug>/members/<int:member_id>/role/", update_member_role),
    path("workspaces/<slug:slug>/projects/<slug:project_slug>/members/<int:member_id>/remove/", remove_member),
    path("workspaces/<slug:slug>/projects/<slug:project_slug>/leave/", leave_project),
]