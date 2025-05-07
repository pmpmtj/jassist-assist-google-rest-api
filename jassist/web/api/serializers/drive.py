"""
Serializers for Google Drive API endpoints.
"""
from rest_framework import serializers
from .base import BaseModelSerializer, BaseSerializer

from jassist.web.download_gdrive.models import UserDriveConfig, GlobalDriveConfig


class DriveConfigSerializer(BaseModelSerializer):
    """
    Serializer for the combined Drive configuration.
    Used for GET operations.
    """
    include_extensions = serializers.ListField(
        child=serializers.CharField(), source='global_config.include_extensions'
    )
    delete_after_download = serializers.BooleanField(source='global_config.delete_after_download')
    add_timestamp = serializers.BooleanField(source='global_config.add_timestamp')
    timestamp_format = serializers.CharField(source='global_config.timestamp_format')
    target_folders = serializers.ListField(child=serializers.CharField())
    download_schedule = serializers.CharField(required=False, allow_null=True)
    is_active = serializers.BooleanField()
    
    class Meta:
        model = UserDriveConfig
        fields = [
            'include_extensions', 'delete_after_download', 'add_timestamp',
            'timestamp_format', 'target_folders', 'download_schedule', 
            'is_active', 'last_run'
        ]
        read_only_fields = ['last_run']
    
    def to_representation(self, instance):
        """
        Transform the UserDriveConfig instance into a combined representation
        with global config settings.
        """
        global_config = GlobalDriveConfig.get_config()
        # Add global_config to the instance temporarily for serializing
        instance.global_config = global_config
        return super().to_representation(instance)


class DriveConfigUpdateSerializer(BaseSerializer):
    """
    Serializer for updating Drive configuration.
    Used for POST operations.
    """
    target_folders = serializers.ListField(
        child=serializers.CharField(), 
        required=False
    )
    download_schedule = serializers.CharField(
        required=False, 
        allow_null=True, 
        allow_blank=True
    )
    is_active = serializers.BooleanField(required=False)
    
    def validate_download_schedule(self, value):
        """Validate the cron format of the download schedule."""
        if not value:
            return value
            
        try:
            from croniter import croniter
            if not croniter.is_valid(value):
                raise serializers.ValidationError("Invalid cron format")
        except ImportError:
            # If croniter is not available, we can't validate the cron format
            # but we'll still accept the value
            pass
            
        return value
    
    def update(self, instance, validated_data):
        """Update the UserDriveConfig instance."""
        if 'target_folders' in validated_data:
            instance.target_folders = validated_data['target_folders']
            
        if 'download_schedule' in validated_data:
            instance.download_schedule = validated_data['download_schedule']
            
        if 'is_active' in validated_data:
            instance.is_active = validated_data['is_active']
            
        instance.save()
        return instance 