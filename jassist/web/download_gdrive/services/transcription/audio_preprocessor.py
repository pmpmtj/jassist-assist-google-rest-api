"""
Audio Preprocessor module.

This module handles audio file validation and preparation for transcription.
"""
import os
import logging
import tempfile
import subprocess
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

# Create a logger
logger = logging.getLogger(__name__)

class AudioPreprocessor:
    """
    Handles audio file validation and preparation.
    """
    def __init__(self):
        """Initialize the audio preprocessor."""
        self.supported_extensions = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
        self.optimal_formats = ['.mp3', '.wav']
        self.max_file_size_mb = 25  # OpenAI's limit
    
    def validate_audio(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate an audio file for transcription.
        
        Args:
            file_path (Union[str, Path]): Path to the audio file
            
        Returns:
            Dict[str, Any]: Validation result
        """
        file_path = Path(file_path)
        result = {
            "valid": True,
            "file_size": 0,
            "duration": None,
            "needs_processing": False,
            "recommended_format": None,
            "error": None
        }
        
        try:
            # Check if file exists
            if not file_path.exists():
                result["valid"] = False
                result["error"] = f"File not found: {file_path}"
                return result
            
            # Check file extension
            file_ext = file_path.suffix.lower()
            if file_ext not in self.supported_extensions:
                result["valid"] = False
                result["error"] = f"Unsupported file format: {file_ext}"
                return result
            
            # Check file size
            file_size = file_path.stat().st_size
            result["file_size"] = file_size
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size_mb > self.max_file_size_mb:
                result["valid"] = False
                result["error"] = f"File too large: {file_size_mb:.2f} MB (max: {self.max_file_size_mb} MB)"
                return result
            
            # Check if format needs conversion
            if file_ext not in self.optimal_formats:
                result["needs_processing"] = True
                result["recommended_format"] = "mp3"
            
            # Get audio duration if possible
            duration = self._get_audio_duration(file_path)
            if duration:
                result["duration"] = duration
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating audio file {file_path}: {e}")
            result["valid"] = False
            result["error"] = f"Validation error: {str(e)}"
            return result
    
    def prepare_audio(self, file_path: Path, output_format: str = "mp3") -> Optional[Path]:
        """
        Prepare an audio file for transcription, converting if necessary.
        
        Args:
            file_path (Path): Path to the audio file
            output_format (str): Desired output format
            
        Returns:
            Optional[Path]: Path to the prepared file, or None if failed
        """
        # Ensure output format has a dot prefix
        if not output_format.startswith('.'):
            output_format = f".{output_format}"
        
        # If the file is already in the correct format, return it
        if file_path.suffix.lower() == output_format.lower():
            return file_path
        
        try:
            # Create a temporary file for the converted audio
            temp_dir = tempfile.gettempdir()
            output_path = Path(temp_dir) / f"{file_path.stem}{output_format}"
            
            # Use ffmpeg to convert the file
            cmd = [
                'ffmpeg',
                '-i', str(file_path),
                '-y',  # Overwrite output without asking
                str(output_path)
            ]
            
            logger.debug(f"Running conversion: {' '.join(cmd)}")
            
            # Execute the command
            result = subprocess.run(
                cmd, 
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Check if the output file exists
            if output_path.exists():
                logger.info(f"Successfully converted {file_path} to {output_path}")
                return output_path
            else:
                logger.error(f"Conversion failed, output file does not exist: {output_path}")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting audio: {e.stderr.decode() if e.stderr else str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Error preparing audio file {file_path}: {e}")
            return None
    
    def chunk_large_file(self, file_path: Path, max_size_mb: float = 25.0) -> List[Path]:
        """
        Split a large audio file into smaller chunks.
        
        Args:
            file_path (Path): Path to the audio file
            max_size_mb (float): Maximum size per chunk in MB
            
        Returns:
            List[Path]: List of paths to the chunked files
        """
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        # If file is already small enough, return it
        if file_size_mb <= max_size_mb:
            return [file_path]
        
        try:
            # Get total duration
            duration = self._get_audio_duration(file_path)
            if not duration:
                logger.error(f"Could not determine duration of {file_path}")
                return [file_path]
            
            # Calculate chunk duration based on file size ratio
            chunk_duration = (max_size_mb / file_size_mb) * duration
            
            # Ensure chunk duration is at least 10 seconds
            chunk_duration = max(10, chunk_duration)
            
            # Calculate number of chunks needed
            num_chunks = int(duration / chunk_duration) + 1
            logger.info(f"Splitting {file_path} into {num_chunks} chunks of {chunk_duration:.1f}s each")
            
            chunks = []
            temp_dir = tempfile.gettempdir()
            
            for i in range(num_chunks):
                start_time = i * chunk_duration
                output_path = Path(temp_dir) / f"{file_path.stem}_chunk{i+1}{file_path.suffix}"
                
                # Use ffmpeg to extract the chunk
                cmd = [
                    'ffmpeg',
                    '-i', str(file_path),
                    '-ss', str(start_time),  # Start time
                    '-t', str(chunk_duration),  # Duration of segment
                    '-c', 'copy',  # Copy codec (fast)
                    '-y',  # Overwrite output without asking
                    str(output_path)
                ]
                
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    if output_path.exists():
                        chunks.append(output_path)
                        logger.debug(f"Created chunk {i+1}/{num_chunks}: {output_path}")
                    else:
                        logger.warning(f"Failed to create chunk {i+1}/{num_chunks}")
                        
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error creating chunk {i+1}: {e.stderr.decode() if e.stderr else str(e)}")
            
            if not chunks:
                logger.warning("No chunks were created successfully, returning original file")
                return [file_path]
                
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking file {file_path}: {e}")
            return [file_path]
    
    def _get_audio_duration(self, file_path: Path) -> Optional[float]:
        """
        Get the duration of an audio file in seconds.
        
        Args:
            file_path (Path): Path to the audio file
            
        Returns:
            Optional[float]: Duration in seconds, or None if couldn't be determined
        """
        try:
            # Check if it's a WAV file that can be processed with wave module
            if file_path.suffix.lower() == '.wav':
                import wave
                with wave.open(str(file_path), 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / float(rate)
                    return duration
            
            # For other formats, try using ffprobe if available
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(file_path)
            ]
            
            result = subprocess.run(
                cmd, 
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.stdout.strip():
                duration = float(result.stdout.strip())
                return duration
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not determine duration of {file_path}: {e}")
            return None
