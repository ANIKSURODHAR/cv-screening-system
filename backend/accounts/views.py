"""
Views for authentication: register, login (JWT), profile, admin user management.
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from .serializers import RegisterSerializer, UserSerializer, UserListSerializer
from .permissions import IsAdmin

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — Register as recruiter or candidate."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": f"Registration successful as {user.role}.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT /api/auth/profile/ — View/update own profile."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class AdminUserListView(generics.ListAPIView):
    """GET /api/auth/users/ — Admin: list all users."""

    serializer_class = UserListSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["role"]
    search_fields = ["username", "email", "first_name", "last_name"]

    def get_queryset(self):
        return User.objects.all()


class AdminUserDeleteView(generics.DestroyAPIView):
    """DELETE /api/auth/users/<id>/ — Admin: remove a user."""

    serializer_class = UserListSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.all()

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.is_superuser:
            return Response(
                {"error": "Cannot delete a superuser."},
                status=status.HTTP_403_FORBIDDEN,
            )
        user.delete()
        return Response(
            {"message": "User removed successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_stats(request):
    """GET /api/auth/stats/ — Admin dashboard stats."""
    from jobs.models import Job
    from candidates.models import Application

    return Response({
        "total_users": User.objects.count(),
        "recruiters": User.objects.filter(role="recruiter").count(),
        "candidates": User.objects.filter(role="candidate").count(),
        "total_jobs": Job.objects.count(),
        "pending_jobs": Job.objects.filter(status="pending").count(),
        "approved_jobs": Job.objects.filter(status="approved").count(),
        "total_applications": Application.objects.count(),
    })
