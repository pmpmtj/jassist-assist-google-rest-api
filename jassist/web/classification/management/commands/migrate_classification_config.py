"""
Management command to migrate classification configuration.

This command migrates classification configuration from files to the database.
"""

import logging
from django.core.management.base import BaseCommand, CommandError

from jassist.web.classification.data_migration import (
    migrate_config_to_database,
    migrate_prompts_to_database,
    remove_config_files,
    perform_full_migration
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management command to migrate classification configuration.
    """
    
    help = "Migrate classification configuration from files to the database"
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--config-only',
            action='store_true',
            help='Only migrate configuration, not prompts'
        )
        parser.add_argument(
            '--prompts-only',
            action='store_true',
            help='Only migrate prompts, not configuration'
        )
        parser.add_argument(
            '--remove-files',
            action='store_true',
            help='Remove configuration files after migration'
        )
        parser.add_argument(
            '--keep-files',
            action='store_true',
            help='Keep configuration files after migration'
        )
    
    def handle(self, *args, **options):
        """Run the command."""
        try:
            # Parse options
            config_only = options.get('config_only', False)
            prompts_only = options.get('prompts_only', False)
            remove_files = options.get('remove_files', False)
            keep_files = options.get('keep_files', False)
            
            # Validate options
            if config_only and prompts_only:
                raise CommandError("Cannot specify both --config-only and --prompts-only")
            
            if remove_files and keep_files:
                raise CommandError("Cannot specify both --remove-files and --keep-files")
            
            # Default is to remove files unless --keep-files is specified
            should_remove_files = remove_files or (not keep_files)
            
            # Determine migration mode
            if config_only:
                # Migrate only configuration
                self.stdout.write("Migrating only configuration...")
                success, message = migrate_config_to_database()
                self.stdout.write(message)
                
                if success and should_remove_files:
                    # Remove config file
                    self.stdout.write("Removing configuration file...")
                    from pathlib import Path
                    import os
                    config_file = Path(__file__).resolve().parent.parent.parent / "config" / "classification_assistant_config.json"
                    if config_file.exists():
                        os.remove(config_file)
                        self.stdout.write(f"Removed: {config_file}")
                    else:
                        self.stdout.write(f"File not found: {config_file}")
                
            elif prompts_only:
                # Migrate only prompts
                self.stdout.write("Migrating only prompts...")
                success, message = migrate_prompts_to_database()
                self.stdout.write(message)
                
                if success and should_remove_files:
                    # Remove prompts file
                    self.stdout.write("Removing prompts file...")
                    from pathlib import Path
                    import os
                    prompts_file = Path(__file__).resolve().parent.parent.parent / "config" / "prompts.yaml"
                    if prompts_file.exists():
                        os.remove(prompts_file)
                        self.stdout.write(f"Removed: {prompts_file}")
                    else:
                        self.stdout.write(f"File not found: {prompts_file}")
                
            else:
                # Migrate everything
                self.stdout.write("Performing full migration...")
                success, message = perform_full_migration()
                self.stdout.write(message)
            
            # Report final status
            if success:
                self.stdout.write(self.style.SUCCESS("Migration completed successfully"))
            else:
                self.stdout.write(self.style.ERROR("Migration completed with errors"))
                return 1
            
            return 0
            
        except Exception as e:
            logger.exception(f"Error in classification config migration: {e}")
            raise CommandError(f"Command failed: {e}") 