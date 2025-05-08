"""
Classification adapter for OpenAI Assistant.

This module provides a specialized interface for text classification
using the OpenAI Assistant API.
"""

import time
import logging
from typing import Dict, Any, Optional, Union
from django.utils import timezone
from django.conf import settings

from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from .models import ClassificationConfig, ClassificationPrompt, ClassificationMetrics

logger = logging.getLogger(__name__)

# Error handling constants
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
BACKOFF_FACTOR = 2  # exponential backoff


class ClassificationError(Exception):
    """Base exception for classification errors."""
    pass


class ConfigError(ClassificationError):
    """Error related to configuration."""
    pass


class APIClientError(ClassificationError):
    """Error related to OpenAI API client."""
    pass


class ClassificationAdapter:
    """
    Adapter for using the OpenAI Assistant with text classification.
    """
    
    def __init__(self):
        """
        Initialize the classification assistant adapter.
        
        Raises:
            ConfigError: If required configuration is missing
        """
        # Load configuration from database
        try:
            self.config = ClassificationConfig.get_active_config()
            logger.debug(f"Using classification config for {self.config.assistant_name}")
        except Exception as e:
            error_msg = f"Failed to load classification configuration: {e}"
            logger.error(error_msg)
            raise ConfigError(error_msg)
        
        # Initialize OpenAI client
        try:
            # Try to get API key from config or settings
            api_key = self.config.api_key or getattr(settings, 'OPENAI_API_KEY', None)
            
            if not api_key:
                logger.warning("No OpenAI API key found in config or settings")
                # For dry runs or testing, we can create a client without a key
                self.client = None
            else:
                self.client = OpenAI(api_key=api_key)
                logger.debug("OpenAI client initialized")
                
        except Exception as e:
            error_msg = f"Failed to initialize OpenAI client: {e}"
            logger.error(error_msg)
            raise APIClientError(error_msg)
    
    def get_prompt_template(self, prompt_name: str) -> str:
        """
        Get a prompt template by name from the database.
        
        Args:
            prompt_name: Name of the prompt template
            
        Returns:
            str: The prompt template text
            
        Raises:
            ConfigError: If the prompt template is not found
        """
        prompt = ClassificationPrompt.get_prompt(prompt_name)
        if not prompt:
            raise ConfigError(f"Prompt '{prompt_name}' not found in classification prompts")
        
        return prompt.template
    
    def get_or_create_assistant(self) -> str:
        """
        Get or create an OpenAI Assistant for classification.
        
        Returns:
            str: The Assistant ID
            
        Raises:
            APIClientError: If the assistant cannot be created or retrieved
        """
        # Check if client is available
        if not self.client:
            raise APIClientError("OpenAI client not initialized (missing API key)")
            
        # Check if we already have an assistant ID
        if self.config.assistant_id:
            try:
                # Verify the assistant exists
                assistant = self.client.beta.assistants.retrieve(self.config.assistant_id)
                logger.debug(f"Using existing assistant: {assistant.id}")
                return assistant.id
            except Exception as e:
                logger.warning(f"Couldn't retrieve assistant {self.config.assistant_id}: {e}")
                # Fall through to create a new one
        
        # Create a new assistant
        try:
            logger.info("Creating new classification assistant")
            
            # Get the assistant instructions
            instructions = None
            try:
                instructions = self.get_prompt_template("assistant_instructions_json")
            except ConfigError:
                instructions = "Classify content into categories based on their content."
                logger.warning("Using default instructions - no 'assistant_instructions_json' prompt found")
            
            # Create the assistant
            assistant = self.client.beta.assistants.create(
                name=self.config.assistant_name,
                instructions=instructions,
                model=self.config.model,
                temperature=self.config.temperature,
                tools=self.config.tools or [{"type": "code_interpreter"}],
                response_format={"type": self.config.default_response_format}
            )
            
            # Save the assistant ID
            self.config.update_assistant_id(assistant.id)
            logger.info(f"Created new assistant: {assistant.id}")
            
            return assistant.id
            
        except Exception as e:
            error_msg = f"Failed to create assistant: {e}"
            logger.error(error_msg)
            raise APIClientError(error_msg)
    
    def get_or_create_thread(self) -> str:
        """
        Get or create a thread for the classification assistant.
        
        Returns:
            str: The Thread ID
            
        Raises:
            APIClientError: If the thread cannot be created or retrieved
        """
        # Check if client is available
        if not self.client:
            raise APIClientError("OpenAI client not initialized (missing API key)")
            
        # Check if we already have a thread ID
        if self.config.persistent_thread_id:
            try:
                # Verify the thread exists
                thread = self.client.beta.threads.retrieve(self.config.persistent_thread_id)
                logger.debug(f"Using existing thread: {thread.id}")
                return thread.id
            except Exception as e:
                logger.warning(f"Couldn't retrieve thread {self.config.persistent_thread_id}: {e}")
                # Fall through to create a new one
        
        # Create a new thread
        try:
            logger.info("Creating new classification thread")
            thread = self.client.beta.threads.create()
            
            # Save the thread ID
            self.config.update_thread_id(thread.id)
            logger.info(f"Created new thread: {thread.id}")
            
            return thread.id
            
        except Exception as e:
            error_msg = f"Failed to create thread: {e}"
            logger.error(error_msg)
            raise APIClientError(error_msg)
    
    def _format_message(self, input_text: str, prompt_template: str, 
                        template_vars: Optional[Dict[str, Any]] = None) -> str:
        """
        Format the input text using the prompt template.
        
        Args:
            input_text: The input text to classify
            prompt_template: The prompt template text
            template_vars: Optional variables to use in the template
            
        Returns:
            str: The formatted message
        """
        if not template_vars:
            template_vars = {}
        
        # Add input text to template vars
        if 'entry_content' not in template_vars:
            template_vars['entry_content'] = input_text
        
        # Format the template
        try:
            formatted_message = prompt_template.format(**template_vars)
            return formatted_message
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            # Fall back to just using the template with the input text
            return f"{prompt_template}\n\n{input_text}"
    
    def classify_text(self, text: Union[str, Dict[str, Any]], job_id: Optional[int] = None,
                     batch_id: Optional[str] = None, force_new_thread: bool = False) -> str:
        """
        Classify text using the OpenAI assistant.
        
        Args:
            text: The text to classify or a dict containing the text
            job_id: Optional ID of the job being processed
            batch_id: Optional ID of the batch being processed
            force_new_thread: Force creation of a new thread instead of reusing
            
        Returns:
            str: The classification result
            
        Raises:
            ClassificationError: If processing fails
        """
        # Check if client is available
        if not self.client:
            error_msg = "OpenAI client not initialized (missing API key)"
            logger.error(error_msg)
            
            # For dry run or testing, return a mock response
            if getattr(settings, 'DEBUG', False):
                logger.warning("Running in DEBUG mode - returning mock classification response")
                mock_response = '{"classifications":[{"text":"mock text","category":"diary"}]}'
                return mock_response
            else:
                raise APIClientError(error_msg)
        
        start_time = time.time()
        
        try:
            # Extract text content if input is a dictionary
            if isinstance(text, dict):
                content = text.get("text", "")
                if not content and "transcript_content" in text:
                    content = text.get("transcript_content", "")
            else:
                content = text
                
            if not content:
                raise ClassificationError("No content to classify")
                
            # Get prompt templates
            parse_prompt = self.get_prompt_template("parse_entry_prompt")
            
            # Set up template variables
            template_vars = {
                "entry_content": content
            }
            
            # Format the message
            message_text = self._format_message(content, parse_prompt, template_vars)
            
            # Get or create assistant and thread
            assistant_id = self.get_or_create_assistant()
            thread_id = self.get_or_create_thread() if not force_new_thread else None
            
            if force_new_thread:
                # Create a temporary thread
                thread = self.client.beta.threads.create()
                thread_id = thread.id
                logger.debug(f"Created temporary thread: {thread_id}")
            
            # Add message to thread
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message_text
            )
            
            # Create and monitor the run
            retry_count = 0
            while retry_count <= MAX_RETRIES:
                try:
                    # Create run
                    run = self.client.beta.threads.runs.create(
                        thread_id=thread_id,
                        assistant_id=assistant_id
                    )
                    
                    # Poll until complete
                    while run.status in ["queued", "in_progress"]:
                        run = self.client.beta.threads.runs.retrieve(
                            thread_id=thread_id,
                            run_id=run.id
                        )
                        
                        if run.status in ["queued", "in_progress"]:
                            # Wait before polling again
                            time.sleep(1)
                    
                    # Check if completed successfully
                    if run.status == "completed":
                        # Get the response messages
                        messages = self.client.beta.threads.messages.list(
                            thread_id=thread_id
                        )
                        
                        # Extract the last message from the assistant
                        for msg in messages.data:
                            if msg.role == "assistant":
                                response_text = ""
                                for content_item in msg.content:
                                    if content_item.type == "text":
                                        response_text = content_item.text.value
                                        break
                                
                                elapsed_time = time.time() - start_time
                                
                                # Record metrics if configured
                                if self.config.save_usage_stats:
                                    try:
                                        # Calculate tokens and costs (estimated)
                                        if hasattr(run, 'usage') and run.usage:
                                            prompt_tokens = run.usage.prompt_tokens
                                            completion_tokens = run.usage.completion_tokens
                                            total_tokens = prompt_tokens + completion_tokens
                                            
                                            # Estimate cost based on model (these rates might need adjustment)
                                            cost_per_1k_prompt = 0.01  # Default rate
                                            cost_per_1k_completion = 0.03  # Default rate
                                            
                                            if "gpt-4" in self.config.model:
                                                cost_per_1k_prompt = 0.03
                                                cost_per_1k_completion = 0.06
                                            
                                            estimated_cost = (
                                                (prompt_tokens / 1000) * cost_per_1k_prompt +
                                                (completion_tokens / 1000) * cost_per_1k_completion
                                            )
                                        else:
                                            # If usage data isn't available, estimate based on text length
                                            prompt_tokens = len(message_text) // 4  # rough estimate
                                            completion_tokens = len(response_text) // 4  # rough estimate
                                            total_tokens = prompt_tokens + completion_tokens
                                            estimated_cost = total_tokens / 1000 * 0.02  # rough estimate
                                        
                                        # Create metrics record
                                        ClassificationMetrics.objects.create(
                                            batch_id=batch_id or "",
                                            job_id=job_id,
                                            prompt_tokens=prompt_tokens,
                                            completion_tokens=completion_tokens,
                                            total_tokens=total_tokens,
                                            processing_time_ms=int(elapsed_time * 1000),
                                            estimated_cost_usd=estimated_cost,
                                            success=True,
                                            model_used=self.config.model
                                        )
                                    except Exception as metrics_error:
                                        logger.error(f"Failed to record metrics: {metrics_error}")
                                
                                logger.info(f"Classification successful (completed in {elapsed_time:.2f}s)")
                                return response_text
                        
                        # If we get here, no assistant message was found
                        raise ClassificationError("No response from classification assistant")
                    
                    else:
                        # Run failed or was cancelled
                        error_message = f"Run failed with status: {run.status}"
                        if hasattr(run, 'last_error') and run.last_error:
                            error_message += f" - {run.last_error}"
                        
                        if retry_count < MAX_RETRIES:
                            retry_count += 1
                            logger.warning(f"Classification attempt {retry_count} failed: {error_message}. Retrying...")
                            time.sleep(RETRY_DELAY * (BACKOFF_FACTOR ** (retry_count - 1)))
                        else:
                            # Record failed metrics
                            if self.config.save_usage_stats:
                                ClassificationMetrics.objects.create(
                                    batch_id=batch_id or "",
                                    job_id=job_id,
                                    processing_time_ms=int((time.time() - start_time) * 1000),
                                    success=False,
                                    error_message=error_message,
                                    model_used=self.config.model
                                )
                            
                            raise ClassificationError(error_message)
                
                except (APIError, APIConnectionError, RateLimitError) as api_error:
                    if retry_count < MAX_RETRIES:
                        retry_count += 1
                        logger.warning(f"OpenAI API error (attempt {retry_count}): {api_error}. Retrying...")
                        time.sleep(RETRY_DELAY * (BACKOFF_FACTOR ** (retry_count - 1)))
                    else:
                        # Record failed metrics
                        if self.config.save_usage_stats:
                            ClassificationMetrics.objects.create(
                                batch_id=batch_id or "",
                                job_id=job_id,
                                processing_time_ms=int((time.time() - start_time) * 1000),
                                success=False,
                                error_message=str(api_error),
                                model_used=self.config.model
                            )
                        
                        raise ClassificationError(f"OpenAI API error after {MAX_RETRIES} retries: {api_error}")
                
            # This should not be reached, but just in case
            raise ClassificationError("Unexpected error during classification")
            
        except ClassificationError:
            # Re-raise classification errors
            raise
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"Unexpected error during classification: {e} (after {elapsed_time:.2f}s)"
            logger.error(error_msg, exc_info=True)
            
            # Record failed metrics
            if hasattr(self, 'config') and self.config.save_usage_stats:
                try:
                    ClassificationMetrics.objects.create(
                        batch_id=batch_id or "",
                        job_id=job_id,
                        processing_time_ms=int(elapsed_time * 1000),
                        success=False,
                        error_message=str(e),
                        model_used=getattr(self.config, 'model', 'unknown')
                    )
                except Exception as metrics_error:
                    logger.error(f"Failed to record failure metrics: {metrics_error}")
            
            raise ClassificationError(error_msg) 