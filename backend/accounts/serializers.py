"""
Serializers for user registration, login, and profile.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Register a new user (recruiter or candidate)."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "password", "password_confirm",
            "first_name", "last_name", "role", "company", "phone",
        ]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_role(self, value):
        # Only allow recruiter and candidate registration
        if value not in [User.Role.RECRUITER, User.Role.CANDIDATE]:
            raise serializers.ValidationError(
                "You can only register as a recruiter or candidate."
            )
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serialize user profile data."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "full_name", "role", "company", "phone", "bio",
            "created_at",
        ]
        read_only_fields = ["id", "role", "created_at"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for lists."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "company", "created_at"]
