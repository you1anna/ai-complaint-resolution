"""
Policy Document Analyzer - Uses Claude to analyze multilingual policy documents
Reduces 2.5 hour manual analysis to ~15 minutes
"""
import json
import logging
from typing import Dict, List, Optional
from anthropic import Anthropic

from .models import PolicyDocument, PolicyAnalysisResult, Complaint
from .config import settings

logger = logging.getLogger(__name__)


class PolicyAnalyzer:
    """
    Analyzes insurance policy documents using Claude LLM
    Extracts relevant clauses, determines coverage, and identifies exclusions
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the policy analyzer"""
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set in environment or provided")

        self.client = Anthropic(api_key=self.api_key)
        self.model = settings.claude_model

    def analyze_policy_for_complaint(
        self,
        policy: PolicyDocument,
        complaint: Complaint
    ) -> PolicyAnalysisResult:
        """
        Analyze a policy document in the context of a specific complaint

        Args:
            policy: The policy document to analyze
            complaint: The complaint to analyze against

        Returns:
            PolicyAnalysisResult with coverage decision and reasoning
        """
        logger.info(f"Analyzing policy {policy.policy_id} for complaint {complaint.complaint_id}")

        # Construct the analysis prompt
        prompt = self._build_analysis_prompt(policy, complaint)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.1,  # Low temperature for consistent, factual analysis
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse the response
            result_text = response.content[0].text
            result = self._parse_analysis_response(result_text, policy.policy_id, complaint.complaint_id)

            logger.info(f"Analysis complete: {result.coverage_decision} (confidence: {result.confidence})")
            return result

        except Exception as e:
            logger.error(f"Error analyzing policy: {str(e)}")
            raise

    def _build_analysis_prompt(self, policy: PolicyDocument, complaint: Complaint) -> str:
        """Build the prompt for policy analysis"""
        return f"""You are an expert travel insurance policy analyst. Analyze the following policy document and complaint to determine coverage eligibility.

POLICY DOCUMENT:
Policy ID: {policy.policy_id}
Language: {policy.language}
Version: {policy.version}

{policy.content}

COMPLAINT DETAILS:
Complaint ID: {complaint.complaint_id}
Customer: {complaint.customer_name}
Claim Reference: {complaint.claim_reference or 'N/A'}
Complaint Text:
{complaint.complaint_text}

ANALYSIS REQUIREMENTS:
1. Extract all relevant policy clauses that apply to this complaint
2. Identify any exclusions that may apply
3. Determine coverage decision: "covered", "not_covered", "partial", or "unclear"
4. Provide clear reasoning based on policy terms
5. Assess confidence level (0.0 to 1.0)
6. Flag if human review is needed (complex interpretation, edge cases, unclear terms)

Respond in JSON format:
{{
    "relevant_clauses": ["clause 1", "clause 2", ...],
    "exclusions_applied": ["exclusion 1", "exclusion 2", ...],
    "coverage_decision": "covered|not_covered|partial|unclear",
    "reasoning": "detailed explanation referencing specific policy sections",
    "confidence": 0.0-1.0,
    "requires_human_review": true|false,
    "key_considerations": ["consideration 1", "consideration 2", ...]
}}

Ensure your analysis is thorough, accurate, and references specific policy sections."""

    def _parse_analysis_response(self, response_text: str, policy_id: str, complaint_id: str) -> PolicyAnalysisResult:
        """Parse Claude's response into PolicyAnalysisResult"""
        try:
            # Try to extract JSON from response
            # Claude might wrap JSON in markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            data = json.loads(response_text)

            return PolicyAnalysisResult(
                policy_id=policy_id,
                complaint_id=complaint_id,
                relevant_clauses=data.get("relevant_clauses", []),
                coverage_decision=data.get("coverage_decision", "unclear"),
                reasoning=data.get("reasoning", ""),
                exclusions_applied=data.get("exclusions_applied", []),
                confidence=float(data.get("confidence", 0.0)),
                requires_human_review=data.get("requires_human_review", True)
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse analysis response: {str(e)}")
            # Return a safe default result flagged for review
            return PolicyAnalysisResult(
                policy_id=policy_id,
                complaint_id=complaint_id,
                relevant_clauses=[],
                coverage_decision="unclear",
                reasoning=f"Failed to parse AI response: {response_text[:200]}",
                exclusions_applied=[],
                confidence=0.0,
                requires_human_review=True
            )

    def extract_policy_structure(self, policy_content: str, language: str) -> Dict:
        """
        Extract structured information from a policy document
        Useful for pre-processing policies into searchable format
        """
        prompt = f"""Analyze this travel insurance policy document and extract its structure.

Language: {language}

Policy Content:
{policy_content}

Extract and return in JSON format:
{{
    "coverage_sections": {{"section_name": "summary", ...}},
    "exclusions": ["exclusion 1", "exclusion 2", ...],
    "key_terms": {{"term": "definition", ...}},
    "claim_procedures": "summary of how to make a claim",
    "coverage_limits": {{"coverage_type": "limit_amount", ...}}
}}
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text

            # Extract JSON
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()

            return json.loads(result_text)

        except Exception as e:
            logger.error(f"Error extracting policy structure: {str(e)}")
            return {}
