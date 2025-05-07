"""
Health check endpoint to verify API functionality.
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from api.common.responses import success_response

logger = logging.getLogger('api')


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint for API status verification.
    """
    logger.debug("Health check endpoint called")
    
    # Return a simple success response
    return success_response(
        data={
            "status": "healthy",
            "api_version": "v1",
            "message": "API is working correctly"
        }
    ) 