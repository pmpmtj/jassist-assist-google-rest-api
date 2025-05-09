from django.db import models
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

class Contact(models.Model):
    """
    Model for storing user contacts with comprehensive information.
    Each contact is associated with a specific user.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='contacts'
    )
    
    # Basic information
    first_name = models.CharField(
        max_length=100,
        help_text="Contact's first name"
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Contact's last name"
    )
    alias = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nickname or alternative name"
    )
    
    # Personal contact information
    email = models.EmailField(
        blank=True,
        help_text="Main email address"
    )
    private_email = models.EmailField(
        blank=True,
        help_text="Private/personal email address"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Main phone number"
    )
    private_phone = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Private/mobile phone number"
    )
    
    # Professional contact information
    professional_email = models.EmailField(
        blank=True,
        help_text="Work/professional email address"
    )
    professional_phone = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Work/professional phone number"
    )
    
    # Additional information
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
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
    
    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        if self.alias:
            return f"{full_name} ({self.alias}) - {self.user.username}"
        return f"{full_name} - {self.user.username}"
    
    @property
    def full_name(self):
        """Return the full name of the contact."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def save(self, *args, **kwargs):
        logger.debug(f"Saving contact {self.full_name} for user: {self.user.username if self.user else 'Unknown'}")
        super().save(*args, **kwargs) 