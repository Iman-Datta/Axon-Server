import re # Automata
from urllib.parse import urlparse
from rest_framework import serializers
from .models import User

from tickets.models import Ticket
from organizations.models import OrganizationMember

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
        ]

    def validate_email(self, value):
        value = value.strip().lower()

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate_username(self, value):
        # Reuse the common username validation
        value = UsernameSerializer().validate_username(value)

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
            is_username_set=True,
            is_email_verified=False,
            is_profile_completed=False,
        )

        user.set_password(validated_data["password"])
        user.save()
        return user
    
class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True,max_length=255,trim_whitespace=True)
    password = serializers.CharField(required=True,write_only=True,style={"input_type": "password"})

    def validate_identifier(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Username or email is required."
            )

        return value

    def validate_password(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Password is required."
            )

        return value

class UsernameSerializer(serializers.Serializer):

    username = serializers.CharField(min_length=4,max_length=30)

    def validate_username(self, value):
        value = value.strip().lower()

        pattern = r"^[a-z][a-z0-9_]*[a-z0-9]$"
        if not re.match(pattern, value):
            raise serializers.ValidationError("Invalid username format.")
        return value

class UsernameUpdateSerializer(UsernameSerializer):
    def validate_username(self, value): # OOPS
        value = super().validate_username(value)

        user = self.context["user"]

        if User.objects.filter(username__iexact = value).exclude(id=user.id).exists(): # case insensitive
            raise serializers.ValidationError("Username already exists.")
        return value

class EmailOTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower().strip()

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

class EmailOTPVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6,max_length=6)

class CompleteProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "bio",
            "linkedin_profile",
            "portfolio_website",
        ]

    def validate_first_name(self, value):

        value = value.strip()
        pattern = r"^[A-Za-z][A-Za-z\s'-]{1,49}$"

        if not re.match(pattern, value):
            raise serializers.ValidationError("Invalid first name.")
        
        return value
    
    def validate_last_name(self, value):

        value = value.strip()
        pattern = r"^[A-Za-z][A-Za-z\s'-]{1,49}$"

        if not re.match(pattern, value):
            raise serializers.ValidationError("Invalid last name.")
        
        return value
    
    def validate_bio(self, value):

        value = value.strip()
        value = re.sub(r"\s+", " ",value)

        if len(value) > 300:
            raise serializers.ValidationError("Bio cannot exceed 300 characters.")

        return value
    
    def validate_linkedin_profile(self, value):
        if not value:
            return value
        
        value = value.strip()
        parsed_url = urlparse(value)
        if parsed_url.scheme not in ["http","https"]:
            raise serializers.ValidationError("Invalid LinkedIn URL.")
        
        allowed_domains = ["linkedin.com", "www.linkedin.com"]
        if parsed_url.netloc.lower() not in allowed_domains:
            raise serializers.ValidationError("Only LinkedIn profile URL allowed.")
        
        return value
    
    def validate_portfolio_website(self, value):

        if not value:
            return value

        value = value.strip()
        parsed_url = urlparse(value)

        if parsed_url.scheme not in ["http","https"]:
            raise serializers.ValidationError("Invalid portfolio URL.")

        return value

    def update(self, instance, validated_data):
        update_fields = []
        for field, value in validated_data.items():
            setattr(instance, field, value)
            update_fields.append(field)

        instance.is_profile_completed = True
        update_fields.append("is_profile_completed")

        if update_fields:
            instance.save(update_fields=update_fields)

        return instance

class PublicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "github_username",
            "github_profile",
            "linkedin_profile",
            "portfolio_website",
        ]

class MeSerializer(serializers.ModelSerializer):
    is_github_connected = serializers.SerializerMethodField()
    is_password = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_password",

            "first_name",
            "last_name",

            "avatar",
            "bio",
            "location",

            "is_profile_completed",
            "is_username_set",
            "is_email_verified",

            "github_username",
            "github_profile",
            "is_github_connected",

            "linkedin_profile",
            "portfolio_website",

            "created_at",
        ]

    def get_is_github_connected(self, obj):
        return bool(obj.github_id)
    def get_is_password(self, obj):
        return bool(obj.password)

class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "location",
            "linkedin_profile",
            "portfolio_website",
        ]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "avatar": {"required": False},
            "bio": {"required": False},
            "location": {"required": False},
            "linkedin_profile": {"required": False},
            "portfolio_website": {"required": False},
        }

class ProfileTicketSerializer(serializers.ModelSerializer):
    epic_name = serializers.CharField(source="epic.name", read_only=True, default=None)
    epic_color = serializers.CharField(source="epic.color", read_only=True, default=None)
    project_name = serializers.CharField(source="project.name", read_only=True)
    project_slug = serializers.CharField(source="project.slug", read_only=True)
    
    # Dynamically extract workspace slug & name from the Workspace model
    workspace_slug = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()
    is_organization = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "ticket_number",
            "title",
            "status",
            "kanban_column",
            "priority",
            "type",
            "story_points",
            "project_name",
            "project_slug",
            "workspace_slug",
            "workspace_name",
            "is_organization",
            "epic_name",
            "epic_color",
            "updated_at",
        ]

    def get_workspace_slug(self, obj):
        workspace = obj.project.workspace
        # Check if workspace has an organization attached, otherwise fallback to owner's username
        if hasattr(workspace, "organization") and workspace.organization:
            return workspace.organization.slug
        if hasattr(workspace, "owner") and workspace.owner:
            return workspace.owner.username
        return "personal"

    def get_workspace_name(self, obj):
        workspace = obj.project.workspace
        if hasattr(workspace, "organization") and workspace.organization:
            return workspace.organization.name
        if hasattr(workspace, "owner") and workspace.owner:
            return workspace.owner.username
        return "Personal"

    def get_is_organization(self, obj):
        workspace = obj.project.workspace
        return bool(hasattr(workspace, "organization") and workspace.organization)

class ProfileOrganizationSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="organization.id")
    name = serializers.ReadOnlyField(source="organization.name")
    slug = serializers.ReadOnlyField(source="organization.slug")
    description = serializers.ReadOnlyField(source="organization.description")

    class Meta:
        model = OrganizationMember
        fields = ["id", "name", "slug", "description", "role", "joined_at"]


class UserProfileOverviewSerializer(serializers.Serializer):
    assigned_tickets = ProfileTicketSerializer(many=True)
    organizations = ProfileOrganizationSerializer(many=True)
    metrics = serializers.DictField()
    
class ProfileOrganizationSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="organization.id")
    name = serializers.ReadOnlyField(source="organization.name")
    slug = serializers.ReadOnlyField(source="organization.slug")
    description = serializers.ReadOnlyField(source="organization.description")

    class Meta:
        model = OrganizationMember
        fields = ["id", "name", "slug", "description", "role", "joined_at"]


class UserProfileOverviewSerializer(serializers.Serializer):
    assigned_tickets = ProfileTicketSerializer(many=True)
    organizations = ProfileOrganizationSerializer(many=True)
    metrics = serializers.DictField()

class MyWorkTicketSerializer(serializers.ModelSerializer):
    epic_name = serializers.CharField(source="epic.name", read_only=True, default=None)
    epic_color = serializers.CharField(source="epic.color", read_only=True, default=None)
    project_name = serializers.CharField(source="project.name", read_only=True)
    project_slug = serializers.CharField(source="project.slug", read_only=True)
    
    workspace_slug = serializers.SerializerMethodField()
    workspace_name = serializers.SerializerMethodField()
    is_organization = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "ticket_number",
            "title",
            "status",
            "kanban_column",
            "priority",
            "type",
            "story_points",
            "project_name",
            "project_slug",
            "workspace_slug",
            "workspace_name",
            "is_organization",
            "epic_name",
            "epic_color",
            "updated_at",
            "due_date",
        ]

    def get_workspace_slug(self, obj):
        workspace = obj.project.workspace
        if hasattr(workspace, "organization") and workspace.organization:
            return workspace.organization.slug
        if hasattr(workspace, "owner") and workspace.owner:
            return workspace.owner.username
        return "personal"

    def get_workspace_name(self, obj):
        workspace = obj.project.workspace
        if hasattr(workspace, "organization") and workspace.organization:
            return workspace.organization.name
        if hasattr(workspace, "owner") and workspace.owner:
            return workspace.owner.username
        return "Personal"

    def get_is_organization(self, obj):
        workspace = obj.project.workspace
        return bool(hasattr(workspace, "organization") and workspace.organization)

class ForgotPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=6, write_only=True)