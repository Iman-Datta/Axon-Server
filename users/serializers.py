import re # Automata
from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_email(self, value):
        if User.objects.filter(email = value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username = value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],

            is_username_set=True,

            is_email_verified=False,
            is_profile_completed=False
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
            raise serializers.ValidationError(
                "Invalid username format."
            )

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