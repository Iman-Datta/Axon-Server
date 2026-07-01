from rest_framework import serializers

from projects.models import Project
from users.models import Workspace

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "workspace_id",
            "name",
            "description",
            "visibility",
            "website",
        ]