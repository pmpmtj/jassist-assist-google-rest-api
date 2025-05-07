"""
Google API interaction module for authentication.
Provides services for Google OAuth authentication.
"""
import logging
from google.oauth2.credentials import Credentials
from diary_project.credentials import credentials_manager

# Get a logger instance specific to this module
logger = logging.getLogger(__name__)

def get_google_credentials(user):
    """
    Fetches Google credentials for a given Django user.
    
    Args:
        user: Django User object
        
    Returns:
        google.oauth2.credentials.Credentials object or None if not available
    """
    logger.debug(f"Attempting to fetch Google credentials for user: {user.username}")
    
    try:
        # Get the credentials data from our storage
        credentials_data = credentials_manager.get_user_credentials(user.id)
        if not credentials_data:
            logger.warning(f"No stored credentials found for user {user.username}")
            return None
        
        # Try to get additional info from Django allauth
        try:
            social_account = user.socialaccount_set.get(provider='google')
            social_app = social_account.get_provider().app
            client_id = social_app.client_id
            client_secret = social_app.secret
        except Exception as e:
            logger.warning(f"Could not retrieve social app details: {e}")
            return None
        
        # Use the credentials data from our JSON storage
        token = credentials_data.get('token')
        token_secret = credentials_data.get('token_secret')
        scopes = credentials_data.get('scopes', '').split() if isinstance(credentials_data.get('scopes'), str) else credentials_data.get('scopes', [])
        
        if not token:
            logger.warning(f"No token found in stored credentials for user {user.username}")
            return None
        
        # Build google-auth credentials object
        credentials = Credentials(
            token=token,
            refresh_token=token_secret,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes
        )
        
        logger.debug(f"Successfully created Google credentials for user {user.username}")
        return credentials
        
    except Exception as e:
        logger.error(f"Error fetching Google credentials for user {user.username}: {e}", exc_info=True)
        return None 