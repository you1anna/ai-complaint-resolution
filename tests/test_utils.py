"""
Unit tests for utility functions
"""
import pytest
from datetime import datetime, timedelta
from src.utils import (
    format_datetime,
    calculate_days_until,
    is_deadline_approaching,
    is_overdue,
    sanitize_filename,
    truncate_text,
    calculate_percentage,
    format_duration,
    extract_json_from_text
)


class TestDateUtils:
    """Test date utility functions"""

    def test_format_datetime_with_time(self):
        """Test datetime formatting with time"""
        dt = datetime(2024, 11, 15, 14, 30, 45)
        result = format_datetime(dt, include_time=True)
        assert result == "2024-11-15 14:30:45"

    def test_format_datetime_without_time(self):
        """Test datetime formatting without time"""
        dt = datetime(2024, 11, 15, 14, 30, 45)
        result = format_datetime(dt, include_time=False)
        assert result == "2024-11-15"

    def test_calculate_days_until_future(self):
        """Test calculating days until future date"""
        future = datetime.utcnow() + timedelta(days=5)
        days = calculate_days_until(future)
        assert days == 5

    def test_calculate_days_until_past(self):
        """Test calculating days until past date (negative)"""
        past = datetime.utcnow() - timedelta(days=3)
        days = calculate_days_until(past)
        assert days == -3

    def test_is_deadline_approaching(self):
        """Test deadline approaching detection"""
        approaching = datetime.utcnow() + timedelta(days=2)
        assert is_deadline_approaching(approaching, warning_days=3) is True

        far_future = datetime.utcnow() + timedelta(days=10)
        assert is_deadline_approaching(far_future, warning_days=3) is False

    def test_is_overdue(self):
        """Test overdue detection"""
        past = datetime.utcnow() - timedelta(days=1)
        assert is_overdue(past) is True

        future = datetime.utcnow() + timedelta(days=1)
        assert is_overdue(future) is False


class TestStringUtils:
    """Test string utility functions"""

    def test_sanitize_filename(self):
        """Test filename sanitization"""
        unsafe = "complaint:2024/11/15.txt"
        safe = sanitize_filename(unsafe)
        assert ":" not in safe
        assert "/" not in safe
        assert "_" in safe

    def test_sanitize_filename_long(self):
        """Test filename sanitization with length limit"""
        long_name = "a" * 300 + ".txt"
        safe = sanitize_filename(long_name)
        assert len(safe) <= 255

    def test_truncate_text(self):
        """Test text truncation"""
        long_text = "This is a very long text that needs to be truncated"
        short = truncate_text(long_text, max_length=20)
        assert len(short) <= 20
        assert short.endswith("...")

    def test_truncate_text_already_short(self):
        """Test truncation of already short text"""
        short_text = "Short"
        result = truncate_text(short_text, max_length=20)
        assert result == short_text


class TestMathUtils:
    """Test mathematical utility functions"""

    def test_calculate_percentage(self):
        """Test percentage calculation"""
        result = calculate_percentage(25, 100)
        assert result == 25.0

        result = calculate_percentage(1, 3, decimals=2)
        assert result == 33.33

    def test_calculate_percentage_zero_total(self):
        """Test percentage calculation with zero total (safe division)"""
        result = calculate_percentage(10, 0)
        assert result == 0.0

    def test_format_duration(self):
        """Test duration formatting"""
        assert format_duration(2.5) == "2h 30m"
        assert format_duration(1.0) == "1h"
        assert format_duration(0.5) == "30m"
        assert format_duration(0.0) == "0m"
        assert format_duration(3.75) == "3h 45m"


class TestJSONUtils:
    """Test JSON utility functions"""

    def test_extract_json_from_markdown(self):
        """Test extracting JSON from markdown code block"""
        text = '''Here is some JSON:
```json
{"key": "value"}
```
End of text'''
        result = extract_json_from_text(text)
        assert result == '{"key": "value"}'

    def test_extract_json_from_plain_block(self):
        """Test extracting JSON from plain code block"""
        text = '''Some text
```
{"key": "value"}
```'''
        result = extract_json_from_text(text)
        assert result == '{"key": "value"}'

    def test_extract_json_from_text(self):
        """Test extracting JSON from plain text"""
        text = 'Before text {"key": "value"} After text'
        result = extract_json_from_text(text)
        assert result == '{"key": "value"}'

    def test_extract_json_no_json(self):
        """Test extracting from text without JSON"""
        text = "No JSON here"
        result = extract_json_from_text(text)
        assert result == text.strip()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
