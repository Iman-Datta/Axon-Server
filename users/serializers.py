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