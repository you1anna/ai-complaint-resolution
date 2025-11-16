"""
Response Generator - Generates multilingual, compliant complaint responses
Reduces response drafting time from 45 minutes to ~15 minutes
"""
import json
import logging
from typing import Optional, Dict
from datetime import datetime
from anthropic import Anthropic

from .models import (
    Complaint, PolicyAnalysisResult, ResponseDraft,
    ClassificationResult
)
from .config import settings

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generates professional, empathetic, FCA-compliant complaint responses
    in the customer's preferred language with English translation for review
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the response generator"""
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = settings.claude_model

    def generate_response(
        self,
        complaint: Complaint,
        policy_analysis: Optional[PolicyAnalysisResult] = None,
        classification: Optional[ClassificationResult] = None,
        additional_context: Optional[str] = None
    ) -> ResponseDraft:
        """
        Generate a complaint response

        Args:
            complaint: The complaint to respond to
            policy_analysis: Optional policy analysis results
            classification: Optional classification results
            additional_context: Any additional context for the response

        Returns:
            ResponseDraft with response text and metadata
        """
        logger.info(
            f"Generating response for complaint {complaint.complaint_id} "
            f"in language: {complaint.customer_language}"
        )

        prompt = self._build_response_prompt(
            complaint, policy_analysis, classification, additional_context
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,  # Slightly higher for natural language, but still controlled
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text
            draft = self._parse_response(result_text, complaint)

            logger.info(f"Response generated successfully for {complaint.complaint_id}")
            return draft

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    def _build_response_prompt(
        self,
        complaint: Complaint,
        policy_analysis: Optional[PolicyAnalysisResult],
        classification: Optional[ClassificationResult],
        additional_context: Optional[str]
    ) -> str:
        """Build the prompt for response generation"""

        # Build context section
        context_parts = []

        if policy_analysis:
            context_parts.append(f"""
POLICY ANALYSIS:
Coverage Decision: {policy_analysis.coverage_decision}
Reasoning: {policy_analysis.reasoning}
Relevant Clauses: {', '.join(policy_analysis.relevant_clauses[:3]) if policy_analysis.relevant_clauses else 'None'}
Exclusions Applied: {', '.join(policy_analysis.exclusions_applied) if policy_analysis.exclusions_applied else 'None'}
""")

        if classification:
            context_parts.append(f"""
COMPLAINT CLASSIFICATION:
Category: {classification.predicted_category.value}
Urgency: {classification.urgency_level.value}
""")

        if additional_context:
            context_parts.append(f"""
ADDITIONAL CONTEXT:
{additional_context}
""")

        context = "\n".join(context_parts) if context_parts else "No additional context provided."

        return f"""You are an expert complaint handler at Collinson, a travel insurance provider. Write a professional, empathetic, and FCA-compliant response to the following customer complaint.

COMPLAINT DETAILS:
Complaint ID: {complaint.complaint_id}
Customer Name: {complaint.customer_name}
Customer Language: {complaint.customer_language}
Policy Number: {complaint.policy_number}
{f"Claim Reference: {complaint.claim_reference}" if complaint.claim_reference else ""}

Customer's Complaint:
{complaint.complaint_text}

{context}

RESPONSE REQUIREMENTS:
1. Write in {complaint.customer_language} (the customer's language)
2. Maintain a professional, empathetic, and understanding tone
3. Address all points raised in the complaint
4. Reference specific policy terms where relevant
5. Be clear about the decision and reasoning
6. Follow FCA Consumer Duty principles (act in good faith, avoid foreseeable harm, enable customers to pursue their financial objectives)
7. Provide clear next steps if applicable
8. Include appropriate complaint escalation information (Financial Ombudsman Service)
9. Be concise but thorough (aim for 300-500 words)

TONE GUIDELINES:
- Acknowledge the customer's frustration/concern
- Show empathy and understanding
- Be transparent and clear
- Maintain professionalism
- Avoid defensive language
- Take ownership where appropriate

Respond in JSON format:
{{
    "response_text": "the complete response letter in {complaint.customer_language}",
    "english_translation": "English translation for internal review",
    "key_points_addressed": ["point 1", "point 2", ...],
    "tone_assessment": {{
        "empathy_score": 0.0-1.0,
        "professionalism_score": 0.0-1.0,
        "compliance_score": 0.0-1.0
    }},
    "escalation_path_included": true|false,
    "notes_for_reviewer": "any important considerations for human reviewer"
}}
"""

    def _parse_response(self, response_text: str, complaint: Complaint) -> ResponseDraft:
        """Parse Claude's response into ResponseDraft"""
        try:
            # Extract JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            data = json.loads(response_text)

            # Create ResponseDraft
            draft = ResponseDraft(
                complaint_id=complaint.complaint_id,
                response_text=data.get("response_text", ""),
                language=complaint.customer_language,
                tone_score=data.get("tone_assessment", {}),
                key_points_addressed=data.get("key_points_addressed", []),
                generated_at=datetime.utcnow()
            )

            # Log English translation for review
            if "english_translation" in data:
                logger.info(f"English translation available for review: {complaint.complaint_id}")

            return draft

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse response: {str(e)}")
            # Return a minimal draft flagged for review
            return ResponseDraft(
                complaint_id=complaint.complaint_id,
                response_text=f"[ERROR: Failed to generate response. Raw output: {response_text[:200]}]",
                language=complaint.customer_language,
                tone_score={},
                key_points_addressed=[],
                generated_at=datetime.utcnow()
            )

    def translate_response(self, response_text: str, target_language: str) -> str:
        """
        Translate a response to a different language
        Useful for generating both customer-facing and internal versions
        """
        prompt = f"""Translate the following complaint response to {target_language}.
Maintain the professional, empathetic tone and ensure all technical insurance terms are accurately translated.

Original text:
{response_text}

Provide only the translation, no explanations."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Error translating response: {str(e)}")
            return response_text  # Return original if translation fails
