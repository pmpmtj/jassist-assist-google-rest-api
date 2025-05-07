"""
Google Drive configuration API endpoints.
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from api.common.responses import success_response, error_response
from api.serializers import DriveConfigSerializer, DriveConfigUpdateSerializer
from jassist.web.download_gdrive.models import UserDriveConfig, GlobalDriveConfig

# Get the logger for the API module
logger = logging.getLogger('api')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_drive_config(request):
    """
    Get the current user's Google Drive configuration.
    """
    logger.debug("Drive config endpoint called by user: %s", request.user.username)
    
    try:
        # Get or create user config
        user_config, created = UserDriveConfig.objects.get_or_create(
            user=request.user,
            defaults={
                'target_folders': [],
                'is_active': True
            }
        )
        
        if created:
            logger.info("Created new drive config for user: %s", request.user.username)
        
        # Use the serializer to format the response
        serializer = DriveConfigSerializer(user_config)
        return success_response(data=serializer.data)
    
    except Exception as e:
        logger.error("Error retrieving drive config: %s", str(e))
        return error_response(
            message="Failed to retrieve drive configuration",
            error_code="DRIVE_CONFIG_RETRIEVAL_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error": str(e)}
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_drive_config(request):
    """
    Update the current user's Google Drive configuration.
    """
    logger.debug("Update drive config endpoint called by user: %s", request.user.username)
    
    try:
        # Get existing user config or create default
        user_config, created = UserDriveConfig.objects.get_or_create(
            user=request.user,
            defaults={
                'target_folders': [],
                'is_active': True
            }
        )
        
        # Use the serializer to validate and update
        serializer = DriveConfigUpdateSerializer(data=request.data)
        if serializer.is_valid():
            # Update the user config with validated data
            updated_config = serializer.update(user_config, serializer.validated_data)
            
            # Return the updated config
            response_serializer = DriveConfigSerializer(updated_config)
            return success_response(
                data=response_serializer.data,
                message="Drive configuration updated successfully"
            )
        else:
            # Return validation errors
            return error_response(
                message="Invalid drive configuration data",
                error_code="DRIVE_CONFIG_VALIDATION_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors
            )
    
    except Exception as e:
        logger.error("Error updating drive config: %s", str(e))
        return error_response(
            message="Failed to update drive configuration",
            error_code="DRIVE_CONFIG_UPDATE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error": str(e)}
        ) 