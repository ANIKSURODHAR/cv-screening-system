"""
Custom permissions for role-based access control.
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Only admin/superuser can access."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_admin_user
        )


class IsRecruiter(BasePermission):
    """Only recruiters can access."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_recruiter
        )


class IsCandidate(BasePermission):
    """Only candidates can access."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_candidate
        )


class IsAdminOrRecruiter(BasePermission):
    """Admin or recruiter can access."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_admin_user or request.user.is_recruiter)
        )


class IsOwnerOrAdmin(BasePermission):
    """Object owner or admin can access."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin_user:
            return True
        # Check various owner fields
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "recruiter"):
            return obj.recruiter == request.user
        if hasattr(obj, "candidate"):
            return obj.candidate == request.user
        return False
