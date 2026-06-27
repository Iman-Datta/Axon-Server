from rest_framework import serializers

from projects.models import Project


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "visibility",
            "github_repository",
            "website",
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Project name is required.")
        return value

    def validate_visibility(self, value):
        valid_choices = [
            choice[0]
            for choice in Project.VISIBILITY_CHOICES
        ]
        if value not in valid_choices:
            raise serializers.ValidationError("Invalid visibility.")
        return value

    def validate_github_repository(self, value):
        if value and not value.startswith("https://github.com/"):
            raise serializers.ValidationError("Enter a valid GitHub repository URL.")
        return value

    def validate_website(self, value):
        return value.strip()