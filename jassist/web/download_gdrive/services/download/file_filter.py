"""
File Filter module.

This module handles determining which files should be downloaded
based on various filtering criteria.
"""
import os
import logging
from typing import Dict, List, Any

# Create a logger
logger = logging.getLogger(__name__)

class FileFilter:
    """
    Filters files based on various criteria.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the file filter with configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.include_extensions = config.get("include_extensions", [])
        logger.debug(f"Initialized FileFilter with extensions: {self.include_extensions}")
    
    def match_extension(self, filename: str, extensions: List[str]) -> bool:
        """
        Check if a filename matches any of the given extensions.
        
        Args:
            filename (str): Name of the file
            extensions (List[str]): List of extensions to match against
            
        Returns:
            bool: True if the file matches any extension, False otherwise
        """
        if not extensions:
            return True
            
        file_ext = os.path.splitext(filename)[1].lower()
        
        # If the extension doesn't start with '.', add it
        normalized_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions]
        
        return file_ext in normalized_extensions
    
    def filter_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter files based on configured criteria.
        
        Args:
            files (List[Dict[str, Any]]): List of file metadata dictionaries
            
        Returns:
            List[Dict[str, Any]]: Filtered list of files
        """
        filtered_files = []
        
        for file_metadata in files:
            # Check if file meets all criteria
            if self._should_download(file_metadata):
                filtered_files.append(file_metadata)
        
        logger.debug(f"Filtered {len(files)} files to {len(filtered_files)} based on criteria")
        return filtered_files
    
    def _should_download(self, file_metadata: Dict[str, Any]) -> bool:
        """
        Determine if a file should be downloaded based on various criteria.
        
        Args:
            file_metadata (Dict[str, Any]): File metadata dictionary
            
        Returns:
            bool: True if the file should be downloaded, False otherwise
        """
        filename = file_metadata.get("name", "")
        
        # Check extension filter
        if not self.match_extension(filename, self.include_extensions):
            logger.debug(f"Skipping file {filename} - extension not in include list")
            return False
        
        # Add more filter criteria here as needed
        
        return True
    
    def should_transcribe(self, filename: str) -> bool:
        """
        Determine if a file should be transcribed based on its extension.
        
        Args:
            filename (str): Name of the file
            
        Returns:
            bool: True if the file should be transcribed
        """
        # List of audio file extensions that can be transcribed
        audio_extensions = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
        
        # Get file extension (lowercase for comparison)
        file_ext = os.path.splitext(filename)[1].lower()
        
        return file_ext in audio_extensions 