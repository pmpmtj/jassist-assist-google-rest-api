"""
Serializers for Transcription API endpoints.
"""
from rest_framework import serializers
from .base import BaseModelSerializer, BaseSerializer

from jassist.web.download_gdrive.models import TranscriptionJob


class TranscriptionJobSerializer(BaseModelSerializer):
    """
    Serializer for transcription job data.
    Used for job creation and detailed responses.
    """
    class Meta:
        model = TranscriptionJob
        fields = [
            'id', 'file_id', 'file_name', 'status', 'language', 
            'model', 'progress', 'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'status', 'progress', 'created_at', 
            'completed_at', 'file_name'
        ]
    
    def create(self, validated_data):
        """
        Create a new TranscriptionJob instance.
        The user is automatically set from the request context.
        """
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Check if a file name was provided
        if not validated_data.get('file_name'):
            # In a real implementation, we might fetch the file name from Drive
            validated_data['file_name'] = f"File {validated_data['file_id']}"
            
        return super().create(validated_data)
        

class TranscriptionJobStatusSerializer(BaseModelSerializer):
    """
    Serializer for transcription job status updates and responses.
    """
    result_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TranscriptionJob
        fields = [
            'id', 'status', 'progress', 'error_message',
            'updated_at', 'completed_at', 'result_url'
        ]
        read_only_fields = fields
    
    def get_result_url(self, obj):
        """
        Generate URL to the transcription results if the job is completed.
        """
        if obj.status == 'completed' and obj.result_path:
            from django.urls import reverse
            # This assumes you have a URL pattern named 'api_transcription_result' 
            # that takes a job_id parameter
            return reverse('api_transcription_result', kwargs={'job_id': obj.id})
        return None 