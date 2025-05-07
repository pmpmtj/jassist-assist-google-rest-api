"""
Transcription Result Processor module.

This module handles processing and formatting of transcription results.
"""
import os
import json
import logging
import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path

# Create a logger
logger = logging.getLogger(__name__)

class TranscriptionResultProcessor:
    """
    Processes and formats transcription results.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the result processor.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.timestamp_format = config.get("timestamp_format", "%Y%m%d_%H%M%S")
    
    def format_result(self, raw_result: Dict[str, Any], output_format: str = "txt") -> Dict[str, Any]:
        """
        Format the transcription result based on the desired output format.
        
        Args:
            raw_result (Dict[str, Any]): Raw transcription result
            output_format (str): Desired output format (txt, json, srt, etc.)
            
        Returns:
            Dict[str, Any]: Processed result
        """
        try:
            # Extract the transcription text
            text = raw_result.get("text", "")
            
            # If result is already in requested format, return as is
            if (output_format == "json" and isinstance(raw_result, dict)) or \
               (output_format == "text" and isinstance(text, str)):
                return {"text": text, "format": output_format, "processed": False}
            
            # Process based on target format
            if output_format == "txt":
                result = self._format_as_text(raw_result)
            elif output_format == "json":
                result = self._format_as_json(raw_result)
            elif output_format == "srt":
                result = self._format_as_srt(raw_result)
            elif output_format == "vtt":
                result = self._format_as_vtt(raw_result)
            else:
                logger.warning(f"Unknown format '{output_format}', defaulting to text")
                result = self._format_as_text(raw_result)
            
            return {
                "text": result,
                "format": output_format,
                "processed": True,
                "raw_result": raw_result
            }
            
        except Exception as e:
            logger.error(f"Error formatting result: {e}")
            # Return raw text as fallback
            return {
                "text": raw_result.get("text", "Error processing transcript"),
                "format": "txt",
                "error": str(e)
            }
    
    def save_transcription(
        self, 
        processed_result: Dict[str, Any], 
        original_file_path: Path, 
        output_dir: Path
    ) -> Path:
        """
        Save the transcription result to a file.
        
        Args:
            processed_result (Dict[str, Any]): Processed transcription result
            original_file_path (Path): Path to the original audio file
            output_dir (Path): Directory to save the result
            
        Returns:
            Path: Path to the saved file
        """
        try:
            text_content = processed_result.get("text", "")
            output_format = processed_result.get("format", "txt")
            
            # Generate output filename with timestamp
            timestamp = datetime.datetime.now().strftime(self.timestamp_format)
            original_stem = original_file_path.stem
            
            # Determine output path and format
            extension = self._get_extension_for_format(output_format)
            output_file = output_dir / f"{original_stem}_{timestamp}{extension}"
            
            # Write the file
            with open(output_file, "w", encoding="utf-8") as f:
                if output_format == "json":
                    # If it's json, ensure it's actually JSON data
                    try:
                        if isinstance(text_content, str):
                            json_content = json.loads(text_content)
                        else:
                            json_content = text_content
                        json.dump(json_content, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        logger.error(f"Error writing JSON: {e}, writing as plain text")
                        f.write(str(text_content))
                else:
                    # Write as plain text
                    f.write(text_content)
            
            logger.info(f"Saved transcription to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error saving transcription: {e}")
            # Create a fallback file
            fallback_file = output_dir / f"error_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            try:
                with open(fallback_file, "w", encoding="utf-8") as f:
                    f.write(f"Error saving transcription: {e}\n\n")
                    f.write(str(processed_result.get("text", "")))
                return fallback_file
            except:
                logger.critical("Failed to save fallback error file")
                return Path(output_dir) / "transcription_error.txt"
    
    def generate_summary(self, transcription: str, max_length: int = 100) -> str:
        """
        Generate a summary of the transcription.
        
        Args:
            transcription (str): Full transcription text
            max_length (int): Maximum length of summary
            
        Returns:
            str: Summarized text
        """
        # Simple summarization - first few sentences
        try:
            # Split by sentences
            sentences = transcription.split('. ')
            
            # Take first few sentences up to max_length
            summary = ""
            for sentence in sentences:
                if len(summary) + len(sentence) + 2 <= max_length:
                    summary += sentence + '. '
                else:
                    break
            
            # Trim and add ellipsis if truncated
            if len(summary) < len(transcription):
                summary = summary.strip() + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            # Fallback to truncation
            if len(transcription) <= max_length:
                return transcription
            return transcription[:max_length] + "..."
    
    def _format_as_text(self, raw_result: Dict[str, Any]) -> str:
        """
        Format result as plain text.
        
        Args:
            raw_result (Dict[str, Any]): Raw transcription result
            
        Returns:
            str: Formatted text
        """
        return raw_result.get("text", "")
    
    def _format_as_json(self, raw_result: Dict[str, Any]) -> str:
        """
        Format result as JSON.
        
        Args:
            raw_result (Dict[str, Any]): Raw transcription result
            
        Returns:
            str: JSON string
        """
        return json.dumps(raw_result, ensure_ascii=False, indent=2)
    
    def _format_as_srt(self, raw_result: Dict[str, Any]) -> str:
        """
        Format result as SRT subtitle format.
        
        Args:
            raw_result (Dict[str, Any]): Raw transcription result
            
        Returns:
            str: SRT formatted text
        """
        # Check if we already have segments with timestamps
        segments = raw_result.get("segments", [])
        
        if segments:
            # OpenAI already provided timestamped segments
            srt_content = ""
            for i, segment in enumerate(segments):
                start_time = self._format_srt_time(segment.get("start", 0))
                end_time = self._format_srt_time(segment.get("end", 0))
                text = segment.get("text", "").strip()
                
                srt_content += f"{i+1}\n"
                srt_content += f"{start_time} --> {end_time}\n"
                srt_content += f"{text}\n\n"
            
            return srt_content
        
        # Fallback: create a single segment for the entire text
        text = raw_result.get("text", "").strip()
        return f"1\n00:00:00,000 --> 99:59:59,999\n{text}\n"
    
    def _format_as_vtt(self, raw_result: Dict[str, Any]) -> str:
        """
        Format result as WebVTT subtitle format.
        
        Args:
            raw_result (Dict[str, Any]): Raw transcription result
            
        Returns:
            str: WebVTT formatted text
        """
        # WebVTT header
        vtt_content = "WEBVTT\n\n"
        
        # Check if we already have segments with timestamps
        segments = raw_result.get("segments", [])
        
        if segments:
            # OpenAI already provided timestamped segments
            for i, segment in enumerate(segments):
                start_time = self._format_vtt_time(segment.get("start", 0))
                end_time = self._format_vtt_time(segment.get("end", 0))
                text = segment.get("text", "").strip()
                
                vtt_content += f"{i+1}\n"
                vtt_content += f"{start_time} --> {end_time}\n"
                vtt_content += f"{text}\n\n"
            
            return vtt_content
        
        # Fallback: create a single segment for the entire text
        text = raw_result.get("text", "").strip()
        return f"WEBVTT\n\n1\n00:00:00.000 --> 99:59:59.999\n{text}\n"
    
    def _format_srt_time(self, seconds: float) -> str:
        """
        Format time in SRT format.
        
        Args:
            seconds (float): Time in seconds
            
        Returns:
            str: Time in SRT format (HH:MM:SS,mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """
        Format time in WebVTT format.
        
        Args:
            seconds (float): Time in seconds
            
        Returns:
            str: Time in WebVTT format (HH:MM:SS.mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d}.{milliseconds:03d}"
    
    def _get_extension_for_format(self, output_format: str) -> str:
        """
        Get file extension for output format.
        
        Args:
            output_format (str): Output format
            
        Returns:
            str: File extension with dot
        """
        format_map = {
            "txt": ".txt",
            "json": ".json",
            "srt": ".srt",
            "vtt": ".vtt",
            "text": ".txt"
        }
        
        return format_map.get(output_format.lower(), ".txt")
