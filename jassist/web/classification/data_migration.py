"""
Data migration utilities for classification.

This module provides utilities to migrate configuration and prompt data
from files to the database.
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import os

from django.db import transaction
from django.utils import timezone

from .models import ClassificationConfig, ClassificationPrompt

logger = logging.getLogger(__name__)

# Configuration file paths
CONFIG_FILE_PATH = Path(__file__).resolve().parent / "config" / "classification_assistant_config.json"
PROMPTS_FILE_PATH = Path(__file__).resolve().parent / "config" / "prompts.yaml"


def migrate_config_to_database() -> Tuple[bool, str]:
    """
    Migrate classification configuration from files to database.
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        # Check if config file exists
        if not CONFIG_FILE_PATH.exists():
            logger.warning(f"Config file not found: {CONFIG_FILE_PATH}")
            return False, f"Config file not found: {CONFIG_FILE_PATH}"
        
        # Load config from file
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # Check if we already have a config in the database
        existing_config = ClassificationConfig.objects.filter(is_active=True).first()
        
        with transaction.atomic():
            if existing_config:
                # Update existing config
                logger.info(f"Updating existing classification config: {existing_config.id}")
                
                # Map fields from file to model
                existing_config.assistant_name = config_data.get("assistant_name", "Classification Assistant")
                existing_config.api_key = config_data.get("api_key", "")
                existing_config.model = config_data.get("model", "gpt-4o")
                existing_config.temperature = config_data.get("temperature", 0.2)
                existing_config.max_tokens = config_data.get("max_tokens", 1000)
                existing_config.top_p = config_data.get("top_p", 1.0)
                existing_config.frequency_penalty = config_data.get("frequency_penalty", 0.0)
                existing_config.presence_penalty = config_data.get("presence_penalty", 0.0)
                existing_config.save_usage_stats = config_data.get("save_usage_stats", True)
                existing_config.thread_retention_days = config_data.get("thread_retention_days", 30)
                existing_config.default_response_format = config_data.get("default_response_format", "json")
                existing_config.tools = config_data.get("tools", [{"type": "code_interpreter"}])
                
                # Assistant and thread IDs
                existing_config.assistant_id = config_data.get("assistant_id_classification_assistant", "")
                existing_config.persistent_thread_id = config_data.get("thread_id_classification_assistant_persistent", "")
                
                # Try to parse thread creation date
                thread_created_at = config_data.get("thread_id_classification_assistant_persistent_created_at", "")
                if thread_created_at:
                    try:
                        existing_config.persistent_thread_created_at = thread_created_at
                    except Exception as e:
                        logger.warning(f"Could not parse thread creation date: {e}")
                
                existing_config.updated_at = timezone.now()
                existing_config.save()
                
                logger.info(f"Updated classification config in database (ID: {existing_config.id})")
                config_obj = existing_config
            else:
                # Create new config
                logger.info("Creating new classification config in database")
                
                # Map fields from file to model
                config_obj = ClassificationConfig.objects.create(
                    assistant_name=config_data.get("assistant_name", "Classification Assistant"),
                    api_key=config_data.get("api_key", ""),
                    model=config_data.get("model", "gpt-4o"),
                    temperature=config_data.get("temperature", 0.2),
                    max_tokens=config_data.get("max_tokens", 1000),
                    top_p=config_data.get("top_p", 1.0),
                    frequency_penalty=config_data.get("frequency_penalty", 0.0),
                    presence_penalty=config_data.get("presence_penalty", 0.0),
                    save_usage_stats=config_data.get("save_usage_stats", True),
                    thread_retention_days=config_data.get("thread_retention_days", 30),
                    default_response_format=config_data.get("default_response_format", "json"),
                    tools=config_data.get("tools", [{"type": "code_interpreter"}]),
                    assistant_id=config_data.get("assistant_id_classification_assistant", ""),
                    persistent_thread_id=config_data.get("thread_id_classification_assistant_persistent", ""),
                    is_active=True
                )
                
                # Try to parse thread creation date
                thread_created_at = config_data.get("thread_id_classification_assistant_persistent_created_at", "")
                if thread_created_at:
                    try:
                        config_obj.persistent_thread_created_at = thread_created_at
                        config_obj.save(update_fields=['persistent_thread_created_at'])
                    except Exception as e:
                        logger.warning(f"Could not parse thread creation date: {e}")
                
                logger.info(f"Created classification config in database (ID: {config_obj.id})")
        
        return True, f"Successfully migrated configuration from file to database (ID: {config_obj.id})"
        
    except Exception as e:
        logger.exception(f"Error migrating config to database: {e}")
        return False, f"Error migrating config to database: {e}"


def migrate_prompts_to_database() -> Tuple[bool, str]:
    """
    Migrate classification prompts from files to database.
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        # Check if prompts file exists
        if not PROMPTS_FILE_PATH.exists():
            logger.warning(f"Prompts file not found: {PROMPTS_FILE_PATH}")
            return False, f"Prompts file not found: {PROMPTS_FILE_PATH}"
        
        # Load prompts from file
        with open(PROMPTS_FILE_PATH, "r", encoding="utf-8") as f:
            prompts_data = yaml.safe_load(f)
        
        prompts = prompts_data.get("prompts", {})
        if not prompts:
            logger.warning("No prompts found in prompts file")
            return False, "No prompts found in prompts file"
        
        # Create or update prompts in database
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for name, prompt_data in prompts.items():
                if "template" not in prompt_data:
                    logger.warning(f"Prompt '{name}' has no template field, skipping")
                    continue
                
                template = prompt_data["template"]
                description = f"Migrated from {PROMPTS_FILE_PATH.name}"
                
                # Check if prompt already exists
                existing_prompt = ClassificationPrompt.objects.filter(name=name).first()
                
                if existing_prompt:
                    # Update existing prompt
                    existing_prompt.template = template
                    existing_prompt.description = description
                    existing_prompt.is_active = True
                    existing_prompt.updated_at = timezone.now()
                    existing_prompt.save()
                    
                    updated_count += 1
                    logger.debug(f"Updated prompt '{name}' in database (ID: {existing_prompt.id})")
                else:
                    # Create new prompt
                    new_prompt = ClassificationPrompt.objects.create(
                        name=name,
                        template=template,
                        description=description,
                        is_active=True
                    )
                    
                    created_count += 1
                    logger.debug(f"Created prompt '{name}' in database (ID: {new_prompt.id})")
        
        logger.info(f"Migrated {created_count + updated_count} prompts from file to database "
                   f"({created_count} created, {updated_count} updated)")
        
        return True, f"Successfully migrated {created_count + updated_count} prompts from file to database"
        
    except Exception as e:
        logger.exception(f"Error migrating prompts to database: {e}")
        return False, f"Error migrating prompts to database: {e}"


def remove_config_files() -> Tuple[bool, str]:
    """
    Remove old configuration files after migration.
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        files_removed = []
        
        # Remove config file if it exists
        if CONFIG_FILE_PATH.exists():
            os.remove(CONFIG_FILE_PATH)
            files_removed.append(str(CONFIG_FILE_PATH))
            logger.info(f"Removed config file: {CONFIG_FILE_PATH}")
        
        # Remove prompts file if it exists
        if PROMPTS_FILE_PATH.exists():
            os.remove(PROMPTS_FILE_PATH)
            files_removed.append(str(PROMPTS_FILE_PATH))
            logger.info(f"Removed prompts file: {PROMPTS_FILE_PATH}")
        
        if files_removed:
            return True, f"Successfully removed files: {', '.join(files_removed)}"
        else:
            return False, "No files to remove"
        
    except Exception as e:
        logger.exception(f"Error removing config files: {e}")
        return False, f"Error removing config files: {e}"


def perform_full_migration() -> Tuple[bool, str]:
    """
    Perform a full migration from files to database.
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    messages = []
    success = True
    
    # Migrate config
    config_success, config_message = migrate_config_to_database()
    success = success and config_success
    messages.append(f"Config migration: {config_message}")
    
    # Migrate prompts
    prompts_success, prompts_message = migrate_prompts_to_database()
    success = success and prompts_success
    messages.append(f"Prompts migration: {prompts_message}")
    
    # Remove files if migration was successful
    if success:
        remove_success, remove_message = remove_config_files()
        messages.append(f"File cleanup: {remove_message}")
    
    # Combine messages
    final_message = "\n".join(messages)
    
    return success, final_message 