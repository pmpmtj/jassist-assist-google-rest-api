"""
URL configuration for the Google Drive download app.
"""
from django.urls import path
from . import views

app_name = 'download_gdrive'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Drive Configuration
    path('configure/', views.configure_drive, name='configure_drive'),
    path('configure/add-folder/', views.add_folder, name='add_folder'),
    
    # Transcription Configuration
    path('configure/transcription/', views.configure_transcription, name='configure_transcription'),
    path('toggle-transcription/', views.toggle_transcription, name='toggle_transcription'),
    
    # Download operations
    path('download/', views.download_now, name='download_now'),
    path('history/', views.download_history, name='history'),
] 