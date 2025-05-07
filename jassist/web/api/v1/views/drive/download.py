"""
Google Drive download API endpoints.
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from api.common.responses import success_response, error_response
from jassist.web.download_gdrive.services.download.download_manager import DownloadManager
from jassist.web.download_gdrive.models import DownloadRecord

# Get the logger for the API module
logger = logging.getLogger('api')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def download_file(request):
    """
    Download a specific file from Google Drive.
    """
    logger.debug("Download file endpoint called by user: %s", request.user.username)
    
    # Extract file ID from request
    file_id = request.data.get('file_id')
    
    if not file_id:
        return error_response(
            message="File ID is required",
            error_code="MISSING_FILE_ID",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Initialize the downloader
        downloader = DownloadManager(request.user.id, dry_run=False)
        
        # Attempt to download the file
        result = downloader.run_downloads()
        
        if result.get('success', False):
            return success_response(
                data={'download_id': result.get('download_id'), 'local_path': result.get('local_path')},
                message="File downloaded successfully"
            )
        else:
            return error_response(
                message=result.get('error', "Failed to download file"),
                error_code="DOWNLOAD_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error("Error downloading file: %s", str(e), exc_info=True)
        return error_response(
            message="An error occurred while downloading the file",
            error_code="DOWNLOAD_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error": str(e)}
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_download_status(request, download_id):
    """
    Get the status of a download operation.
    """
    logger.debug("Download status endpoint called by user: %s for download %s", 
                request.user.username, download_id)
    
    try:
        # Initialize the downloader
        downloader = DownloadManager(request.user.id, dry_run=False)
        
        # Get the status
        status_result = downloader.get_download_status(download_id)
        
        return success_response(data=status_result)
        
    except Exception as e:
        logger.error("Error getting download status: %s", str(e), exc_info=True)
        return error_response(
            message="Failed to retrieve download status",
            error_code="STATUS_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error": str(e)}
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_download_history(request):
    """
    Get the user's download history.
    """
    logger.debug("Download history endpoint called by user: %s", request.user.username)
    
    try:
        # Get the user's download records
        records = DownloadRecord.objects.filter(user=request.user).order_by('-downloaded_at')
        
        # Format the records for the response
        history = []
        for record in records:
            history.append({
                'id': record.id,
                'filename': record.filename,
                'source_id': record.source_id,
                'source_folder': record.source_folder,
                'local_path': record.local_path,
                'downloaded_at': record.downloaded_at.isoformat(),
                'deleted_from_drive': record.deleted_from_drive,
                'file_size': record.file_size
            })
        
        return success_response(data={"history": history})
        
    except Exception as e:
        logger.error("Error retrieving download history: %s", str(e), exc_info=True)
        return error_response(
            message="Failed to retrieve download history",
            error_code="HISTORY_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error": str(e)}
        ) 