"""
Models for classification functionality.

This module defines database models for storing OpenAI Assistant classification
configuration, prompts, and usage metrics.
"""

from django.db import models
from django.utils import timezone
import json
import logging
import uuid

logger = logging.getLogger(__name__)


def generate_uuid():
    """Generate a UUID string for batch IDs."""
    return str(uuid.uuid4())


class ClassificationConfig(models.Model):
    """
    Configuration for OpenAI Assistant used for classification.
    Replaces classification_assistant_config.json
    """
    assistant_name = models.CharField(max_length=100, default="Classification Assistant")
    api_key = models.CharField(max_length=255, blank=True)
    model = models.CharField(max_length=50, default="gpt-4o")
    temperature = models.FloatField(default=0.2)
    max_tokens = models.IntegerField(default=1000)
    top_p = models.FloatField(default=1.0)
    frequency_penalty = models.FloatField(default=0.0)
    presence_penalty = models.FloatField(default=0.0)
    save_usage_stats = models.BooleanField(default=True)
    thread_retention_days = models.IntegerField(default=30)
    default_response_format = models.CharField(max_length=20, default="json")
    tools = models.JSONField(default=list)
    
    # Thread and assistant IDs
    assistant_id = models.CharField(max_length=100, blank=True)
    persistent_thread_id = models.CharField(max_length=100, blank=True)
    persistent_thread_created_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Classification Configuration"
        verbose_name_plural = "Classification Configuration"
    
    def __str__(self):
        return f"{self.assistant_name} Config (Updated: {self.updated_at.strftime('%Y-%m-%d')})"
    
    @classmethod
    def get_active_config(cls):
        """Get the active configuration or create a default one if none exists."""
        config, created = cls.objects.get_or_create(
            is_active=True,
            defaults={
                'tools': [{'type': 'code_interpreter'}]
            }
        )
        if created:
            logger.info("Created default classification configuration")
        return config

    def to_dict(self):
        """Convert the configuration to a dictionary for the OpenAI client."""
        return {
            "assistant_name": self.assistant_name,
            "api_key": self.api_key,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "save_usage_stats": self.save_usage_stats,
            "thread_retention_days": self.thread_retention_days,
            "default_response_format": self.default_response_format,
            "tools": self.tools,
            "assistant_id": self.assistant_id,
            "thread_id_classification_assistant_persistent": self.persistent_thread_id,
            "thread_id_classification_assistant_persistent_created_at": 
                self.persistent_thread_created_at.isoformat() if self.persistent_thread_created_at else ""
        }

    def update_assistant_id(self, assistant_id):
        """Update the assistant ID and save the model."""
        self.assistant_id = assistant_id
        self.save(update_fields=['assistant_id', 'updated_at'])
        logger.debug(f"Updated assistant ID to {assistant_id}")

    def update_thread_id(self, thread_id):
        """Update the persistent thread ID and save the model."""
        self.persistent_thread_id = thread_id
        self.persistent_thread_created_at = timezone.now()
        self.save(update_fields=['persistent_thread_id', 'persistent_thread_created_at', 'updated_at'])
        logger.debug(f"Updated persistent thread ID to {thread_id}")


class ClassificationPrompt(models.Model):
    """
    Prompt templates for classification.
    Replaces prompts.yaml
    """
    name = models.CharField(max_length=100, unique=True)
    template = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Classification Prompt"
        verbose_name_plural = "Classification Prompts"
    
    def __str__(self):
        return f"Prompt: {self.name}"
    
    @classmethod
    def get_prompt(cls, name):
        """Get a specific prompt by name."""
        try:
            return cls.objects.get(name=name, is_active=True)
        except cls.DoesNotExist:
            logger.error(f"Prompt '{name}' not found or inactive")
            return None


class ClassificationMetrics(models.Model):
    """
    Metrics for tracking classification API usage and costs.
    """
    batch_id = models.CharField(max_length=100, blank=True)
    job_id = models.IntegerField(null=True, blank=True)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    processing_time_ms = models.IntegerField(default=0)
    estimated_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    model_used = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Classification Metric"
        verbose_name_plural = "Classification Metrics"
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['batch_id']),
            models.Index(fields=['job_id']),
        ]
    
    def __str__(self):
        return f"Metric: {self.batch_id or self.job_id} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"


class TranscriptionClassificationBatch(models.Model):
    """
    Records batches of transcription classification processing.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    batch_id = models.CharField(max_length=100, unique=True, default=generate_uuid)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    successful_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    total_tokens = models.IntegerField(default=0)
    total_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    error_message = models.TextField(blank=True)
    dry_run = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Transcription Classification Batch"
        verbose_name_plural = "Transcription Classification Batches"
        indexes = [
            models.Index(fields=['batch_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Batch: {self.batch_id} ({self.status})"
    
    def start_processing(self):
        """Mark batch as processing and set start time."""
        self.status = 'processing'
        self.start_time = timezone.now()
        self.save(update_fields=['status', 'start_time', 'updated_at'])
        logger.info(f"Started processing batch {self.batch_id}")
    
    def complete_processing(self):
        """Mark batch as completed and set end time."""
        self.status = 'completed'
        self.end_time = timezone.now()
        self.save(update_fields=['status', 'end_time', 'updated_at'])
        
        duration = self.end_time - self.start_time
        logger.info(
            f"Completed batch {self.batch_id}: {self.successful_records}/{self.total_records} "
            f"successful in {duration.total_seconds():.2f}s"
        )
    
    def fail_processing(self, error_message):
        """Mark batch as failed with error message."""
        self.status = 'failed'
        self.error_message = error_message
        self.end_time = timezone.now()
        self.save(update_fields=['status', 'error_message', 'end_time', 'updated_at'])
        logger.error(f"Batch {self.batch_id} failed: {error_message}")
    
    def update_metrics(self, tokens=0, cost=0.0, processed=1, successful=1, failed=0):
        """Update batch metrics."""
        self.total_tokens += tokens
        self.total_cost_usd += cost
        self.processed_records += processed
        self.successful_records += successful
        self.failed_records += failed
        self.save(update_fields=[
            'total_tokens', 'total_cost_usd', 'processed_records', 
            'successful_records', 'failed_records', 'updated_at'
        ]) 