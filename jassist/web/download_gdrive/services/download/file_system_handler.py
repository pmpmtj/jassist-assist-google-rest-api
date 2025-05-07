"""
File System Handler module.

This module handles local file system operations for the downloader.
"""
import os
import shutil
import logging
import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from django.conf import settings

# Create a logger
logger = logging.getLogger(__name__)

class FileSystemHandler:
    """
    Handles local file system operations.
    """
    def __init__(self, user_id: int, config: Dict[str, Any]):
        """
        Initialize the file system handler.
        
        Args:
            user_id (int): User ID
            config (Dict[str, Any]): Configuration dictionary
        """
        self.user_id = user_id
        self.config = config
        self.base_download_dir = self._create_user_download_dir()
    
    def _create_user_download_dir(self) -> Path:
        """
        Create and return path to user's download directory.
        
        Returns:
            Path: Path to the user's download directory
        """
        # Base directory for all downloads
        download_base = Path(settings.BASE_DIR) / "media" / "downloads" / "drive"
        
        # User-specific directory
        user_dir = download_base / str(self.user_id)
        
        # Create directories if they don't exist
        os.makedirs(user_dir, exist_ok=True)
        
        logger.debug(f"User download directory: {user_dir}")
        return user_dir
    
    def prepare_directory(self, directory_path: Path) -> bool:
        """
        Ensure a directory exists.
        
        Args:
            directory_path (Path): Path to the directory
            
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {e}")
            return False
    
    def generate_file_path(self, original_name: str) -> Path:
        """
        Generate a local file path with proper naming.
        
        Args:
            original_name (str): Original file name
            
        Returns:
            Path: Path where the file should be saved
        """
        # Check if we need to add timestamp to filename
        if self.config.get("add_timestamp", False):
            # Get timestamp format from config
            timestamp_format = self.config.get("timestamp_format", "%Y%m%d_%H%M%S")
            timestamp = datetime.datetime.now().strftime(timestamp_format)
            
            # Split original name and add timestamp
            name_parts = os.path.splitext(original_name)
            new_name = f"{name_parts[0]}_{timestamp}{name_parts[1]}"
        else:
            new_name = original_name
        
        # Create path
        file_path = self.base_download_dir / new_name
        
        # Handle duplicates
        counter = 1
        while file_path.exists():
            # Split filename and extension
            name_parts = os.path.splitext(new_name)
            # Add counter to filename
            file_path = self.base_download_dir / f"{name_parts[0]}_{counter}{name_parts[1]}"
            counter += 1
        
        return file_path
    
    def check_available_space(self, directory_path: Path, required_bytes: int, buffer_factor: float = 1.5) -> bool:
        """
        Check if there's enough space available on the disk.
        
        Args:
            directory_path (Path): Path to check space on
            required_bytes (int): Number of bytes required
            buffer_factor (float): Safety factor multiplier
            
        Returns:
            bool: True if there's enough space, False otherwise
        """
        try:
            # Get disk usage statistics
            total, used, free = shutil.disk_usage(directory_path)
            
            # Add safety buffer
            required_with_buffer = int(required_bytes * buffer_factor)
            
            # Check if we have enough space
            has_enough_space = free > required_with_buffer
            
            if not has_enough_space:
                logger.warning(
                    f"Low disk space: {free} bytes available, "
                    f"need {required_with_buffer} bytes "
                    f"(with {buffer_factor}x buffer)"
                )
            
            return has_enough_space
            
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            # Return True by default to allow download to proceed
            # Better to try downloading than to block due to an error
            return True
    
    def get_download_path(self, filename: str) -> Path:
        """
        Get the path where a file should be saved.
        
        Args:
            filename (str): Name of the file
            
        Returns:
            Path: Path where the file should be saved
        """
        # Create a timestamped filename if configured
        if self.config['download']['add_timestamps']:
            from datetime import datetime
            timestamp = datetime.now().strftime(self.config['download']['timestamp_format'])
            filename_parts = filename.split('.')
            if len(filename_parts) > 1:
                # Add timestamp before extension
                ext = filename_parts[-1]
                base = '.'.join(filename_parts[:-1])
                filename = f"{base}_{timestamp}.{ext}"
            else:
                # No extension, just append timestamp
                filename = f"{filename}_{timestamp}"
        
        # Create the full path
        download_path = self.base_download_dir / filename
        
        # Ensure the directory exists
        download_path.parent.mkdir(parents=True, exist_ok=True)
        
        return download_path

    def save_file(self, file_path: Path, content: bytes) -> bool:
        """
        Save file content to disk.
        
        Args:
            file_path (Path): Path where to save the file
            content (bytes): File content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure the directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.debug(f"Saved file to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving file to {file_path}: {e}")
            return False
    
    def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file from disk.
        
        Args:
            file_path (Path): Path to the file
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted file {file_path}")
                return True
            else:
                logger.warning(f"File not found: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False 