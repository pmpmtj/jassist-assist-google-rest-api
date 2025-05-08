"""
Admin interface for Google Drive download models.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    GlobalDriveConfig, 
    UserDriveConfig, 
    DownloadRecord,
    TranscriptionGlobalConfig,
    UserTranscriptionConfig,
    TranscriptionJob
)

@admin.register(GlobalDriveConfig)
class GlobalDriveConfigAdmin(admin.ModelAdmin):
    """Admin interface for global drive configuration."""
    list_display = ('id', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('File Types', {
            'fields': ('include_extensions',),
        }),
        ('Download Behavior', {
            'fields': ('delete_after_download', 'add_timestamp', 'timestamp_format'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not GlobalDriveConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False

@admin.register(UserDriveConfig)
class UserDriveConfigAdmin(admin.ModelAdmin):
    """Admin interface for user drive configuration."""
    list_display = ('user', 'is_active', 'last_run', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User', {
            'fields': ('user',),
        }),
        ('Configuration', {
            'fields': ('target_folders', 'download_schedule', 'is_active'),
        }),
        ('Status', {
            'fields': ('last_run',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(DownloadRecord)
class DownloadRecordAdmin(admin.ModelAdmin):
    """Admin interface for download records."""
    list_display = ('filename', 'user', 'downloaded_at', 'file_size', 'deleted_from_drive')
    list_filter = ('downloaded_at', 'deleted_from_drive', 'user')
    search_fields = ('filename', 'user__username', 'source_folder')
    readonly_fields = ('downloaded_at',)
    fieldsets = (
        ('File', {
            'fields': ('filename', 'source_id', 'source_folder', 'local_path', 'file_size'),
        }),
        ('Status', {
            'fields': ('deleted_from_drive',),
        }),
        ('User', {
            'fields': ('user',),
        }),
        ('Metadata', {
            'fields': ('downloaded_at',),
        }),
    )

@admin.register(TranscriptionGlobalConfig)
class TranscriptionGlobalConfigAdmin(admin.ModelAdmin):
    """Admin interface for global transcription configuration."""
    list_display = ('id', 'default_model', 'response_format', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Model Settings', {
            'fields': ('default_model', 'response_format', 'default_prompt'),
        }),
        ('Cost Management', {
            'fields': ('cost_management',),
        }),
        ('File Settings', {
            'fields': ('timestamp_format',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not TranscriptionGlobalConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False

@admin.register(UserTranscriptionConfig)
class UserTranscriptionConfigAdmin(admin.ModelAdmin):
    """Admin interface for user transcription configuration."""
    list_display = ('user', 'language', 'is_active', 'updated_at')
    list_filter = ('is_active', 'language')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User', {
            'fields': ('user',),
        }),
        ('Configuration', {
            'fields': ('api_key', 'language', 'is_active'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(TranscriptionJob)
class TranscriptionJobAdmin(admin.ModelAdmin):
    """Admin interface for TranscriptionJob model."""
    list_display = ('id', 'user', 'file_name', 'status', 'progress', 'word_count', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at', 'completed_at')
    search_fields = ('file_name', 'file_id', 'user__username', 'transcript_content', 'transcript_summary')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'file_id', 'file_name', 'download_record')
        }),
        ('Status', {
            'fields': ('status', 'progress', 'error_message')
        }),
        ('Configuration', {
            'fields': ('language', 'model', 'result_format')
        }),
        ('Results', {
            'fields': ('result_path', 'word_count', 'duration_seconds', 'transcript_summary', 'transcript_content')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ['completed', 'failed', 'canceled']:
            # Make more fields read-only once the job is in a terminal state
            return self.readonly_fields + ('status', 'progress', 'language', 'model', 'transcript_content', 'transcript_summary')
        return self.readonly_fields 