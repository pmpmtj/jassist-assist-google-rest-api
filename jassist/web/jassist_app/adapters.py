"""
Custom adapters for django-allauth that restrict authentication to Google only.
"""
import logging
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.conf import settings

logger = logging.getLogger(__name__)

class NoSignupAccountAdapter(DefaultAccountAdapter):
    """
    Adapter that prevents direct signup not using a social account.
    All authentication must go through Google OAuth.
    """
    def is_open_for_signup(self, request):
        """
        Disable standard signup without social auth.
        """
        return False
    
    def login(self, request, user):
        """
        Log user in and log the action
        """
        logger.info(f"User {user.username} logged in via Google OAuth")
        return super().login(request, user)

class GoogleOnlySocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapter that only allows Google social account authentication.
    """
    def is_open_for_signup(self, request, sociallogin):
        """
        Allow signup via social accounts.
        """
        return True
    
    def pre_social_login(self, request, sociallogin):
        """
        Validate that only Google authentication is allowed.
        """
        if sociallogin.account.provider != 'google':
            logger.warning(f"Blocked login attempt with non-Google provider: {sociallogin.account.provider}")
            raise ImmediateHttpResponse(HttpResponseForbidden("Only Google authentication is supported."))
        
        # Store tokens after successful login
        logger.debug(f"Processing Google OAuth login for {sociallogin.user}")
        
        # For existing users, store their credentials on every login
        if sociallogin.user and sociallogin.user.id:
            self._store_user_credentials(sociallogin)
    
    def _store_user_credentials(self, sociallogin):
        """
        Helper method to store user credentials from the OAuth process.
        """
        # Only process if we have a valid user
        if not sociallogin.user or not sociallogin.user.id:
            return
            
        # Store the credentials data from the OAuth process
        from diary_project.credentials import credentials_manager
        
        # Get scopes from settings
        google_settings = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
        scopes = ' '.join(google_settings.get('SCOPE', [
            'profile', 
            'email',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.send'
        ]))
        
        # Convert datetime to ISO format string for JSON serialization
        expires_at = None
        if sociallogin.token.expires_at:
            expires_at = sociallogin.token.expires_at.isoformat()
        
        # Ensure we capture the refresh token - this is what we need for reauthorization
        token_secret = sociallogin.token.token_secret
        
        # Log if no token_secret (refresh token) is present - this is critical
        if not token_secret:
            logger.warning(f"No refresh token (token_secret) found for user {sociallogin.user.username}. Token might expire without ability to refresh.")
        
        credentials_data = {
            'token': sociallogin.token.token,
            'token_secret': token_secret,
            'expires_at': expires_at,
            'account_id': sociallogin.account.id,
            'provider': 'google',
            'scopes': scopes
        }
        
        credentials_manager.store_user_credentials(sociallogin.user.id, credentials_data)
        logger.info(f"Stored Google credentials for user {sociallogin.user.username}")
        
    def save_user(self, request, sociallogin, form=None):
        """
        Save the user and store their Google credentials.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Store credentials for new users
        self._store_user_credentials(sociallogin)
        
        return user 