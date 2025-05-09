from django.db import models
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

class ManualEntry(models.Model):
    """
    Model for storing manual text entries made by users.
    """
    CLASSIFICATION_CHOICES = [
        ('diary', 'Diary'),
        # Add more classifications here as needed
    ]
    
    content = models.TextField(
        help_text="Enter your text here (minimum 15 characters)"
    )
    classification = models.CharField(
        max_length=50, 
        choices=CLASSIFICATION_CHOICES,
        default='diary'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='manual_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Manual Entry"
        verbose_name_plural = "Manual Entries"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.classification} entry by {self.user.username} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        logger.debug(f"Saving manual entry for user: {self.user.username if self.user else 'Unknown'}")
        super().save(*args, **kwargs)
