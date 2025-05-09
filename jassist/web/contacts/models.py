from django.db import models
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

class Contact(models.Model):
    """
    Model for storing user contacts with basic information.
    Each contact is associated with a specific user.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='contacts'
    )
    name = models.CharField(
        max_length=100,
        help_text="Contact's full name"
    )
    email = models.EmailField(
        blank=True,
        help_text="Contact's email address"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Contact's phone number"
    )
    address = models.TextField(
        blank=True,
        help_text="Contact's physical address"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the contact"
    )
    category = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Optional category for organizing contacts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    def save(self, *args, **kwargs):
        logger.debug(f"Saving contact {self.name} for user: {self.user.username if self.user else 'Unknown'}")
        super().save(*args, **kwargs) 