"""
Data models for complaint resolution system
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class ComplaintCategory(str, Enum):
    """Complaint categories"""
    CLAIM_REJECTION = "claim_rejection"
    SERVICE_QUALITY = "service_quality"
    POLICY_INTERPRETATION = "policy_interpretation"
    MEDICAL_COVERAGE = "medical_coverage"
    TRIP_CANCELLATION = "trip_cancellation"
    BAGGAGE_LOSS = "baggage_loss"
    TRAVEL_DELAY = "travel_delay"
    COMMUNICATION_ISSUE = "communication_issue"


class UrgencyLevel(str, Enum):
    """Urgency levels for triage"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplaintStatus(str, Enum):
    """Complaint processing status"""
    NEW = "new"
    ANALYZING = "analyzing"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class Complaint(BaseModel):
    """Complaint data model"""
    complaint_id: str
    customer_name: str
    customer_language: str
    policy_number: str
    claim_reference: Optional[str] = None
    complaint_text: str
    received_date: datetime
    deadline_date: datetime
    category: Optional[ComplaintCategory] = None
    urgency: Optional[UrgencyLevel] = None
    status: ComplaintStatus = ComplaintStatus.NEW

    # AI Analysis results
    predicted_category: Optional[ComplaintCategory] = None
    predicted_outcome: Optional[str] = None
    confidence_score: Optional[float] = None

    # Generated response
    draft_response: Optional[str] = None
    final_response: Optional[str] = None

    # Human review
    requires_review: bool = True
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    review_date: Optional[datetime] = None


class PolicyDocument(BaseModel):
    """Policy document model"""
    policy_id: str
    policy_name: str
    language: str
    content: str
    version: str
    effective_date: datetime

    # Parsed sections
    coverage_terms: Optional[dict] = None
    exclusions: Optional[List[str]] = None
    key_clauses: Optional[dict] = None


class PolicyAnalysisResult(BaseModel):
    """Result of policy analysis"""
    policy_id: str
    complaint_id: str
    relevant_clauses: List[str]
    coverage_decision: str  # "covered", "not_covered", "partial", "unclear"
    reasoning: str
    exclusions_applied: List[str]
    confidence: float
    requires_human_review: bool


class ResponseDraft(BaseModel):
    """AI-generated response draft"""
    complaint_id: str
    response_text: str
    language: str
    tone_score: dict  # empathy, professionalism, compliance
    key_points_addressed: List[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ClassificationResult(BaseModel):
    """Complaint classification result"""
    complaint_id: str
    predicted_category: ComplaintCategory
    confidence: float
    urgency_level: UrgencyLevel
    urgency_indicators: List[str]
    estimated_handling_time: float  # in hours
    recommended_handler: Optional[str] = None
