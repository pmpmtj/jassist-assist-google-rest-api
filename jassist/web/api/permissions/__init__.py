"""
Custom permissions for the API.
"""
from .base import IsAuthenticated, IsAdminUser, IsOwnerOrReadOnly

__all__ = ['IsAuthenticated', 'IsAdminUser', 'IsOwnerOrReadOnly'] 