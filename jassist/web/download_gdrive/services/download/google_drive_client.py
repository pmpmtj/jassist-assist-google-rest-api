"""
Google Drive Client module.

This module handles all interactions with the Google Drive API.
"""
import logging
from typing import Dict, List, Optional, Any, Union
from django.contrib.auth.models import User

from jassist_app.services.google_apis import get_google_credentials

# Create a logger
logger = logging.getLogger(__name__)

class GoogleDriveClient:
    """
    Handles all interactions with the Google Drive API.
    """
    def __init__(self, user: User):
        """
        Initialize the Google Drive client for a specific user.
        
        Args:
            user (User): Django User object
        """
        self.user = user
        self.drive_service = None
    
    def _get_drive_service(self):
        """
        Get authenticated Google Drive service for the user.
        
        Returns:
            googleapiclient.discovery.Resource: Google Drive API service
        """
        if self.drive_service:
            return self.drive_service
            
        from googleapiclient.discovery import build
        
        credentials = get_google_credentials(self.user)
        if not credentials:
            logger.error(f"Could not get Google credentials for user: {self.user.username}")
            raise ValueError(f"Google credentials not available for user: {self.user.username}")
        
        self.drive_service = build('drive', 'v3', credentials=credentials)
        logger.debug(f"Created Google Drive service for user: {self.user.username}")
        
        return self.drive_service
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            self._get_drive_service()
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def find_folder_by_name(self, folder_name: str) -> Optional[str]:
        """
        Find a folder by name in the user's Google Drive.
        
        Args:
            folder_name (str): Name of the folder
            
        Returns:
            Optional[str]: Folder ID or None if not found
        """
        service = self._get_drive_service()
        
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        
        try:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=5
            ).execute()
            
            items = response.get('files', [])
            
            if not items:
                logger.warning(f"Folder '{folder_name}' not found")
                return None
            
            # If multiple folders with the same name, use the first one
            folder_id = items[0]['id']
            logger.debug(f"Found folder '{folder_name}' with ID: {folder_id}")
            
            return folder_id
            
        except Exception as e:
            logger.error(f"Error finding folder '{folder_name}': {e}")
            return None
    
    def list_files(self, folder_id: str, query_params: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """
        List files in a specific folder.
        
        Args:
            folder_id (str): ID of the folder
            query_params (Dict[str, str]): Additional query parameters
            
        Returns:
            List[Dict[str, Any]]: List of file metadata dictionaries
        """
        service = self._get_drive_service()
        
        # Base query for files in the folder that aren't trashed
        base_query = f"'{folder_id}' in parents and trashed=false and mimeType!='application/vnd.google-apps.folder'"
        
        # Add any additional query parameters
        if query_params and isinstance(query_params, dict):
            for key, value in query_params.items():
                base_query += f" and {key}='{value}'"
        
        try:
            results = []
            page_token = None
            
            while True:
                response = service.files().list(
                    q=base_query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, modifiedTime, size)',
                    pageToken=page_token,
                    pageSize=100
                ).execute()
                
                items = response.get('files', [])
                results.extend(items)
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            
            logger.debug(f"Found {len(results)} files in folder {folder_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error listing files in folder {folder_id}: {e}")
            return []
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific file.
        
        Args:
            file_id (str): ID of the file
            
        Returns:
            Optional[Dict[str, Any]]: File metadata or None if not found
        """
        service = self._get_drive_service()
        
        try:
            file_metadata = service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, modifiedTime, size'
            ).execute()
            
            logger.debug(f"Retrieved metadata for file: {file_metadata.get('name', file_id)}")
            return file_metadata
            
        except Exception as e:
            logger.error(f"Error getting metadata for file {file_id}: {e}")
            return None
    
    def download_file(self, file_id: str) -> Optional[bytes]:
        """
        Download file content from Google Drive.
        
        Args:
            file_id (str): ID of the file to download
            
        Returns:
            Optional[bytes]: File content as bytes or None if failed
        """
        service = self._get_drive_service()
        
        try:
            # First, get the file's metadata to check its mimeType
            file_metadata = self.get_file_metadata(file_id)
            if not file_metadata:
                logger.error(f"Could not get metadata for file {file_id}")
                return None
                
            mime_type = file_metadata.get('mimeType', '')
            
            # Check if this is a Google Workspace file
            if mime_type.startswith('application/vnd.google-apps'):
                # Handle Google Workspace files (Docs, Sheets, etc.)
                export_mime_type = self._get_export_mime_type(mime_type)
                if not export_mime_type:
                    logger.error(f"Cannot determine export format for {mime_type}, file: {file_metadata.get('name', file_id)}")
                    return None
                    
                logger.debug(f"Exporting Google Workspace file: {file_metadata.get('name', file_id)} as {export_mime_type}")
                
                # Use export method for Google Workspace files
                from io import BytesIO
                
                response = service.files().export(
                    fileId=file_id,
                    mimeType=export_mime_type
                ).execute()
                
                if not response:
                    logger.error(f"Failed to export file {file_id}")
                    return None
                    
                logger.debug(f"Successfully exported file {file_id}")
                return response
            
            # Regular binary file download
            request = service.files().get_media(fileId=file_id)
            
            from io import BytesIO
            from googleapiclient.http import MediaIoBaseDownload
            
            file_content = BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.debug(f"Download progress: {int(status.progress() * 100)}%")
            
            logger.debug(f"Downloaded file {file_id} successfully")
            return file_content.getvalue()
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            return None
    
    def _get_export_mime_type(self, google_mime_type: str) -> Optional[str]:
        """
        Get the appropriate export MIME type for a Google Workspace file.
        
        Args:
            google_mime_type (str): Google Workspace MIME type
            
        Returns:
            Optional[str]: Export MIME type or None if not supported
        """
        # Mapping of Google Workspace MIME types to export formats
        export_formats = {
            'application/vnd.google-apps.document': 'application/pdf',  # Google Docs -> PDF
            'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # Sheets -> XLSX
            'application/vnd.google-apps.presentation': 'application/pdf',  # Slides -> PDF
            'application/vnd.google-apps.drawing': 'image/png',  # Drawings -> PNG
            'application/vnd.google-apps.script': 'application/vnd.google-apps.script+json',  # Apps Script -> JSON
        }
        
        return export_formats.get(google_mime_type)
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive.
        
        Args:
            file_id (str): ID of the file to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        service = self._get_drive_service()
        
        try:
            service.files().delete(fileId=file_id).execute()
            logger.debug(f"Deleted file {file_id} from Google Drive")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False 