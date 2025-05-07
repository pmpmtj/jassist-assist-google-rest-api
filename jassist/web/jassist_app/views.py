from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import logging

# Get a logger instance
logger = logging.getLogger(__name__)

def login_view(request):
    """Displays the login page."""
    logger.debug("Rendering login page")
    if request.user.is_authenticated:
        logger.debug("User already authenticated, redirecting to success")
        return redirect('success')
    return render(request, 'jassist_app/login.html')

@login_required
def success_view(request):
    """Success view after login."""
    logger.info(f"User {request.user.username} successfully logged in")
    context = {
        'user': request.user
    }
    return render(request, 'jassist_app/success.html', context)

@login_required
def profile_view(request):
    """User profile view that shows user info and available configurations."""
    logger.debug(f"Rendering profile page for user {request.user.username}")
    
    # Check if user has Google Drive configuration
    has_drive_config = False
    try:
        from jassist.web.download_gdrive.models import UserDriveConfig
        has_drive_config = UserDriveConfig.objects.filter(user=request.user).exists()
    except:
        logger.warning("Could not check for Drive configuration")
    
    context = {
        'user': request.user,
        'has_drive_config': has_drive_config
    }
    return render(request, 'jassist_app/profile.html', context) 