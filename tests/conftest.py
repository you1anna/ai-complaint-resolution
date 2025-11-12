"""
Pytest configuration and fixtures
"""
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from src.models import Complaint, PolicyDocument, ComplaintStatus
from src.database import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    # Create temporary database file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Initialize database
    db = Database(path)

    yield db

    # Cleanup
    db.close()
    os.unlink(path)


@pytest.fixture
def sample_complaint():
    """Create a sample complaint for testing"""
    return Complaint(
        complaint_id="TEST-001",
        customer_name="Test Customer",
        customer_language="en",
        policy_number="TEST-POL-001",
        claim_reference="CLM-TEST-001",
        complaint_text="""
        Dear Sir/Madam,

        I am writing to complain about the rejection of my travel insurance claim.
        My flight was delayed by 15 hours due to technical issues, and I had to pay
        for accommodation and meals. I submitted all required documentation, but
        my claim was rejected without proper explanation.

        I believe this falls under the travel delay section of my policy and
        request an immediate review of this decision.

        Sincerely,
        Test Customer
        """,
        received_date=datetime.utcnow() - timedelta(days=2),
        deadline_date=datetime.utcnow() + timedelta(days=13),
        status=ComplaintStatus.NEW
    )


@pytest.fixture
def sample_policy():
    """Create a sample policy for testing"""
    return PolicyDocument(
        policy_id="TEST-POL-001",
        policy_name="Test Travel Insurance Policy",
        language="en",
        version="1.0",
        effective_date=datetime(2024, 1, 1),
        content="""
        TEST TRAVEL INSURANCE POLICY

        SECTION 1 - TRAVEL DELAY
        This policy covers travel delays exceeding 12 hours due to:
        - Technical issues with aircraft
        - Severe weather conditions
        - Air traffic control restrictions

        Coverage:
        - £50 for first 12 hours
        - £25 for each additional 12 hours
        - Maximum £200 total

        Requirements:
        - Written confirmation from carrier
        - Receipts for expenses incurred

        SECTION 2 - TRIP CANCELLATION
        Covers cancellation due to:
        - Serious illness or injury
        - Death of family member
        - Compulsory quarantine

        Maximum coverage: £5,000

        SECTION 3 - MEDICAL EXPENSES
        Emergency medical treatment up to £50,000

        Exclusions:
        - Pre-existing conditions not declared
        - Non-emergency treatment
        - Treatment after return to home country
        """
    )


@pytest.fixture
def sample_processed_complaint(sample_complaint):
    """Create a complaint that has been processed"""
    from src.models import ComplaintCategory, UrgencyLevel

    complaint = sample_complaint
    complaint.status = ComplaintStatus.AWAITING_REVIEW
    complaint.predicted_category = ComplaintCategory.TRAVEL_DELAY
    complaint.urgency = UrgencyLevel.MEDIUM
    complaint.confidence_score = 0.92
    complaint.draft_response = "This is a test draft response."
    complaint.requires_review = True

    return complaint


@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock API key for testing"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-123456789")
    return "sk-ant-test-key-123456789"


@pytest.fixture
def sample_workflow_result():
    """Sample workflow result for testing"""
    return {
        "complaint_id": "TEST-001",
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "requires_review": True,
        "review_reasons": ["high_urgency", "policy_analysis_flagged"],
        "stages": {
            "classification": {
                "completed_at": datetime.utcnow().isoformat(),
                "result": {
                    "predicted_category": "travel_delay",
                    "confidence": 0.92,
                    "urgency_level": "medium"
                }
            }
        },
        "metrics": {
            "estimated_manual_time_hours": 4.25,
            "estimated_ai_assisted_time_hours": 1.0,
            "time_saved_hours": 3.25,
            "time_saved_percentage": 76.5
        }
    }
