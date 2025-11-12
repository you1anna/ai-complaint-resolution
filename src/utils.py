"""
Utility functions for the complaint resolution system
Provides common functionality used across modules
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to

    Returns:
        Configured logger instance
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def format_datetime(dt: datetime, include_time: bool = True) -> str:
    """
    Format datetime in a consistent, readable format

    Args:
        dt: Datetime to format
        include_time: Whether to include time component

    Returns:
        Formatted datetime string
    """
    if include_time:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return dt.strftime('%Y-%m-%d')


def calculate_days_until(target_date: datetime) -> int:
    """
    Calculate days remaining until a target date

    Args:
        target_date: Target datetime

    Returns:
        Number of days (negative if past due)
    """
    delta = target_date - datetime.utcnow()
    return delta.days


def is_deadline_approaching(deadline: datetime, warning_days: int = 3) -> bool:
    """
    Check if a deadline is approaching

    Args:
        deadline: Deadline datetime
        warning_days: Number of days threshold

    Returns:
        True if deadline is within warning_days
    """
    days_until = calculate_days_until(deadline)
    return 0 <= days_until <= warning_days


def is_overdue(deadline: datetime) -> bool:
    """
    Check if a deadline has passed

    Args:
        deadline: Deadline datetime

    Returns:
        True if deadline has passed
    """
    return calculate_days_until(deadline) < 0


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe file system usage

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')

    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:max_length - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name

    return filename


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """
    Safely parse JSON with fallback

    Args:
        json_string: JSON string to parse
        default: Default value if parsing fails

    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError) as e:
        logging.warning(f"Failed to parse JSON: {str(e)}")
        return default


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON from text that may contain markdown code blocks

    Args:
        text: Text potentially containing JSON

    Returns:
        Extracted JSON string or original text
    """
    # Try to extract from markdown code blocks
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        return text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        return text[start:end].strip()

    # Try to find JSON object
    if "{" in text and "}" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        return text[start:end].strip()

    return text.strip()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def calculate_percentage(part: float, total: float, decimals: int = 1) -> float:
    """
    Calculate percentage with safe division

    Args:
        part: Part value
        total: Total value
        decimals: Number of decimal places

    Returns:
        Percentage value
    """
    if total == 0:
        return 0.0

    percentage = (part / total) * 100
    return round(percentage, decimals)


def format_duration(hours: float) -> str:
    """
    Format duration in hours to human-readable format

    Args:
        hours: Duration in hours

    Returns:
        Formatted duration string (e.g., "2h 30m")
    """
    if hours < 0:
        return "0m"

    hours_int = int(hours)
    minutes = int((hours - hours_int) * 60)

    if hours_int > 0 and minutes > 0:
        return f"{hours_int}h {minutes}m"
    elif hours_int > 0:
        return f"{hours_int}h"
    else:
        return f"{minutes}m"


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, create if it doesn't

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


class ProgressTracker:
    """Simple progress tracker for batch operations"""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.utcnow()

    def update(self, increment: int = 1) -> None:
        """Update progress"""
        self.current += increment
        self._display()

    def _display(self) -> None:
        """Display progress"""
        percentage = calculate_percentage(self.current, self.total)
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()

        if self.current > 0:
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate if rate > 0 else 0
            eta = f"ETA: {int(remaining)}s"
        else:
            eta = "ETA: calculating..."

        print(
            f"\r{self.description}: {self.current}/{self.total} "
            f"({percentage}%) - {eta}",
            end="",
            flush=True
        )

        if self.current >= self.total:
            print()  # New line when complete


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format

    Args:
        api_key: API key to validate

    Returns:
        True if valid format
    """
    if not api_key or api_key == "your_api_key_here":
        return False

    # Basic validation - should start with sk-ant-
    if not api_key.startswith("sk-ant-"):
        logging.warning("API key doesn't match expected format (sk-ant-...)")
        return False

    return True


def dict_to_pretty_string(data: Dict, indent: int = 2) -> str:
    """
    Convert dictionary to pretty-printed string

    Args:
        data: Dictionary to format
        indent: Indentation spaces

    Returns:
        Pretty-printed string
    """
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
