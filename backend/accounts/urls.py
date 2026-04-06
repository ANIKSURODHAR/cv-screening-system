from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # Profile
    path("profile/", views.ProfileView.as_view(), name="profile"),
    # Admin
    path("users/", views.AdminUserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", views.AdminUserDeleteView.as_view(), name="user-delete"),
    path("stats/", views.admin_stats, name="admin-stats"),
]
