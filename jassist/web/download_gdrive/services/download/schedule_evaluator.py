"""
Schedule Evaluator module.

This module handles evaluating download schedules and determining
when downloads should run.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Union
from django.utils import timezone

# Try to import croniter for cron expression parsing
try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False

# Create a logger
logger = logging.getLogger(__name__)

class ScheduleEvaluator:
    """
    Evaluates schedules to determine when downloads should run.
    """
    def __init__(self):
        """Initialize the schedule evaluator."""
        self.schedule_types = {
            "hourly": self._check_hourly,
            "daily": self._check_daily,
            "weekly": self._check_weekly,
            "monthly": self._check_monthly,
            "cron": self._check_cron
        }
    
    def should_run_now(self, schedule_expression: str, last_run: Optional[datetime] = None) -> bool:
        """
        Determine if a download should run now based on schedule and last run time.
        
        Args:
            schedule_expression (str): Schedule expression (e.g., "daily", "weekly:monday", "cron:0 0 * * *")
            last_run (Optional[datetime]): Last time the download was run
            
        Returns:
            bool: True if the download should run now, False otherwise
        """
        if not schedule_expression:
            logger.debug("No schedule expression provided, defaulting to run")
            return True
        
        # If no last run, always run
        if not last_run:
            logger.debug("No last run timestamp, running download")
            return True
        
        try:
            # Split schedule type and parameters
            parts = schedule_expression.split(":", 1)
            schedule_type = parts[0].strip().lower()
            
            # Parameters are everything after the first colon
            parameters = parts[1].strip() if len(parts) > 1 else ""
            
            # Check if we have a handler for this schedule type
            if schedule_type in self.schedule_types:
                return self.schedule_types[schedule_type](parameters, last_run)
            else:
                logger.warning(f"Unknown schedule type: {schedule_type}, defaulting to run")
                return True
                
        except Exception as e:
            logger.error(f"Error evaluating schedule '{schedule_expression}': {e}")
            # Default to run on error
            return True
    
    def calculate_next_run(self, schedule_expression: str, last_run: Optional[datetime] = None) -> Optional[datetime]:
        """
        Calculate the next scheduled run time.
        
        Args:
            schedule_expression (str): Schedule expression
            last_run (Optional[datetime]): Last time the download was run
            
        Returns:
            Optional[datetime]: Next scheduled run time or None if cannot be determined
        """
        if not schedule_expression:
            return None
            
        if not last_run:
            return timezone.now()
        
        try:
            # Split schedule type and parameters
            parts = schedule_expression.split(":", 1)
            schedule_type = parts[0].strip().lower()
            parameters = parts[1].strip() if len(parts) > 1 else ""
            
            # Calculate based on schedule type
            if schedule_type == "hourly":
                hours = int(parameters) if parameters else 1
                return last_run + timedelta(hours=hours)
                
            elif schedule_type == "daily":
                days = int(parameters) if parameters else 1
                return last_run + timedelta(days=days)
                
            elif schedule_type == "weekly":
                return self._calculate_next_weekly(parameters, last_run)
                
            elif schedule_type == "monthly":
                return self._calculate_next_monthly(parameters, last_run)
                
            elif schedule_type == "cron" and CRONITER_AVAILABLE:
                cron_expression = parameters or "0 0 * * *"  # Default to midnight every day
                cron = croniter(cron_expression, last_run)
                return cron.get_next(datetime)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating next run for '{schedule_expression}': {e}")
            return None
    
    def _check_hourly(self, parameters: str, last_run: datetime) -> bool:
        """
        Check if an hourly schedule should run now.
        
        Args:
            parameters (str): Hours between runs (default: 1)
            last_run (datetime): Last run time
            
        Returns:
            bool: True if should run now
        """
        try:
            hours = int(parameters) if parameters else 1
            next_run = last_run + timedelta(hours=hours)
            should_run = timezone.now() >= next_run
            
            if should_run:
                logger.debug(f"Hourly schedule ({hours}h) due to run")
            
            return should_run
            
        except ValueError:
            logger.warning(f"Invalid hourly parameter: {parameters}, defaulting to 1 hour")
            next_run = last_run + timedelta(hours=1)
            return timezone.now() >= next_run
    
    def _check_daily(self, parameters: str, last_run: datetime) -> bool:
        """
        Check if a daily schedule should run now.
        
        Args:
            parameters (str): Days between runs (default: 1)
            last_run (datetime): Last run time
            
        Returns:
            bool: True if should run now
        """
        try:
            days = int(parameters) if parameters else 1
            next_run = last_run + timedelta(days=days)
            should_run = timezone.now() >= next_run
            
            if should_run:
                logger.debug(f"Daily schedule ({days}d) due to run")
            
            return should_run
            
        except ValueError:
            logger.warning(f"Invalid daily parameter: {parameters}, defaulting to 1 day")
            next_run = last_run + timedelta(days=1)
            return timezone.now() >= next_run
    
    def _check_weekly(self, parameters: str, last_run: datetime) -> bool:
        """
        Check if a weekly schedule should run now.
        
        Args:
            parameters (str): Day of week (e.g., "monday", "tuesday", etc.)
            last_run (datetime): Last run time
            
        Returns:
            bool: True if should run now
        """
        # Days of week mapping (0 = Monday, 6 = Sunday)
        days_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        # Default to Monday if no day specified
        target_day = days_map.get(parameters.lower(), 0) if parameters else 0
        
        # Calculate days since last run
        days_since_run = (timezone.now() - last_run).days
        
        # If it has been less than 7 days, check if we've passed the target day this week
        if days_since_run < 7:
            current_weekday = timezone.now().weekday()
            last_run_weekday = last_run.weekday()
            
            # If we're in a different week, or we've passed the target day this week
            if (current_weekday < last_run_weekday) or (current_weekday >= target_day > last_run_weekday):
                logger.debug(f"Weekly schedule (day {target_day}) due to run")
                return True
            return False
        
        # If it has been 7+ days, definitely run
        logger.debug("Weekly schedule due to run (7+ days since last run)")
        return True
    
    def _calculate_next_weekly(self, parameters: str, last_run: datetime) -> datetime:
        """
        Calculate next run time for weekly schedule.
        
        Args:
            parameters (str): Day of week
            last_run (datetime): Last run time
            
        Returns:
            datetime: Next run time
        """
        days_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        target_day = days_map.get(parameters.lower(), 0) if parameters else 0
        current_day = last_run.weekday()
        
        # Days to add to reach the target day
        days_to_add = (target_day - current_day) % 7
        if days_to_add == 0:
            days_to_add = 7  # If today is the target day, go to next week
        
        return last_run + timedelta(days=days_to_add)
    
    def _check_monthly(self, parameters: str, last_run: datetime) -> bool:
        """
        Check if a monthly schedule should run now.
        
        Args:
            parameters (str): Day of month (1-31)
            last_run (datetime): Last run time
            
        Returns:
            bool: True if should run now
        """
        # Default to 1st day of month if not specified
        try:
            target_day = int(parameters) if parameters else 1
            # Clamp to valid range
            target_day = max(1, min(31, target_day))
        except ValueError:
            logger.warning(f"Invalid monthly parameter: {parameters}, defaulting to day 1")
            target_day = 1
        
        now = timezone.now()
        
        # If we're in a new month from last run
        if (now.year > last_run.year) or (now.month > last_run.month):
            # Check if we've passed the target day this month
            if now.day >= target_day:
                logger.debug(f"Monthly schedule (day {target_day}) due to run")
                return True
        
        return False
    
    def _calculate_next_monthly(self, parameters: str, last_run: datetime) -> datetime:
        """
        Calculate next run time for monthly schedule.
        
        Args:
            parameters (str): Day of month
            last_run (datetime): Last run time
            
        Returns:
            datetime: Next run time
        """
        try:
            target_day = int(parameters) if parameters else 1
            # Clamp to valid range
            target_day = max(1, min(31, target_day))
        except ValueError:
            target_day = 1
        
        # Start with last run
        next_date = last_run
        
        # Move to the next month
        if next_date.month == 12:
            next_date = next_date.replace(year=next_date.year + 1, month=1, day=1)
        else:
            next_date = next_date.replace(month=next_date.month + 1, day=1)
        
        # Adjust to target day, clamping to month end if needed
        import calendar
        month_days = calendar.monthrange(next_date.year, next_date.month)[1]
        actual_day = min(target_day, month_days)
        
        return next_date.replace(day=actual_day)
    
    def _check_cron(self, cron_expression: str, last_run: datetime) -> bool:
        """
        Check if a cron schedule should run now.
        
        Args:
            cron_expression (str): Cron expression (e.g., "0 0 * * *")
            last_run (datetime): Last run time
            
        Returns:
            bool: True if should run now
        """
        if not CRONITER_AVAILABLE:
            logger.warning("croniter package not available, defaulting to run")
            return True
            
        # Default to midnight every day if not specified
        cron_expression = cron_expression or "0 0 * * *"
        
        try:
            # Create croniter instance
            cron = croniter(cron_expression, last_run)
            
            # Get next run time after last_run
            next_run = cron.get_next(datetime)
            
            # Check if we've passed it
            should_run = timezone.now() >= next_run
            
            if should_run:
                logger.debug(f"Cron schedule ({cron_expression}) due to run")
            
            return should_run
            
        except Exception as e:
            logger.warning(f"Error parsing cron expression '{cron_expression}': {e}, defaulting to run")
            return True 