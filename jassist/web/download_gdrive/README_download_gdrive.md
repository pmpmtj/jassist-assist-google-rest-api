# Google Drive Download App for JAssist

## Overview
The Google Drive Download app is a Django-based multi-user application that allows users to automatically download files from their Google Drive. It provides a secure, configurable way to sync files from specified Google Drive folders to local storage, with support for multiple users, each with their own configuration and credentials. The app also supports automatic transcription of audio files using OpenAI's API, storing both transcription files and content in the database for easy access.

## Key Features
- Multi-user support with user-specific configurations
- Download files from multiple Google Drive folders
- File filtering by extension type
- Automatic timestamping of downloaded files
- Optional deletion of files from Google Drive after download
- Download history tracking
- Dry run mode for testing configurations
- Admin interface for global configuration management
- Scheduled downloads with cron-style scheduling
- Automatic audio transcription with OpenAI API
- Transcription content storage and management
- Transcription viewing and searching interface

## Components

### Data Models
- **GlobalDriveConfig**: System-wide configuration that applies to all users
  - Controls file types to download (extensions)
  - Configures post-download behavior (delete from Drive)
  - Sets timestamp format
  
- **UserDriveConfig**: User-specific settings 
  - Target folders to download from
  - Download scheduling options
  - Enable/disable functionality per user
  
- **DownloadRecord**: Tracks download history
  - Records which files were downloaded
  - Captures metadata (time, size, etc.)
  - Records if file was deleted from Drive

- **TranscriptionGlobalConfig**: Global transcription settings
  - Default AI model selection
  - Format settings (JSON, text, SRT, VTT)
  - Cost management settings
  - Default prompts

- **UserTranscriptionConfig**: User-specific transcription settings
  - API key storage (encrypted)
  - Language preferences
  - Enable/disable transcription

- **TranscriptionJob**: Tracks transcription jobs
  - Links to downloaded files
  - Tracks status and progress
  - Stores transcription results and content
  - Contains transcription metadata (word count, duration)
  - Stores both the transcription content and a summary directly in the database

### Core Services
- **DriveDownloader**: Main service that handles the download process
  - Authenticates with Google Drive API
  - Applies user and global configurations
  - Manages file downloading, timestamping, and optional deletion
  - Records download history
  - Supports dry-run mode
  - Provides detailed statistics about download operations
  - Integrates with the transcription service

- **TranscriptionManager**: Manages audio transcription
  - Handles audio file validation and preprocessing
  - Interfaces with OpenAI's transcription API
  - Processes and formats transcription results
  - Stores results in both files and the database
  - Generates summaries of transcriptions

### Management Commands
- **run_scheduled_downloads**: Django command for automatic downloading
  - Checks for users with scheduled downloads
  - Runs downloads based on cron scheduling
  - Supports forcing downloads regardless of schedule
  - Can target specific users

### Utility Functions
- **gdrive_utils.py**: Provides helper functions for Google Drive operations
  - Finding folders by name
  - Downloading files
  - Deleting files
  - Generating timestamped filenames
  - Listing Drive folders

### Views and Forms
- Dashboard view for user overview
- Configuration interface for user settings
- Download history view
- Form-based configuration for target folders and options
- Transcription job listing view
- Transcription detail view with full content and summary

## Configuration System

### Global vs User Configuration
The app uses a two-tier configuration approach:
1. **Global configuration**: Applies to all users, managed by administrators
   - File types (extensions) to download
   - Whether to delete files after download
   - Whether to add timestamps to filenames
   - Format of timestamps
   - Default transcription model and settings

2. **User-specific configuration**: Customizable by each user
   - Target folders to download from
   - Enable/disable downloads
   - Scheduling options (via cron syntax)
   - Transcription API key
   - Language preference for transcription

### Configuration Flow
1. When a download is triggered, the system first retrieves the user's configuration
2. The user configuration is combined with the global configuration using the `get_combined_config()` method
3. This merged configuration dictates the download behavior for the specific user
4. For transcription, a similar process merges user and global transcription configurations

## Credentials Management
- User Google API credentials are stored securely in user-specific JSON files
- Credentials are managed through the `credentials_manager` in the main project
- Each user's credentials are stored in a separate file under `credentials/users/{user_id}.json`
- The app verifies credentials before each operation
- OpenAI API keys are stored encrypted in the database using django-cryptography

## Logging System
- Comprehensive logging throughout the application
- Debug, info, warning, and error levels used appropriately
- Logs for authentication, file operations, and errors
- Tracking of all download activities
- Transcription job progress and errors logged

## Security
- Each user can only access their own Google Drive files
- Credentials are stored separately for each user
- Operations are performed in the context of the authenticated user
- Downloads are stored in user-specific directories
- API keys for transcription services are stored encrypted using django-cryptography
- Encryption uses Django's SECRET_KEY and FERNET symmetric encryption to protect sensitive data
- Transcription content is only accessible to the user who created it

## File Storage
- Downloaded files are stored in a user-specific directory: `media/downloads/drive/{user_id}/`
- Files can optionally have timestamps added to prevent overwriting
- Download records maintain the link between Drive files and local files
- Transcription files are stored in `media/transcriptions/{user_id}/`
- Transcription content is also stored directly in the database for easy access and search

## Integration Points
- Integrates with Django's authentication system for user management
- Uses Google's OAuth2 for secure API authentication
- Connects to Django Admin for configuration management
- Can be scheduled using cron syntax for automated downloads
- Uses OpenAI API for transcription services

## Usage Flow
1. Users authenticate with their Google account
2. Users configure which folders to download from
3. Users can manually trigger downloads or set up schedules
4. The system downloads files according to global and user configurations
5. Audio files are automatically transcribed if configured
6. Download history is recorded and viewable by users
7. Transcription content is stored and viewable directly in the web interface
8. Administrators can manage global settings through the admin interface

## Transcription Features
- Automatic transcription of audio files during download
- OpenAI API integration with configurable model selection
- Transcription content stored both as files and in the database
- Automatic summarization of transcription content
- User-friendly interface for viewing transcriptions
- Detail view with complete transcription content
- Searchable transcription content through admin interface

## Scheduling
- Uses cron syntax for flexible scheduling
- Management command `run_scheduled_downloads` processes scheduled tasks
- Can be run via crontab or similar task scheduler
- Supports force-run and user-specific run options

## Technical Requirements
- Django web framework
- Google API client libraries
- PostgreSQL database (for ArrayField support)
- Python 3.6+ compatibility
- croniter library for schedule parsing
- OpenAI API client for transcription 