"""
Base permissions for API endpoints.
"""
from rest_framework import permissions


# Re-export DRF's built-in permission classes
IsAuthenticated = permissions.IsAuthenticated
IsAdminUser = permissions.IsAdminUser


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Read operations are allowed to any authenticated user.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the owner
        return obj.user == request.user
        

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Only allow access to the owner
        return obj.user == request.user
        
        
class IsResourceOwner(permissions.BasePermission):
    """
    Permission to only allow owners of a resource to access it.
    Flexible with configurable owner field name.
    """
    owner_field = 'owner'  # Default owner field
    
    def has_object_permission(self, request, view, obj):
        if hasattr(view, 'owner_field'):
            # Allow views to specify different owner field
            owner_field = view.owner_field
        else:
            owner_field = self.owner_field
            
        # Check if object has the specified owner field
        if not hasattr(obj, owner_field):
            return False
            
        # Compare the owner with the request user
        owner = getattr(obj, owner_field)
        return owner == request.user 