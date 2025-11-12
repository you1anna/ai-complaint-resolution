"""
Complaint Classifier - Categorizes and triages complaints
Uses ML classification trained on historical data + Claude for intelligent analysis
"""
import json
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from anthropic import Anthropic

from .models import (
    Complaint, ComplaintCategory, UrgencyLevel,
    ClassificationResult
)
from .config import settings, URGENCY_INDICATORS

logger = logging.getLogger(__name__)


class ComplaintClassifier:
    """
    Classifies complaints into categories and determines urgency
    Combines rule-based urgency detection with AI-powered categorization
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the complaint classifier"""
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = settings.claude_model

    def classify_complaint(self, complaint: Complaint) -> ClassificationResult:
        """
        Classify a complaint and determine its urgency

        Args:
            complaint: The complaint to classify

        Returns:
            ClassificationResult with category, urgency, and handling estimates
        """
        logger.info(f"Classifying complaint {complaint.complaint_id}")

        # Step 1: Determine urgency (rule-based + AI)
        urgency_level, urgency_indicators = self._determine_urgency(complaint)

        # Step 2: Categorize complaint (AI-powered)
        category, confidence = self._categorize_complaint(complaint)

        # Step 3: Estimate handling time based on category and urgency
        estimated_time = self._estimate_handling_time(category, urgency_level)

        result = ClassificationResult(
            complaint_id=complaint.complaint_id,
            predicted_category=category,
            confidence=confidence,
            urgency_level=urgency_level,
            urgency_indicators=urgency_indicators,
            estimated_handling_time=estimated_time,
            recommended_handler=None  # Can be enhanced with workload balancing
        )

        logger.info(
            f"Classification complete: {category.value} "
            f"(urgency: {urgency_level.value}, confidence: {confidence:.2f})"
        )

        return result

    def _determine_urgency(self, complaint: Complaint) -> tuple[UrgencyLevel, List[str]]:
        """
        Determine urgency level based on deadline, keywords, and context
        """
        indicators = []
        urgency_score = 0

        # Check deadline proximity
        if complaint.deadline_date:
            days_until_deadline = (complaint.deadline_date - datetime.utcnow()).days
            if days_until_deadline <= 3:
                indicators.append("regulatory_deadline_approaching")
                urgency_score += 3
            elif days_until_deadline <= 7:
                indicators.append("deadline_within_week")
                urgency_score += 2

        # Check for urgency keywords in complaint text
        text_lower = complaint.complaint_text.lower()

        high_urgency_keywords = [
            "lawyer", "legal action", "ombudsman", "fos", "regulatory",
            "vulnerable", "medical emergency", "urgent", "immediate",
            "press", "media", "social media", "twitter"
        ]

        medium_urgency_keywords = [
            "disappointed", "unacceptable", "escalate", "manager",
            "complaint", "formal complaint", "dissatisfied"
        ]

        for keyword in high_urgency_keywords:
            if keyword in text_lower:
                indicators.append(f"keyword_{keyword.replace(' ', '_')}")
                urgency_score += 2

        for keyword in medium_urgency_keywords:
            if keyword in text_lower:
                indicators.append(f"keyword_{keyword.replace(' ', '_')}")
                urgency_score += 1

        # Determine urgency level
        if urgency_score >= 4:
            urgency_level = UrgencyLevel.HIGH
        elif urgency_score >= 2:
            urgency_level = UrgencyLevel.MEDIUM
        else:
            urgency_level = UrgencyLevel.LOW
            if not indicators:
                indicators.append("standard_complaint")

        return urgency_level, indicators

    def _categorize_complaint(self, complaint: Complaint) -> tuple[ComplaintCategory, float]:
        """
        Categorize complaint using Claude AI
        """
        prompt = f"""You are an expert travel insurance complaint analyst. Categorize the following complaint into ONE of these categories:

CATEGORIES:
- claim_rejection: Customer disputes claim denial
- service_quality: Issues with customer service or handling
- policy_interpretation: Confusion about policy terms/coverage
- medical_coverage: Medical expense claim issues
- trip_cancellation: Trip cancellation claim disputes
- baggage_loss: Lost/damaged baggage claims
- travel_delay: Flight delay or travel interruption claims
- communication_issue: Poor communication from insurer

COMPLAINT:
ID: {complaint.complaint_id}
Customer: {complaint.customer_name}
Policy: {complaint.policy_number}
{f"Claim: {complaint.claim_reference}" if complaint.claim_reference else ""}

Complaint Text:
{complaint.complaint_text}

Respond in JSON format:
{{
    "category": "one_of_the_categories_above",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of why this category was chosen",
    "secondary_categories": ["other_relevant_categories"]
}}
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text

            # Extract JSON
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()

            data = json.loads(result_text)

            category = ComplaintCategory(data["category"])
            confidence = float(data.get("confidence", 0.8))

            return category, confidence

        except Exception as e:
            logger.error(f"Error categorizing complaint: {str(e)}")
            # Fallback to a safe default
            return ComplaintCategory.POLICY_INTERPRETATION, 0.5

    def _estimate_handling_time(self, category: ComplaintCategory, urgency: UrgencyLevel) -> float:
        """
        Estimate handling time based on category and urgency
        Returns estimated hours
        """
        # Base times for each category (with AI automation)
        base_times = {
            ComplaintCategory.CLAIM_REJECTION: 1.2,
            ComplaintCategory.MEDICAL_COVERAGE: 1.5,
            ComplaintCategory.POLICY_INTERPRETATION: 0.8,
            ComplaintCategory.SERVICE_QUALITY: 0.7,
            ComplaintCategory.TRIP_CANCELLATION: 1.0,
            ComplaintCategory.BAGGAGE_LOSS: 0.9,
            ComplaintCategory.TRAVEL_DELAY: 0.9,
            ComplaintCategory.COMMUNICATION_ISSUE: 0.6,
        }

        base_time = base_times.get(category, 1.0)

        # Adjust for urgency (high urgency requires more careful handling)
        urgency_multiplier = {
            UrgencyLevel.HIGH: 1.3,
            UrgencyLevel.MEDIUM: 1.1,
            UrgencyLevel.LOW: 1.0,
        }

        estimated = base_time * urgency_multiplier[urgency]

        return round(estimated, 2)

    def batch_classify(self, complaints: List[Complaint]) -> List[ClassificationResult]:
        """
        Classify multiple complaints
        Useful for processing backlog
        """
        results = []
        for complaint in complaints:
            try:
                result = self.classify_complaint(complaint)
                results.append(result)
            except Exception as e:
                logger.error(f"Error classifying complaint {complaint.complaint_id}: {str(e)}")
                continue

        return results
