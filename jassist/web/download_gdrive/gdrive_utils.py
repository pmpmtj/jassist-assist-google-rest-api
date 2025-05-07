"""
Utility functions for Google Drive operations.
Contains helper functions for file and folder operations in Google Drive.
"""
import os
import datetime
import logging
from pathlib import Path
import io
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)

def find_folder_by_name(service, folder_name, parent_id='root'):
    """
    Find a folder in Google Drive by name and parent.
    
    Args:
        service (googleapiclient.discovery.Resource): Google Drive API service
        folder_name (str): Name of the folder to find
        parent_id (str): ID of the parent folder (default: 'root')
        
    Returns:
        str: Folder ID if found, None otherwise
    """
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
    
    try:
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=1
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            logger.debug(f"Folder '{folder_name}' not found in parent '{parent_id}'")
            return None
            
        logger.debug(f"Found folder '{folder_name}' with ID: {items[0]['id']}")
        return items[0]['id']
    except Exception as e:
        logger.error(f"Error finding folder '{folder_name}': {e}")
        return None

def download_file(service, file_id, output_path):
    """
    Download a file from Google Drive by its ID.
    
    Args:
        service (googleapiclient.discovery.Resource): Google Drive API service
        file_id (str): ID of the file to download
        output_path (str): Path where the file should be saved
        
    Returns:
        dict: Result of the download operation with keys:
            - success (bool): Whether the download was successful
            - file_size (int): Size of the downloaded file in bytes
            - error (str, optional): Error message if download failed
    """
    try:
        # Get file metadata to handle special Google formats
        file_metadata = service.files().get(fileId=file_id, fields='mimeType, name').execute()
        
        # Create a BytesIO stream for the file content
        request = service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        
        # Download the file in chunks
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.debug(f"Download progress: {int(status.progress() * 100)}%")
        
        # Write file to disk
        file_stream.seek(0)
        with open(output_path, 'wb') as f:
            f.write(file_stream.read())
        
        # Get file size
        file_size = os.path.getsize(output_path)
        logger.debug(f"Downloaded file ({file_size} bytes) saved to {output_path}")
        
        return {
            'success': True,
            'file_size': file_size
        }
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def delete_file(service, file_id, file_name=None):
    """
    Delete a file from Google Drive by its ID.
    
    Args:
        service (googleapiclient.discovery.Resource): Google Drive API service
        file_id (str): ID of the file to delete
        file_name (str, optional): Name of the file (for logging purposes)
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    file_desc = file_name or file_id
    
    try:
        service.files().delete(fileId=file_id).execute()
        logger.info(f"Deleted file from Google Drive: {file_desc}")
        return True
    except Exception as e:
        logger.error(f"Error deleting file {file_desc}: {e}")
        return False

def generate_filename_with_timestamp(original_filename, timestamp_format='%Y%m%d_%H%M%S_%f'):
    """
    Generate a new filename with a timestamp inserted before the file extension.
    
    Args:
        original_filename (str): Original filename
        timestamp_format (str): Format string for datetime.strftime()
        
    Returns:
        str: New filename with timestamp inserted
    """
    # Get current timestamp formatted according to the provided format
    timestamp = datetime.datetime.now().strftime(timestamp_format)
    
    # Split the original filename into name and extension
    name, ext = os.path.splitext(original_filename)
    
    # Create the new filename
    return f"{name}_{timestamp}{ext}"

def list_drive_folders(service, parent_id='root', max_results=100):
    """
    List folders in the specified Google Drive parent folder.
    
    Args:
        service (googleapiclient.discovery.Resource): Google Drive API service
        parent_id (str): ID of the parent folder (default: 'root')
        max_results (int): Maximum number of results to return
        
    Returns:
        list: List of dictionaries containing folder information (id, name)
    """
    try:
        query = f"mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=max_results
        ).execute()
        
        folders = results.get('files', [])
        logger.debug(f"Found {len(folders)} folders in parent '{parent_id}'")
        return folders
    except Exception as e:
        logger.error(f"Error listing folders: {e}")
        return [] 