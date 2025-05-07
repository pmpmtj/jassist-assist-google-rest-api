"""
Transcription jobs API endpoints.
"""
import logging
import threading
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from api.serializers import TranscriptionJobSerializer, TranscriptionJobStatusSerializer
from api.common.responses import success_response, error_response
from jassist.web.download_gdrive.models import TranscriptionJob
from jassist.web.download_gdrive.services.transcription.transcription_manager import TranscriptionManager
from jassist.web.download_gdrive.services.download.download_manager import DownloadManager

# Get the logger for the API module
logger = logging.getLogger('api')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_transcription_job(request):
    """
    Submit a new transcription job.
    """
    logger.debug("Submit transcription job endpoint called by user: %s", request.user.username)
    
    # Use our model serializer to validate the input data
    serializer = TranscriptionJobSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        try:
            # Create a new job
            job = serializer.save()
            
            # Start the transcription process in the background
            def process_transcription():
                try:
                    # Update job status to processing
                    job.status = 'processing'
                    job.save()
                    
                    # Initialize transcription service
                    transcription_service = TranscriptionManager(request.user.id)
                    
                    # Get file path from download record or download the file if needed
                    local_path = None
                    if job.download_record:
                        local_path = job.download_record.local_path
                    else:
                        # We need to download the file first
                        downloader = DownloadManager(request.user.id)
                        download_result = downloader.download_specific_file(job.file_id)
                        
                        if download_result.get('success', False):
                            local_path = download_result.get('local_path')
                            
                            # Update job with file name if it wasn't provided
                            if not job.file_name:
                                job.file_name = download_result.get('file_name', f"File {job.file_id}")
                                job.save()
                        else:
                            raise Exception(f"Failed to download file: {download_result.get('error')}")
                    
                    if not local_path:
                        raise Exception("Could not determine file path for transcription")
                    
                    # Process the transcription
                    result = transcription_service.transcribe_file(local_path)
                    
                    if result.get('success', False):
                        # Update job with results
                        job.status = 'completed'
                        job.progress = 100
                        job.completed_at = timezone.now()
                        job.result_path = result.get('output_file')
                        job.word_count = len(result.get('text', '').split())
                        job.duration_seconds = result.get('duration', 0)
                        job.save()
                        logger.info(f"Transcription job {job.id} completed successfully")
                    else:
                        # Handle failure
                        job.status = 'failed'
                        job.error_message = result.get('error', 'Unknown error during transcription')
                        job.save()
                        logger.error(f"Transcription job {job.id} failed: {job.error_message}")
                
                except Exception as e:
                    # Handle any exceptions
                    logger.error(f"Error in transcription thread for job {job.id}: {str(e)}", exc_info=True)
                    job.status = 'failed'
                    job.error_message = str(e)
                    job.save()
            
            # Start transcription in a background thread
            thread = threading.Thread(target=process_transcription)
            thread.daemon = True
            thread.start()
            
            # Return the job data
            return success_response(
                data=serializer.data,
                message="Transcription job submitted successfully"
            )
        except Exception as e:
            logger.error("Error creating transcription job: %s", str(e), exc_info=True)
            return error_response(
                message="Failed to submit transcription job",
                error_code="TRANSCRIPTION_JOB_CREATION_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={"error": str(e)}
            )
    else:
        return error_response(
            message="Invalid transcription job data",
            error_code="TRANSCRIPTION_JOB_VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=serializer.errors
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transcription_job_status(request, job_id):
    """
    Get the status of a transcription job.
    """
    logger.debug("Get transcription job status endpoint called by user: %s for job %s", 
                request.user.username, job_id)
    
    try:
        # Fetch the job, ensuring it belongs to the current user
        job = TranscriptionJob.objects.get(id=job_id, user=request.user)
        
        # Serialize and return the job status
        serializer = TranscriptionJobStatusSerializer(job)
        return success_response(data=serializer.data)
        
    except TranscriptionJob.DoesNotExist:
        logger.warning("Transcription job %s not found for user %s", job_id, request.user.username)
        return error_response(
            message="Transcription job not found",
            error_code="TRANSCRIPTION_JOB_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error("Error getting job status for job %s: %s", job_id, str(e))
        return error_response(
            message="Failed to get transcription job status",
            error_code="TRANSCRIPTION_JOB_STATUS_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error": str(e)}
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transcription_result(request, job_id):
    """
    Get the results of a completed transcription job.
    """
    logger.debug("Get transcription result endpoint called by user: %s for job %s", 
                request.user.username, job_id)
    
    try:
        # Fetch the job, ensuring it belongs to the current user and is completed
        job = TranscriptionJob.objects.get(
            id=job_id, 
            user=request.user,
            status='completed'
        )
        
        if not job.result_path:
            return error_response(
                message="Transcription results not available",
                error_code="TRANSCRIPTION_RESULTS_NOT_AVAILABLE",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Read the actual transcription file
        import json
        import os
        from pathlib import Path
        
        result_path = Path(job.result_path)
        
        if not os.path.exists(result_path):
            logger.error(f"Transcription result file not found: {result_path}")
            return error_response(
                message="Transcription result file not found",
                error_code="TRANSCRIPTION_FILE_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Try to read as JSON first
            if result_path.suffix.lower() == '.json':
                with open(result_path, 'r') as f:
                    transcript_content = json.load(f)
                    
                # Extract text from JSON if needed
                if isinstance(transcript_content, dict) and 'text' in transcript_content:
                    transcript_text = transcript_content['text']
                else:
                    transcript_text = json.dumps(transcript_content)
            else:
                # Read as plain text
                with open(result_path, 'r') as f:
                    transcript_text = f.read()
        except Exception as e:
            logger.error(f"Error reading transcription file {result_path}: {str(e)}", exc_info=True)
            return error_response(
                message="Error reading transcription file",
                error_code="TRANSCRIPTION_FILE_READ_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={"error": str(e)}
            )
        
        # Return the actual transcription data
        result_data = {
            "job_id": job.id,
            "file_name": job.file_name,
            "transcript": transcript_text,
            "word_count": job.word_count,
            "duration_seconds": job.duration_seconds,
            "language": job.language,
            "model": job.model,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
        
        return success_response(data=result_data)
        
    except TranscriptionJob.DoesNotExist:
        logger.warning("Completed transcription job %s not found for user %s", 
                      job_id, request.user.username)
        return error_response(
            message="Completed transcription job not found",
            error_code="TRANSCRIPTION_JOB_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error("Error getting transcription results for job %s: %s", job_id, str(e), exc_info=True)
        return error_response(
            message="Failed to get transcription results",
            error_code="TRANSCRIPTION_RESULTS_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error": str(e)}
        ) 