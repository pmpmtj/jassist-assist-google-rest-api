"""
Forms for Google Drive download configuration.
"""
from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from .models import GlobalDriveConfig, UserDriveConfig, UserTranscriptionConfig

class GlobalDriveConfigForm(forms.ModelForm):
    """Form for global Drive configuration settings."""
    
    include_extensions = SimpleArrayField(
        forms.CharField(max_length=20),
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text='Enter file extensions to include (one per line), for example: .pdf, .doc, .csv'
    )
    
    class Meta:
        model = GlobalDriveConfig
        fields = ['include_extensions', 'delete_after_download', 'add_timestamp', 'timestamp_format']
        widgets = {
            'timestamp_format': forms.TextInput(attrs={'placeholder': '%Y%m%d_%H%M%S_%f'}),
        }
        help_texts = {
            'delete_after_download': 'If checked, files will be deleted from Google Drive after download.',
            'add_timestamp': 'If checked, filenames will include a timestamp.',
            'timestamp_format': 'Format for timestamp (Python datetime format).'
        }

class UserDriveConfigForm(forms.ModelForm):
    """Form for managing user-specific Google Drive download configuration."""
    # Convert ArrayField to a more user-friendly input
    target_folders = SimpleArrayField(
        forms.CharField(max_length=255),
        delimiter=',',
        required=False,
        help_text="Enter folder names separated by commas. Use 'root' for the Drive root folder."
    )
    
    download_schedule = forms.CharField(
        max_length=100,
        required=False,
        help_text="Optional cron-style schedule (e.g., '0 5 * * *' for daily at 5 AM)."
    )
    
    class Meta:
        model = UserDriveConfig
        fields = ['target_folders', 'download_schedule', 'is_active']
        
    def clean_download_schedule(self):
        """Validate the cron schedule format."""
        schedule = self.cleaned_data.get('download_schedule')
        if schedule:
            # Basic validation of cron format (5 or 6 components)
            components = schedule.strip().split()
            if len(components) not in [5, 6]:
                raise ValidationError(
                    "Invalid cron format. Use 5 or 6 components (e.g., '0 5 * * *')."
                )
        return schedule

class UserTranscriptionConfigForm(forms.ModelForm):
    """Form for managing user-specific transcription configuration."""
    api_key = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        required=True,
        help_text="Your OpenAI API key for transcriptions. This will be stored encrypted."
    )
    
    language = forms.CharField(
        max_length=50,
        required=False,
        help_text="Optional language code (e.g., 'en', 'fr', 'es'). Leave blank for auto-detection."
    )
    
    class Meta:
        model = UserTranscriptionConfig
        fields = ['api_key', 'language', 'is_active']
        
    def clean_language(self):
        """Validate language code format."""
        language = self.cleaned_data.get('language')
        if language and len(language) > 2:
            # Basic validation to ensure language code is at least somewhat valid
            if not language.islower() or len(language) > 5:
                raise ValidationError(
                    "Language code should be a standard ISO language code (e.g., 'en', 'fr', 'es')."
                )
        return language

class DriveDownloadForm(forms.Form):
    """Form for triggering a download operation."""
    
    dry_run = forms.BooleanField(
        required=False, 
        initial=False,
        label='Dry Run',
        help_text='If checked, no actual downloads will occur. Use this to test your configuration.'
    )

class FolderSelectionForm(forms.Form):
    """
    Form for selecting folders from a user's Google Drive.
    Used for adding folders to the target_folders list.
    """
    
    folder = forms.ChoiceField(
        choices=[],  # Populated dynamically
        required=True,
        label='Select Folder',
        help_text='Choose a folder from your Google Drive'
    )
    
    def __init__(self, folder_choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add an empty option at the beginning
        self.fields['folder'].choices = [('', 'Select a folder...')] + folder_choices 