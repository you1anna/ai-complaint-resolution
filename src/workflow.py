"""
Complaint Resolution Workflow - Orchestrates the end-to-end complaint handling process
Implements human-in-the-loop workflow: AI analyzes, human approves
"""
import logging
from typing import Optional  # Modern Python 3.9+ uses lowercase built-in types for dict, list, etc.
from datetime import datetime
from enum import Enum

from .models import (
    Complaint, PolicyDocument, ComplaintStatus,
    PolicyAnalysisResult, ClassificationResult, ResponseDraft
)
from .policy_analyzer import PolicyAnalyzer
from .complaint_classifier import ComplaintClassifier
from .response_generator import ResponseGenerator
from .config import settings

logger = logging.getLogger(__name__)


class WorkflowStage(str, Enum):
    """Stages in the complaint resolution workflow"""
    INTAKE = "intake"
    CLASSIFICATION = "classification"
    POLICY_ANALYSIS = "policy_analysis"
    RESPONSE_GENERATION = "response_generation"
    HUMAN_REVIEW = "human_review"
    APPROVAL = "approval"
    COMPLETION = "completion"


class ComplaintWorkflow:
    """
    Orchestrates the end-to-end complaint resolution process
    Ensures proper sequencing, data flow, and human oversight
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the workflow with all necessary components"""
        self.api_key = api_key or settings.anthropic_api_key

        # Initialize all components
        self.classifier = ComplaintClassifier(self.api_key)
        self.policy_analyzer = PolicyAnalyzer(self.api_key)
        self.response_generator = ResponseGenerator(self.api_key)

        logger.info("Complaint workflow initialized")

    def process_complaint(
        self,
        complaint: Complaint,
        policy: PolicyDocument,
        auto_approve: bool = False
    ) -> dict:
        """
        Process a complaint through the complete workflow

        Args:
            complaint: The complaint to process
            policy: The relevant policy document
            auto_approve: If True, skip human review (for testing only)

        Returns:
            Dict with all results and workflow metadata
        """
        logger.info(f"Starting workflow for complaint {complaint.complaint_id}")

        workflow_result = {
            "complaint_id": complaint.complaint_id,
            "started_at": datetime.utcnow().isoformat(),
            "stages": {},
            "requires_review": True,
            "review_reasons": []
        }

        try:
            # Stage 1: Classification
            logger.info(f"Stage 1: Classifying complaint {complaint.complaint_id}")
            complaint.status = ComplaintStatus.ANALYZING
            classification = self.classifier.classify_complaint(complaint)
            workflow_result["stages"]["classification"] = {
                "completed_at": datetime.utcnow().isoformat(),
                "result": classification.model_dump(mode='json')
            }

            # Update complaint with classification
            complaint.predicted_category = classification.predicted_category
            complaint.urgency = classification.urgency_level
            complaint.confidence_score = classification.confidence

            # Stage 2: Policy Analysis
            logger.info(f"Stage 2: Analyzing policy for complaint {complaint.complaint_id}")
            policy_analysis = self.policy_analyzer.analyze_policy_for_complaint(
                policy, complaint
            )
            workflow_result["stages"]["policy_analysis"] = {
                "completed_at": datetime.utcnow().isoformat(),
                "result": policy_analysis.model_dump(mode='json')
            }

            # Stage 3: Response Generation
            logger.info(f"Stage 3: Generating response for complaint {complaint.complaint_id}")
            response_draft = self.response_generator.generate_response(
                complaint=complaint,
                policy_analysis=policy_analysis,
                classification=classification
            )
            workflow_result["stages"]["response_generation"] = {
                "completed_at": datetime.utcnow().isoformat(),
                "result": response_draft.model_dump(mode='json')
            }

            # Update complaint with draft response
            complaint.draft_response = response_draft.response_text

            # Stage 4: Determine if human review is required
            review_required, reasons = self._should_require_review(
                complaint, classification, policy_analysis
            )

            workflow_result["requires_review"] = review_required
            workflow_result["review_reasons"] = reasons

            if review_required:
                complaint.status = ComplaintStatus.AWAITING_REVIEW
                complaint.requires_review = True
                logger.info(
                    f"Complaint {complaint.complaint_id} flagged for human review: {', '.join(reasons)}"
                )
            else:
                if auto_approve:
                    complaint.status = ComplaintStatus.APPROVED
                    logger.info(f"Complaint {complaint.complaint_id} auto-approved")
                else:
                    complaint.status = ComplaintStatus.AWAITING_REVIEW
                    complaint.requires_review = True
                    logger.info(f"Complaint {complaint.complaint_id} awaiting review (standard process)")

            workflow_result["completed_at"] = datetime.utcnow().isoformat()
            workflow_result["final_status"] = complaint.status.value

            # Calculate time saved
            estimated_manual_time = 4.25  # hours (from requirements)
            estimated_ai_time = classification.estimated_handling_time
            time_saved = estimated_manual_time - estimated_ai_time

            workflow_result["metrics"] = {
                "estimated_manual_time_hours": estimated_manual_time,
                "estimated_ai_assisted_time_hours": estimated_ai_time,
                "time_saved_hours": round(time_saved, 2),
                "time_saved_percentage": round((time_saved / estimated_manual_time) * 100, 1)
            }

            logger.info(
                f"Workflow completed for {complaint.complaint_id}. "
                f"Time saved: {time_saved:.2f}h ({workflow_result['metrics']['time_saved_percentage']}%)"
            )

            return workflow_result

        except Exception as e:
            logger.error(f"Error in workflow for complaint {complaint.complaint_id}: {str(e)}")
            complaint.status = ComplaintStatus.AWAITING_REVIEW
            complaint.requires_review = True
            workflow_result["error"] = str(e)
            workflow_result["requires_review"] = True
            workflow_result["review_reasons"] = ["workflow_error"]
            return workflow_result

    def _should_require_review(
        self,
        complaint: Complaint,
        classification: ClassificationResult,
        policy_analysis: PolicyAnalysisResult
    ) -> tuple[bool, list[str]]:
        """
        Determine if a complaint requires human review

        Returns:
            tuple of (requires_review: bool, reasons: list[str])
        """
        reasons = []

        # Always review high urgency complaints
        if classification.urgency_level.value == "high":
            reasons.append("high_urgency")

        # Review if confidence is below threshold
        if classification.confidence < settings.confidence_threshold:
            reasons.append(f"low_classification_confidence_{classification.confidence:.2f}")

        if policy_analysis.confidence < settings.confidence_threshold:
            reasons.append(f"low_policy_analysis_confidence_{policy_analysis.confidence:.2f}")

        # Review if policy analysis explicitly flags it
        if policy_analysis.requires_human_review:
            reasons.append("policy_analysis_flagged")

        # Review if coverage is denied
        if policy_analysis.coverage_decision == "not_covered":
            reasons.append("coverage_denied")

        # Review if coverage is unclear
        if policy_analysis.coverage_decision == "unclear":
            reasons.append("coverage_unclear")

        # Review if certain categories (high risk)
        high_risk_categories = ["claim_rejection", "medical_coverage"]
        if classification.predicted_category.value in high_risk_categories:
            reasons.append(f"high_risk_category_{classification.predicted_category.value}")

        # If human review is enabled in settings, always review
        if settings.enable_human_review and not reasons:
            reasons.append("human_review_enabled")

        requires_review = len(reasons) > 0 or settings.enable_human_review

        return requires_review, reasons

    def approve_response(
        self,
        complaint: Complaint,
        reviewer_name: str,
        review_notes: Optional[str] = None,
        modifications: Optional[str] = None
    ) -> Complaint:
        """
        Human reviewer approves a complaint response

        Args:
            complaint: The complaint to approve
            reviewer_name: Name of the reviewer
            review_notes: Optional notes from the reviewer
            modifications: Optional modifications to the AI-generated response

        Returns:
            Updated complaint object
        """
        logger.info(f"Complaint {complaint.complaint_id} approved by {reviewer_name}")

        complaint.status = ComplaintStatus.APPROVED
        complaint.reviewed_by = reviewer_name
        complaint.review_notes = review_notes
        complaint.review_date = datetime.utcnow()

        if modifications:
            complaint.final_response = modifications
            logger.info(f"Response modified by reviewer for {complaint.complaint_id}")
        else:
            complaint.final_response = complaint.draft_response

        return complaint

    def reject_response(
        self,
        complaint: Complaint,
        reviewer_name: str,
        rejection_reason: str
    ) -> Complaint:
        """
        Human reviewer rejects a complaint response (requires rework)

        Args:
            complaint: The complaint to reject
            reviewer_name: Name of the reviewer
            rejection_reason: Reason for rejection

        Returns:
            Updated complaint object
        """
        logger.info(f"Complaint {complaint.complaint_id} rejected by {reviewer_name}: {rejection_reason}")

        complaint.status = ComplaintStatus.REJECTED
        complaint.reviewed_by = reviewer_name
        complaint.review_notes = f"REJECTED: {rejection_reason}"
        complaint.review_date = datetime.utcnow()

        return complaint

    def batch_process(
        self,
        complaints: list[Complaint],
        policies: dict[str, PolicyDocument]
    ) -> list[dict]:
        """
        Process multiple complaints in batch

        Args:
            complaints: List of complaints to process
            policies: Dict mapping policy_id to PolicyDocument

        Returns:
            List of workflow results
        """
        logger.info(f"Starting batch processing of {len(complaints)} complaints")

        results = []
        for complaint in complaints:
            try:
                # Find the matching policy
                policy = policies.get(complaint.policy_number)
                if not policy:
                    logger.warning(f"No policy found for complaint {complaint.complaint_id}")
                    continue

                result = self.process_complaint(complaint, policy)
                results.append(result)

            except Exception as e:
                logger.error(f"Error processing complaint {complaint.complaint_id}: {str(e)}")
                continue

        logger.info(f"Batch processing completed. Processed {len(results)}/{len(complaints)} complaints")

        return results
