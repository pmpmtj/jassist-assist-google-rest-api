"""
URL routing for API v1.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.health import health_check
from .views.user import current_user
from .views.drive.config import get_drive_config, update_drive_config
from .views.drive.download import download_file, get_download_status, get_download_history
from .views.transcription.jobs import submit_transcription_job, get_transcription_job_status, get_transcription_result

# Create a router for viewsets
router = DefaultRouter()

# Add viewset routes here as they are created
# Example: router.register('downloads', DownloadViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Health check endpoint
    path('health/', health_check, name='api_health_check'),
    
    # User endpoints
    path('user/current/', current_user, name='api_current_user'),
    
    # Drive endpoints
    path('drive/config/', get_drive_config, name='api_get_drive_config'),
    path('drive/config/update/', update_drive_config, name='api_update_drive_config'),
    path('drive/download/', download_file, name='api_download_file'),
    path('drive/download/<str:download_id>/status/', get_download_status, name='api_download_status'),
    path('drive/history/', get_download_history, name='api_download_history'),
    
    # Transcription endpoints
    path('transcription/jobs/', submit_transcription_job, name='api_submit_transcription_job'),
    path('transcription/jobs/<str:job_id>/', get_transcription_job_status, name='api_get_transcription_job_status'),
    path('transcription/results/<str:job_id>/', get_transcription_result, name='api_transcription_result'),
    
    # Add non-viewset URLs here
] 