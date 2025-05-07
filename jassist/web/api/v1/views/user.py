"""
User API endpoints.
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from api.serializers import BaseModelSerializer
from django.contrib.auth.models import User
from api.common.responses import success_response

logger = logging.getLogger('api')


class UserSerializer(BaseModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
        read_only_fields = ['id', 'is_active']


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Get the current authenticated user's information.
    """
    logger.debug("Current user endpoint called by user: %s", request.user.username)
    
    # Serialize the user and return
    serializer = UserSerializer(request.user)
    return success_response(data=serializer.data) 