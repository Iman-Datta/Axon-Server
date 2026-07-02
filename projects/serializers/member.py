from rest_framework import serializers
from users.models import User
from ..models import ProjectMember

class AddMemberSerializer(serializers.Serializer):
    username = serializers.CharField()
    role = serializers.ChoiceField(choices=ProjectMember.Role.choices,default=ProjectMember.Role.VIEWER)

    def validate_username(self, value):
        try:
            return User.objects.get(username=value.strip())
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
    def validate_role(self, value):
        if value in [
            ProjectMember.Role.LEAD,
            ProjectMember.Role.OWNER,
        ]:
            raise serializers.ValidationError("New members can only be added as Developer or Viewer.")
        return value
        
    def validate(self, attrs):
        project = self.context["project"]
        user = attrs["username"]
        if ProjectMember.objects.filter(project=project, user=user).exists():
            raise serializers.ValidationError("User is already a member of this project.")
        return attrs
    
class ProjectMemberListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    avatar = serializers.URLField(source="user.avatar", read_only=True)
    github_username = serializers.CharField(
        source="user.github_username",
        read_only=True
    )

    class Meta:
        model = ProjectMember
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "github_username",
            "role",
            "joined_at",
        ]

class UpdateMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=ProjectMember.Role.choices)

    def validate_role(self, value):
        if value == ProjectMember.Role.OWNER:
            raise serializers.ValidationError("Ownership cannot be assigned using this endpoint.")

        return value