from rest_framework import serializers
from .models import Organization, OrganizationMember
from users.models import User
from projects.models import Project

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization

        fields = [
            "id",
            "name",
            "slug",
            "description",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "updated_at",
        ]
    
    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError("Organization name too short.")
        return value

    def create(self, validated_data):
        user = self.context["user"]

        organization = Organization.objects.create(
            created_by=user,
            **validated_data
        )

        OrganizationMember.objects.create(
            organization=organization,
            user=user,
            role = OrganizationMember.Role.OWNER
        )

        return organization
    
    def update(self, instance, validated_data):

        
        instance.name = validated_data.get("name",instance.name)
        instance.description = validated_data.get("description",instance.description)

        instance.save()
        return instance
    
class OrganizationDetailSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    projects_count = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "created_at",
            "followers_count",
            "members_count",
            "projects_count",
            "role",
        ]

    def get_followers_count(self, obj):
        return 0

    def get_members_count(self, obj):
        return obj.members.count()

    def get_projects_count(self, obj):
        return obj.workspace.projects.count()

    def get_role(self, obj):
            request = self.context["request"]
            user = request.user
    
            membership = OrganizationMember.objects.filter(organization=obj,user=user,).first()
            return membership.role if membership else None
    
class OrganizationMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True
    )

    avatar = serializers.URLField(
        source="user.avatar",
        read_only=True
    )

    bio = serializers.CharField(
        source="user.bio",
        read_only=True
    )

    github_username = serializers.CharField(
        source="user.github_username",
        read_only=True
    )

    github_profile = serializers.URLField(
        source="user.github_profile",
        read_only=True
    )

    linkedin_profile = serializers.URLField(
        source="user.linkedin_profile",
        read_only=True
    )

    portfolio_website = serializers.URLField(
        source="user.portfolio_website",
        read_only=True
    )

    is_email_verified = serializers.BooleanField(
        source="user.is_email_verified",
        read_only=True
    )

    created_at = serializers.DateTimeField(
        source="user.created_at",
        read_only=True
    )

    class Meta:
        model = OrganizationMember

        fields = [
            "id",
            "username",
            "email",
            "avatar",
            "bio",
            "github_username",
            "github_profile",
            "linkedin_profile",
            "portfolio_website",
            "is_email_verified",
            "role",
            "joined_at",
            "created_at",
        ]

class AddMemberSerializer(serializers.Serializer):
    username = serializers.CharField()
    role = serializers.ChoiceField(choices=OrganizationMember.Role.choices, default=OrganizationMember.Role.MEMBER)

    def validate_username(self, value):
        try:
            user = User.objects.get(username=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
class UpdateMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=OrganizationMember.Role.choices
    )

class OrganizationProjectSummarySerializer(serializers.ModelSerializer):
    ticket_count = serializers.IntegerField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 
            'name', 
            'slug', 
            'is_archived', 
            'ticket_count', 
            'member_count'
        ]