"""
This file manages credentials for Google APIs and database connections.
"""
import os
import json
from pathlib import Path
from django.conf import settings

class Credentials:
    """
    Handles loading, storing, and retrieving various API credentials.
    """
    def __init__(self):
        self.base_dir = settings.BASE_DIR
        self.credentials_dir = self.base_dir / 'credentials'
        
        # Create credentials directory if it doesn't exist
        self.credentials_dir.mkdir(exist_ok=True)
        
        # Path to user-specific credentials
        self.user_credentials_dir = self.credentials_dir / 'users'
        self.user_credentials_dir.mkdir(exist_ok=True)
    
    def get_user_credentials_path(self, user_id):
        """Get the path to a user's credentials file."""
        return self.user_credentials_dir / f'{user_id}.json'
    
    def store_user_credentials(self, user_id, credentials_data):
        """
        Store user credentials to a JSON file.
        
        Args:
            user_id: The user's ID
            credentials_data: Dictionary containing credentials
        """
        file_path = self.get_user_credentials_path(user_id)
        with open(file_path, 'w') as f:
            json.dump(credentials_data, f)
        
        return file_path
    
    def get_user_credentials(self, user_id):
        """
        Retrieve user credentials from the JSON file.
        
        Args:
            user_id: The user's ID
            
        Returns:
            dict: The credentials data, or None if not found
        """
        file_path = self.get_user_credentials_path(user_id)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            # Log error but don't raise to prevent application failure
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading credentials for user {user_id}: {e}")
            return None

# Create a singleton instance
credentials_manager = Credentials() 