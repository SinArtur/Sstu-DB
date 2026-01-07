"""
Custom permission classes.
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Permission check for admin role."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsModeratorOrAdmin(permissions.BasePermission):
    """Permission check for moderator or admin role."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_moderate()









