"""
Utils Module
Utility functions for logging, helpers, and common operations.
"""

import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from functools import wraps

from config.settings import Config


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup and return a configured logger.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level if not Config.DEBUG else logging.DEBUG)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    # Also log to file
    log_file = Config.LOGS_DIR / f"{name}.log"
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file: {e}")
    
    return logger


def async_timer(func):
    """
    Decorator to time async function execution.
    
    Usage:
        @async_timer
        async def my_function():
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = datetime.now()
        result = await func(*args, **kwargs)
        end = datetime.now()
        duration = (end - start).total_seconds() * 1000  # ms
        print(f"[TIMER] {func.__name__} took {duration:.2f}ms")
        return result
    return wrapper


def retry_async(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry async function on failure.
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"[RETRY] {func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}")
                        await asyncio.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input for safety.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Truncate if too long
    text = text[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = [';', '|', '&', '$', '`', '(', ')', '{', '}', '[', ']']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


class RateLimiter:
    """
    Async rate limiter for controlling request frequency.
    """
    
    def __init__(self, calls_per_second: float = 1.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_call: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Wait until rate limit allows proceeding."""
        async with self._lock:
            if self.last_call:
                elapsed = (datetime.now() - self.last_call).total_seconds()
                if elapsed < self.min_interval:
                    wait_time = self.min_interval - elapsed
                    await asyncio.sleep(wait_time)
            
            self.last_call = datetime.now()


class Debouncer:
    """
    Debounce function calls to prevent rapid repeated execution.
    """
    
    def __init__(self, delay: float = 0.5):
        self.delay = delay
        self._task: Optional[asyncio.Task] = None
        self._pending_args: Optional[tuple] = None
    
    def debounce(self, func):
        """Decorator to debounce a function."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            self._pending_args = (args, kwargs)
            
            if self._task and not self._task.done():
                self._task.cancel()
            
            async def execute():
                await asyncio.sleep(self.delay)
                if self._pending_args:
                    args, kwargs = self._pending_args
                    return await func(*args, **kwargs)
            
            self._task = asyncio.create_task(execute())
            return await self._task
        
        return wrapper


def ensure_dir(path: Path) -> None:
    """
    Ensure directory exists, creating if necessary.
    
    Args:
        path: Directory path to ensure
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory {path}: {e}")


def get_timestamp() -> str:
    """Get current timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# Create default logger
logger = setup_logger("jarvis_utils")
