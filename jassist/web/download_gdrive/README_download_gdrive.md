# Google Drive Download App for JAssist

## Overview
The Google Drive Download app is a Django-based multi-user application that allows users to automatically download files from their Google Drive. It provides a secure, configurable way to sync files from specified Google Drive folders to local storage, with support for multiple users, each with their own configuration and credentials.

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

### Core Services
- **DriveDownloader**: Main service that handles the download process
  - Authenticates with Google Drive API
  - Applies user and global configurations
  - Manages file downloading, timestamping, and optional deletion
  - Records download history
  - Supports dry-run mode
  - Provides detailed statistics about download operations

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

## Configuration System

### Global vs User Configuration
The app uses a two-tier configuration approach:
1. **Global configuration**: Applies to all users, managed by administrators
   - File types (extensions) to download
   - Whether to delete files after download
   - Whether to add timestamps to filenames
   - Format of timestamps

2. **User-specific configuration**: Customizable by each user
   - Target folders to download from
   - Enable/disable downloads
   - Scheduling options (via cron syntax)

### Configuration Flow
1. When a download is triggered, the system first retrieves the user's configuration
2. The user configuration is combined with the global configuration using the `get_combined_config()` method
3. This merged configuration dictates the download behavior for the specific user

## Credentials Management
- User Google API credentials are stored securely in user-specific JSON files
- Credentials are managed through the `credentials_manager` in the main project
- Each user's credentials are stored in a separate file under `credentials/users/{user_id}.json`
- The app verifies credentials before each operation

## Logging System
- Comprehensive logging throughout the application
- Debug, info, warning, and error levels used appropriately
- Logs for authentication, file operations, and errors
- Tracking of all download activities

## Security
- Each user can only access their own Google Drive files
- Credentials are stored separately for each user
- Operations are performed in the context of the authenticated user
- Downloads are stored in user-specific directories
- API keys for transcription services are stored encrypted using django-cryptography
- Encryption uses Django's SECRET_KEY and FERNET symmetric encryption to protect sensitive data

## File Storage
- Downloaded files are stored in a user-specific directory: `media/downloads/drive/{user_id}/`
- Files can optionally have timestamps added to prevent overwriting
- Download records maintain the link between Drive files and local files

## Integration Points
- Integrates with Django's authentication system for user management
- Uses Google's OAuth2 for secure API authentication
- Connects to Django Admin for configuration management
- Can be scheduled using cron syntax for automated downloads

## Usage Flow
1. Users authenticate with their Google account
2. Users configure which folders to download from
3. Users can manually trigger downloads or set up schedules
4. The system downloads files according to global and user configurations
5. Download history is recorded and viewable by users
6. Administrators can manage global settings through the admin interface

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