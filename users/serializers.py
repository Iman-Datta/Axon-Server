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
            is_email_verified=False,
            is_profile_completed=False
        )

        user.set_password(validated_data["password"])

        user.save()
        return user