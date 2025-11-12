"""
Validation utilities for complaint resolution system
Ensures data quality and business rule compliance
"""
import logging
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from .models import Complaint, PolicyDocument, ComplaintStatus
from .config import SUPPORTED_LANGUAGES, SLA_TIMELINES

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class ComplaintValidator:
    """Validates complaint data and business rules"""

    @staticmethod
    def validate_complaint(complaint: Complaint) -> Tuple[bool, List[str]]:
        """
        Validate complaint data

        Args:
            complaint: Complaint to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Required fields
        if not complaint.complaint_id:
            errors.append("Complaint ID is required")

        if not complaint.customer_name or not complaint.customer_name.strip():
            errors.append("Customer name is required")

        if not complaint.complaint_text or not complaint.complaint_text.strip():
            errors.append("Complaint text is required")

        if not complaint.policy_number:
            errors.append("Policy number is required")

        # Language validation
        if complaint.customer_language not in SUPPORTED_LANGUAGES:
            errors.append(
                f"Unsupported language: {complaint.customer_language}. "
                f"Supported: {', '.join(SUPPORTED_LANGUAGES)}"
            )

        # Date validation
        if complaint.deadline_date <= complaint.received_date:
            errors.append("Deadline date must be after received date")

        # Check if deadline is realistic (not too far in future)
        max_deadline = complaint.received_date + timedelta(days=365)
        if complaint.deadline_date > max_deadline:
            errors.append("Deadline date is too far in the future (>1 year)")

        # Complaint text length validation
        if len(complaint.complaint_text) < 10:
            errors.append("Complaint text is too short (minimum 10 characters)")

        if len(complaint.complaint_text) > 50000:
            errors.append("Complaint text is too long (maximum 50,000 characters)")

        return len(errors) == 0, errors

    @staticmethod
    def validate_sla_compliance(complaint: Complaint) -> Tuple[bool, str]:
        """
        Check if complaint is within SLA timelines

        Args:
            complaint: Complaint to check

        Returns:
            Tuple of (is_compliant, message)
        """
        days_until_deadline = (complaint.deadline_date - datetime.utcnow()).days

        if days_until_deadline < 0:
            return False, f"SLA BREACH: Deadline passed {abs(days_until_deadline)} days ago"

        if days_until_deadline <= 3:
            return True, f"URGENT: Only {days_until_deadline} days until deadline"

        if days_until_deadline <= 7:
            return True, f"WARNING: {days_until_deadline} days until deadline"

        return True, f"On track: {days_until_deadline} days until deadline"

    @staticmethod
    def validate_for_processing(complaint: Complaint) -> Tuple[bool, List[str]]:
        """
        Validate that complaint is ready for AI processing

        Args:
            complaint: Complaint to validate

        Returns:
            Tuple of (is_ready, list_of_blockers)
        """
        blockers = []

        # Check status
        if complaint.status not in [ComplaintStatus.NEW, ComplaintStatus.ANALYZING]:
            blockers.append(
                f"Complaint status is '{complaint.status.value}', "
                f"expected 'new' or 'analyzing'"
            )

        # Check if already processed
        if complaint.draft_response and complaint.status == ComplaintStatus.AWAITING_REVIEW:
            blockers.append("Complaint already has a draft response awaiting review")

        # Basic validation
        is_valid, errors = ComplaintValidator.validate_complaint(complaint)
        if not is_valid:
            blockers.extend(errors)

        return len(blockers) == 0, blockers


class PolicyValidator:
    """Validates policy document data"""

    @staticmethod
    def validate_policy(policy: PolicyDocument) -> Tuple[bool, List[str]]:
        """
        Validate policy document data

        Args:
            policy: Policy to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Required fields
        if not policy.policy_id:
            errors.append("Policy ID is required")

        if not policy.policy_name or not policy.policy_name.strip():
            errors.append("Policy name is required")

        if not policy.content or not policy.content.strip():
            errors.append("Policy content is required")

        if not policy.version:
            errors.append("Policy version is required")

        # Language validation
        if policy.language not in SUPPORTED_LANGUAGES:
            errors.append(
                f"Unsupported language: {policy.language}. "
                f"Supported: {', '.join(SUPPORTED_LANGUAGES)}"
            )

        # Content length validation
        if len(policy.content) < 100:
            errors.append("Policy content is too short (minimum 100 characters)")

        # Effective date validation
        if policy.effective_date > datetime.utcnow():
            logger.warning(f"Policy {policy.policy_id} has future effective date")

        return len(errors) == 0, errors

    @staticmethod
    def check_policy_currency(policy: PolicyDocument, max_age_days: int = 1825) -> Tuple[bool, str]:
        """
        Check if policy is current (not too old)

        Args:
            policy: Policy to check
            max_age_days: Maximum age in days (default: 5 years)

        Returns:
            Tuple of (is_current, message)
        """
        age_days = (datetime.utcnow() - policy.effective_date).days

        if age_days > max_age_days:
            return False, f"Policy is {age_days} days old (may be outdated)"

        if age_days > max_age_days * 0.8:  # 80% of max age
            return True, f"Policy is {age_days} days old (consider review)"

        return True, f"Policy is current ({age_days} days old)"


class WorkflowValidator:
    """Validates workflow operations"""

    @staticmethod
    def validate_for_review(complaint: Complaint) -> Tuple[bool, List[str]]:
        """
        Validate that complaint is ready for human review

        Args:
            complaint: Complaint to validate

        Returns:
            Tuple of (is_ready, list_of_blockers)
        """
        blockers = []

        # Check status
        if complaint.status != ComplaintStatus.AWAITING_REVIEW:
            blockers.append(
                f"Complaint status is '{complaint.status.value}', "
                f"expected 'awaiting_review'"
            )

        # Check for draft response
        if not complaint.draft_response:
            blockers.append("No draft response available for review")

        # Check for AI analysis results
        if not complaint.predicted_category:
            blockers.append("Complaint has not been classified")

        if complaint.confidence_score is None:
            blockers.append("No confidence score available")

        return len(blockers) == 0, blockers

    @staticmethod
    def validate_for_approval(complaint: Complaint, reviewer_name: str) -> Tuple[bool, List[str]]:
        """
        Validate approval operation

        Args:
            complaint: Complaint to approve
            reviewer_name: Name of reviewer

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check reviewer name
        if not reviewer_name or not reviewer_name.strip():
            errors.append("Reviewer name is required")

        # Check complaint is ready for review
        is_ready, blockers = WorkflowValidator.validate_for_review(complaint)
        if not is_ready:
            errors.extend(blockers)

        return len(errors) == 0, errors


def validate_confidence_score(score: float, threshold: float = 0.85) -> Tuple[bool, str]:
    """
    Validate confidence score against threshold

    Args:
        score: Confidence score (0.0 to 1.0)
        threshold: Minimum acceptable score

    Returns:
        Tuple of (meets_threshold, message)
    """
    if not 0.0 <= score <= 1.0:
        return False, f"Invalid confidence score: {score} (must be 0.0-1.0)"

    if score < threshold:
        return False, f"Confidence score {score:.2%} below threshold {threshold:.2%}"

    return True, f"Confidence score {score:.2%} meets threshold"


def validate_api_configuration() -> Tuple[bool, List[str]]:
    """
    Validate that API configuration is correct

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    from .config import settings

    errors = []

    # Check API key
    if not settings.anthropic_api_key:
        errors.append("ANTHROPIC_API_KEY not set in environment")
    elif settings.anthropic_api_key == "your_api_key_here":
        errors.append("ANTHROPIC_API_KEY is set to placeholder value")
    elif not settings.anthropic_api_key.startswith("sk-ant-"):
        errors.append("ANTHROPIC_API_KEY has invalid format (should start with sk-ant-)")

    # Check model
    if not settings.claude_model:
        errors.append("CLAUDE_MODEL not set")

    # Check confidence threshold
    if not 0.0 <= settings.confidence_threshold <= 1.0:
        errors.append(
            f"Invalid CONFIDENCE_THRESHOLD: {settings.confidence_threshold} "
            f"(must be 0.0-1.0)"
        )

    return len(errors) == 0, errors
