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
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required = False)
    username = serializers.CharField(required = False)
    password = serializers.CharField(required = True)

    def validate(self, attrs):
        email = attrs.get("email")
        username = attrs.get("username")

        # both are missing
        if not email and not username:
            raise serializers.ValidationError("Email or username is required")
        
        if(email and username):
            raise serializers.ValidationError("Use either email or username")
        
        return attrs