from django.urls import path

from .views.project import (create_project_view,project_detail_view,project_update_view,delete_project, my_projects_view)

from .views.member import (add_member,list_member,update_member_role,remove_member,leave_project)

from .views.github import (github_repo_view, github_connect_view, disconnect_github_view, github_integration_status_view)

from .views.webhook import (github_webhook_view, create_github_webhook_view)

urlpatterns = [
    # Projects
    path("<slug:slug>/my/",my_projects_view,name="workspace-projects"),
    path("<slug:slug>/create/", create_project_view),
    path("<slug:slug>/<slug:project_slug>/", project_detail_view),
    path("<slug:slug>/<slug:project_slug>/update/", project_update_view),
    path("<slug:slug>/<slug:project_slug>/delete/", delete_project),

    # Members
    path("<slug:slug>/<slug:project_slug>/members/", list_member),
    path("<slug:slug>/<slug:project_slug>/member/add/", add_member),
    path("workspaces/<slug:slug>/projects/<slug:project_slug>/members/<int:member_id>/role/", update_member_role),
    path("workspaces/<slug:slug>/projects/<slug:project_slug>/members/<int:member_id>/remove/", remove_member),
    path("<slug:slug>/<slug:project_slug>/leave/", leave_project),

    # Github
    path("github/repositories/", github_repo_view, name="github-repositories"),
    path("<slug:slug>/<slug:project_slug>/github/connect/", github_connect_view, name="github-connect"),
    path("<slug:slug>/<slug:project_slug>/github/disconnect/", disconnect_github_view, name="github-disconnect"),
    path("<slug:slug>/<slug:project_slug>/github/create-webhook/", create_github_webhook_view, name="github-create-webhook"),
    path("github/webhook/", github_webhook_view, name="github-webhook"),
    path("<slug:slug>/<slug:project_slug>/github/status/",github_integration_status_view,name="github-status"),
]