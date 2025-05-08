"""
Admin interface for classification models.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ClassificationConfig, 
    ClassificationPrompt, 
    ClassificationMetrics,
    TranscriptionClassificationBatch
)


@admin.register(ClassificationConfig)
class ClassificationConfigAdmin(admin.ModelAdmin):
    """Admin interface for ClassificationConfig model."""
    list_display = ('assistant_name', 'model', 'is_active', 'updated_at')
    list_filter = ('is_active', 'model')
    search_fields = ('assistant_name', 'assistant_id', 'persistent_thread_id')
    readonly_fields = ('created_at', 'updated_at', 'assistant_id', 'persistent_thread_id', 
                      'persistent_thread_created_at')
    fieldsets = (
        ('Basic Settings', {
            'fields': ('assistant_name', 'is_active', 'api_key', 'model')
        }),
        ('Model Parameters', {
            'fields': ('temperature', 'max_tokens', 'top_p', 'frequency_penalty', 
                      'presence_penalty', 'default_response_format')
        }),
        ('Maintenance', {
            'fields': ('save_usage_stats', 'thread_retention_days')
        }),
        ('OpenAI IDs', {
            'fields': ('assistant_id', 'persistent_thread_id', 'persistent_thread_created_at')
        }),
        ('Tools', {
            'fields': ('tools',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ClassificationPrompt)
class ClassificationPromptAdmin(admin.ModelAdmin):
    """Admin interface for ClassificationPrompt model."""
    list_display = ('name', 'is_active', 'updated_at', 'template_preview')
    list_filter = ('is_active',)
    search_fields = ('name', 'template', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def template_preview(self, obj):
        """Show a preview of the template text."""
        if obj.template:
            return format_html("<span title='{}'>{}</span>", 
                              obj.template, obj.template[:50] + ('...' if len(obj.template) > 50 else ''))
        return "-"
    template_preview.short_description = "Template Preview"


@admin.register(ClassificationMetrics)
class ClassificationMetricsAdmin(admin.ModelAdmin):
    """Admin interface for ClassificationMetrics model."""
    list_display = ('id', 'batch_id', 'job_id', 'total_tokens', 'estimated_cost_usd', 
                   'success', 'created_at')
    list_filter = ('success', 'model_used', 'created_at')
    search_fields = ('batch_id', 'job_id', 'error_message')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Identifiers', {
            'fields': ('batch_id', 'job_id')
        }),
        ('Usage', {
            'fields': ('prompt_tokens', 'completion_tokens', 'total_tokens', 
                      'processing_time_ms', 'estimated_cost_usd')
        }),
        ('Status', {
            'fields': ('success', 'error_message', 'model_used')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(TranscriptionClassificationBatch)
class TranscriptionClassificationBatchAdmin(admin.ModelAdmin):
    """Admin interface for TranscriptionClassificationBatch model."""
    list_display = ('batch_id', 'status', 'total_records', 'successful_records', 
                   'failed_records', 'total_tokens', 'total_cost_usd', 'created_at')
    list_filter = ('status', 'created_at', 'dry_run')
    search_fields = ('batch_id', 'error_message')
    readonly_fields = ('created_at', 'updated_at', 'start_time', 'end_time')
    fieldsets = (
        ('Batch Info', {
            'fields': ('batch_id', 'status', 'dry_run')
        }),
        ('Stats', {
            'fields': ('total_records', 'processed_records', 'successful_records', 
                      'failed_records', 'total_tokens', 'total_cost_usd')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'created_at', 'updated_at')
        }),
        ('Errors', {
            'fields': ('error_message',)
        }),
    ) 