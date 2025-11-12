"""
Unit tests for validation module
"""
import pytest
from datetime import datetime, timedelta

from src.models import Complaint, PolicyDocument, ComplaintStatus
from src.validators import (
    ComplaintValidator,
    PolicyValidator,
    WorkflowValidator,
    validate_confidence_score
)


class TestComplaintValidator:
    """Test complaint validation"""

    def test_valid_complaint(self):
        """Test validation of valid complaint"""
        complaint = Complaint(
            complaint_id="TEST-001",
            customer_name="Test Customer",
            customer_language="en",
            policy_number="POL-001",
            complaint_text="This is a valid complaint text",
            received_date=datetime.utcnow() - timedelta(days=1),
            deadline_date=datetime.utcnow() + timedelta(days=14),
            status=ComplaintStatus.NEW
        )

        is_valid, errors = ComplaintValidator.validate_complaint(complaint)
        assert is_valid
        assert len(errors) == 0

    def test_missing_complaint_id(self):
        """Test validation fails for missing ID"""
        complaint = Complaint(
            complaint_id="",
            customer_name="Test Customer",
            customer_language="en",
            policy_number="POL-001",
            complaint_text="Test complaint",
            received_date=datetime.utcnow(),
            deadline_date=datetime.utcnow() + timedelta(days=14),
            status=ComplaintStatus.NEW
        )

        is_valid, errors = ComplaintValidator.validate_complaint(complaint)
        assert not is_valid
        assert "Complaint ID is required" in errors

    def test_unsupported_language(self):
        """Test validation fails for unsupported language"""
        complaint = Complaint(
            complaint_id="TEST-001",
            customer_name="Test Customer",
            customer_language="zz",  # Invalid language
            policy_number="POL-001",
            complaint_text="Test complaint",
            received_date=datetime.utcnow(),
            deadline_date=datetime.utcnow() + timedelta(days=14),
            status=ComplaintStatus.NEW
        )

        is_valid, errors = ComplaintValidator.validate_complaint(complaint)
        assert not is_valid
        assert any("Unsupported language" in e for e in errors)

    def test_deadline_before_received(self):
        """Test validation fails when deadline is before received date"""
        complaint = Complaint(
            complaint_id="TEST-001",
            customer_name="Test Customer",
            customer_language="en",
            policy_number="POL-001",
            complaint_text="Test complaint",
            received_date=datetime.utcnow(),
            deadline_date=datetime.utcnow() - timedelta(days=1),  # Before received
            status=ComplaintStatus.NEW
        )

        is_valid, errors = ComplaintValidator.validate_complaint(complaint)
        assert not is_valid
        assert "Deadline date must be after received date" in errors

    def test_complaint_text_too_short(self):
        """Test validation fails for too short complaint text"""
        complaint = Complaint(
            complaint_id="TEST-001",
            customer_name="Test Customer",
            customer_language="en",
            policy_number="POL-001",
            complaint_text="Short",  # Too short
            received_date=datetime.utcnow(),
            deadline_date=datetime.utcnow() + timedelta(days=14),
            status=ComplaintStatus.NEW
        )

        is_valid, errors = ComplaintValidator.validate_complaint(complaint)
        assert not is_valid
        assert any("too short" in e for e in errors)


class TestPolicyValidator:
    """Test policy validation"""

    def test_valid_policy(self):
        """Test validation of valid policy"""
        policy = PolicyDocument(
            policy_id="POL-001",
            policy_name="Test Policy",
            language="en",
            content="This is a valid policy document with sufficient content to pass validation tests.",
            version="1.0",
            effective_date=datetime.utcnow()
        )

        is_valid, errors = PolicyValidator.validate_policy(policy)
        assert is_valid
        assert len(errors) == 0

    def test_missing_policy_id(self):
        """Test validation fails for missing policy ID"""
        policy = PolicyDocument(
            policy_id="",
            policy_name="Test Policy",
            language="en",
            content="Valid content",
            version="1.0",
            effective_date=datetime.utcnow()
        )

        is_valid, errors = PolicyValidator.validate_policy(policy)
        assert not is_valid
        assert "Policy ID is required" in errors

    def test_policy_content_too_short(self):
        """Test validation fails for too short content"""
        policy = PolicyDocument(
            policy_id="POL-001",
            policy_name="Test Policy",
            language="en",
            content="Short",  # Too short
            version="1.0",
            effective_date=datetime.utcnow()
        )

        is_valid, errors = PolicyValidator.validate_policy(policy)
        assert not is_valid
        assert any("too short" in e for e in errors)


class TestConfidenceValidation:
    """Test confidence score validation"""

    def test_valid_confidence_above_threshold(self):
        """Test valid confidence score above threshold"""
        is_valid, message = validate_confidence_score(0.90, threshold=0.85)
        assert is_valid
        assert "meets threshold" in message

    def test_confidence_below_threshold(self):
        """Test confidence score below threshold"""
        is_valid, message = validate_confidence_score(0.70, threshold=0.85)
        assert not is_valid
        assert "below threshold" in message

    def test_invalid_confidence_range(self):
        """Test invalid confidence score (out of range)"""
        is_valid, message = validate_confidence_score(1.5, threshold=0.85)
        assert not is_valid
        assert "Invalid confidence score" in message

        is_valid, message = validate_confidence_score(-0.1, threshold=0.85)
        assert not is_valid
        assert "Invalid confidence score" in message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
