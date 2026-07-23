from rest_framework import serializers
from ..models import GitHubIntegration

class GitHubConnectSerializer(serializers.Serializer):
    repository_id = serializers.IntegerField()

    def validate_repository_id(self, value):
        if GitHubIntegration.objects.filter(repository_id=value).exists():
            raise serializers.ValidationError(
                "This GitHub repository is already connected to another Axon project."
            )
        return value

class GitHubIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubIntegration
        fields = [
            "repository_id",
            "repository_name",
            "repository_full_name",
            "default_branch",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields