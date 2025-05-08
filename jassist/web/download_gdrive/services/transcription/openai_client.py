"""
OpenAI Transcription Client module.

This module handles all communications with the OpenAI API for audio transcription.
"""
import logging
import time
from typing import Dict, Any, Optional, Union
from pathlib import Path

# Create a logger
logger = logging.getLogger(__name__)

class OpenAITranscriptionClient:
    """
    Handles OpenAI API communications for transcription.
    """
    def __init__(self, api_key: str):
        """
        Initialize the OpenAI transcription client.
        
        Args:
            api_key (str): OpenAI API key
        """
        self.api_key = api_key
        self.client = None
    
    def _get_client(self):
        """
        Get or create OpenAI client.
        
        Returns:
            openai.OpenAI: OpenAI client
        """
        if self.client is None:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            
        return self.client
    
    def transcribe(
        self, 
        file_path: Path, 
        model: str = "gpt-4o-transcribe",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file using OpenAI API.
        
        Args:
            file_path (Path): Path to the audio file
            model (str): Model to use (default: gpt-4o-transcribe)
            language (Optional[str]): Language code
            prompt (Optional[str]): Transcription prompt
            response_format (str): Response format (json or text)
            
        Returns:
            Dict[str, Any]: Transcription result or error dict
        """
        try:
            client = self._get_client()
            
            # Validate response format
            if response_format not in ["json", "text", "srt", "verbose_json", "vtt"]:
                response_format = "json"
            
            # Build parameters dictionary with only valid parameters
            params = {
                "model": model,
                "response_format": response_format
            }
            
            if language:
                params["language"] = language
                
            if prompt:
                params["prompt"] = prompt
            
            logger.debug(f"Sending transcription request: {params}")
            
            # Measure time taken
            start_time = time.time()
            
            with open(file_path, "rb") as audio_file:
                params["file"] = audio_file
                response = client.audio.transcriptions.create(**params)
            
            end_time = time.time()
            time_diff = end_time - start_time
            
            logger.info(f"Transcription completed in {time_diff:.2f}s")
            
            # Convert response to dictionary
            if hasattr(response, 'model_dump'):
                result = response.model_dump()
            elif hasattr(response, 'to_dict'):
                result = response.to_dict()
            else:
                result = response
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI transcription error: {e}")
            return {"error": str(e)}
    
    def check_rate_limits(self) -> Dict[str, Any]:
        """
        Check API rate limits.
        
        Returns:
            Dict[str, Any]: Rate limit information
        """
        # OpenAI does not currently provide a direct way to check rate limits
        # This is a placeholder for future implementation
        return {"status": "unknown", "message": "Rate limit checking not implemented"}
    
    def handle_api_error(self, error: Exception) -> Dict[str, Any]:
        """
        Handle OpenAI API errors gracefully.
        
        Args:
            error (Exception): The error that occurred
            
        Returns:
            Dict[str, Any]: Error handling result
        """
        # Import OpenAI error types if available
        try:
            from openai import (
                APIError,
                RateLimitError,
                APIConnectionError,
                AuthenticationError,
                InvalidRequestError,
                PermissionError
            )
            
            # Handle specific error types
            if isinstance(error, RateLimitError):
                logger.warning(f"Rate limit exceeded: {error}")
                return {
                    "error_type": "rate_limit",
                    "message": "OpenAI API rate limit exceeded. Please try again later.",
                    "retry_after": 60  # Default retry after 60 seconds
                }
                
            elif isinstance(error, APIConnectionError):
                logger.error(f"API connection error: {error}")
                return {
                    "error_type": "connection",
                    "message": "Could not connect to OpenAI API. Please check your internet connection."
                }
                
            elif isinstance(error, AuthenticationError):
                logger.error(f"Authentication error: {error}")
                return {
                    "error_type": "auth",
                    "message": "Invalid API key or authentication failure."
                }
                
            elif isinstance(error, InvalidRequestError):
                logger.error(f"Invalid request: {error}")
                return {
                    "error_type": "invalid_request",
                    "message": f"Invalid request to OpenAI API: {error}"
                }
                
            elif isinstance(error, PermissionError):
                logger.error(f"Permission error: {error}")
                return {
                    "error_type": "permission",
                    "message": "You don't have permission to use this OpenAI model or feature."
                }
                
            elif isinstance(error, APIError):
                logger.error(f"API error: {error}")
                return {
                    "error_type": "api_error",
                    "message": f"OpenAI API error: {error}"
                }
                
        except ImportError:
            logger.debug("Could not import OpenAI error types")
        
        # Generic error handling
        logger.error(f"Unhandled OpenAI error: {error}")
        return {
            "error_type": "unknown",
            "message": f"OpenAI API error: {error}"
        }
    
    def estimate_cost(self, duration_seconds: float, model: str = "gpt-4o-transcribe") -> Dict[str, Any]:
        """
        Estimate the cost of a transcription job.
        
        Args:
            duration_seconds (float): Duration of audio in seconds
            model (str): Model name
            
        Returns:
            Dict[str, Any]: Cost estimate
        """
        # Current OpenAI pricing (as of 2023, subject to change)
        # https://openai.com/pricing
        pricing = {
            "gpt-4o-transcribe": 0.006  # $0.006 per minute
        }
        
        # Default to gpt-4o-transcribe pricing if model not found
        per_minute_cost = pricing.get(model, pricing["gpt-4o-transcribe"])
        
        # Convert seconds to minutes and calculate cost
        duration_minutes = duration_seconds / 60.0
        estimated_cost = duration_minutes * per_minute_cost
        
        return {
            "duration_seconds": duration_seconds,
            "duration_minutes": duration_minutes,
            "model": model,
            "per_minute_cost": per_minute_cost,
            "estimated_cost_usd": estimated_cost
        }
