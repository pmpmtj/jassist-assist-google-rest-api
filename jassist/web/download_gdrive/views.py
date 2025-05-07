"""
Views for the Google Drive download functionality.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum
import json
from .models import UserDriveConfig, GlobalDriveConfig, DownloadRecord, UserTranscriptionConfig, TranscriptionGlobalConfig
from .forms import UserDriveConfigForm, GlobalDriveConfigForm, DriveDownloadForm, FolderSelectionForm, UserTranscriptionConfigForm
from .services.download.download_manager import DownloadManager
from .gdrive_utils import list_drive_folders
from jassist_app.services.google_apis import get_google_credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """
    Dashboard view showing download status and configuration.
    """
    # Get or create user-specific Drive configuration
    user_config, created = UserDriveConfig.objects.get_or_create(
        user=request.user,
        defaults={
            'target_folders': [],
            'is_active': True
        }
    )
    
    # Get download history
    download_history = DownloadRecord.objects.filter(user=request.user).order_by('-downloaded_at')[:10]
    
    # Get download statistics
    stats = {
        'total_files': DownloadRecord.objects.filter(user=request.user).count(),
        'total_size': DownloadRecord.objects.filter(user=request.user).aggregate(Sum('file_size'))['file_size__sum'] or 0,
        'last_download': user_config.last_run,
    }
    
    # Check if user has transcription config
    has_transcription_config = UserTranscriptionConfig.objects.filter(user=request.user).exists()
    
    context = {
        'user_config': user_config,
        'download_history': download_history,
        'stats': stats,
        'has_transcription_config': has_transcription_config,
    }
    
    return render(request, 'download_gdrive/dashboard.html', context)

@login_required
def configure_drive(request):
    """
    Configure Google Drive download settings for the user.
    """
    # Get or create user configuration
    user_config, created = UserDriveConfig.objects.get_or_create(
        user=request.user,
        defaults={
            'target_folders': [],
            'is_active': True
        }
    )
    
    if request.method == 'POST':
        form = UserDriveConfigForm(request.POST, instance=user_config)
        if form.is_valid():
            form.save()
            messages.success(request, "Drive download configuration updated successfully!")
            return redirect('download_gdrive:dashboard')
    else:
        form = UserDriveConfigForm(instance=user_config)
    
    # Get global configuration for reference
    global_config = GlobalDriveConfig.get_config()
    
    context = {
        'form': form,
        'global_config': global_config
    }
    
    return render(request, 'download_gdrive/configure.html', context)

@login_required
def download_history(request):
    """
    View download history for the user.
    """
    history = DownloadRecord.objects.filter(user=request.user).order_by('-downloaded_at')
    
    # Group by date for better organization
    grouped_history = {}
    for record in history:
        date_str = record.downloaded_at.strftime('%Y-%m-%d')
        if date_str not in grouped_history:
            grouped_history[date_str] = []
        grouped_history[date_str].append(record)
    
    context = {
        'grouped_history': grouped_history,
    }
    
    return render(request, 'download_gdrive/history.html', context)

@login_required
@require_POST
def download_now(request):
    """
    Trigger an immediate download from Google Drive.
    """
    form = DriveDownloadForm(request.POST)
    
    if form.is_valid():
        try:
            # Check if user has active configuration
            user_config = get_object_or_404(UserDriveConfig, user=request.user)
            
            if not user_config.is_active:
                messages.error(request, "Drive downloads are disabled for your account.")
                return redirect('download_gdrive:dashboard')
            
            if not user_config.target_folders:
                messages.error(request, "No target folders configured. Please configure your download settings first.")
                return redirect('download_gdrive:configure_drive')
            
            # Get form options
            dry_run = form.cleaned_data.get('dry_run', False)
            
            # Create downloader instance
            downloader = DownloadManager(request.user.id, dry_run=dry_run)
            
            # Run the download process
            result = downloader.run_downloads()
            
            if result.get('success', False):
                stats = result.get('stats', {})
                if dry_run:
                    messages.success(
                        request, 
                        f"Dry run completed successfully. Would have downloaded "
                        f"{stats.get('files_found', 0)} files."
                    )
                else:
                    messages.success(
                        request, 
                        f"Download completed successfully. Downloaded "
                        f"{stats.get('files_downloaded', 0)} files."
                    )
            else:
                error = result.get('error', 'Unknown error')
                messages.error(request, f"Download failed: {error}")
            
            return redirect('download_gdrive:dashboard')
            
        except Exception as e:
            logger.error(f"Error during download: {e}", exc_info=True)
            messages.error(request, f"An error occurred: {e}")
            return redirect('download_gdrive:dashboard')
    else:
        messages.error(request, "Invalid form submission.")
        return redirect('download_gdrive:dashboard')

@login_required
def configure_transcription(request):
    """
    Configure transcription settings for the user.
    """
    # Get or create user configuration
    user_config, created = UserTranscriptionConfig.objects.get_or_create(
        user=request.user,
        defaults={
            'api_key': '',
            'is_active': True
        }
    )
    
    if request.method == 'POST':
        form = UserTranscriptionConfigForm(request.POST, instance=user_config)
        if form.is_valid():
            form.save()
            logger.info(f"User {request.user.username} updated transcription configuration with encrypted API key")
            messages.success(request, "Transcription configuration updated successfully!")
            return redirect('download_gdrive:dashboard')
    else:
        form = UserTranscriptionConfigForm(instance=user_config)
    
    # Get global configuration for reference
    global_config = TranscriptionGlobalConfig.get_config()
    
    context = {
        'form': form,
        'global_config': global_config
    }
    
    return render(request, 'download_gdrive/configure_transcription.html', context)

@login_required
@require_POST
def toggle_transcription(request):
    """
    Toggle transcription on/off for the user.
    """
    try:
        # Get user config
        user_config = get_object_or_404(UserTranscriptionConfig, user=request.user)
        
        # Toggle is_active status
        user_config.is_active = not user_config.is_active
        user_config.save()
        
        status = "enabled" if user_config.is_active else "disabled"
        messages.success(request, f"Transcription {status} successfully!")
        
    except UserTranscriptionConfig.DoesNotExist:
        messages.error(request, "You need to configure transcription settings first.")
    
    return redirect('download_gdrive:dashboard')

@login_required
@require_POST
def add_folder(request):
    """
    Add a folder to user's target folders list.
    """
    user = request.user
    folder_name = request.POST.get('folder', '').strip()
    
    if folder_name:
        try:
            user_config = UserDriveConfig.objects.get(user=user)
            
            # Add folder if not already in the list
            if folder_name not in user_config.target_folders:
                user_config.target_folders.append(folder_name)
                user_config.save()
                messages.success(request, f"Added folder '{folder_name}' to your target folders.")
            else:
                messages.info(request, f"Folder '{folder_name}' is already in your target folders.")
                
        except UserDriveConfig.DoesNotExist:
            # Create configuration with this folder
            UserDriveConfig.objects.create(
                user=user,
                target_folders=[folder_name]
            )
            messages.success(request, f"Added folder '{folder_name}' to your target folders.")
    
    # For AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
        
    return redirect('download_gdrive:configure_drive')
    
@login_required
@require_POST
def remove_folder(request):
    """
    Remove a folder from user's target folders list.
    """
    user = request.user
    folder_name = request.POST.get('folder', '').strip()
    
    if folder_name:
        try:
            user_config = UserDriveConfig.objects.get(user=user)
            
            if folder_name in user_config.target_folders:
                user_config.target_folders.remove(folder_name)
                user_config.save()
                messages.success(request, f"Removed folder '{folder_name}' from your target folders.")
            else:
                messages.info(request, f"Folder '{folder_name}' is not in your target folders.")
                
        except UserDriveConfig.DoesNotExist:
            messages.error(request, "You don't have any configured folders yet.")
    
    # For AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
        
    return redirect('download_gdrive:configure_drive') 