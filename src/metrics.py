"""
Metrics and reporting module for complaint resolution system
Tracks performance, time savings, and quality metrics
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

from .models import Complaint, ComplaintStatus, ComplaintCategory, UrgencyLevel
from .database import Database
from .utils import calculate_percentage, format_duration

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and analyzes system metrics"""

    def __init__(self, db: Database):
        self.db = db

    def get_processing_metrics(self, days: int = 30) -> Dict:
        """
        Get processing metrics for a time period

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary of metrics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        all_complaints = self.db.get_all_complaints()

        # Filter to time period
        complaints = [
            c for c in all_complaints
            if c.received_date >= cutoff_date
        ]

        if not complaints:
            return {
                "period_days": days,
                "total_complaints": 0,
                "message": "No complaints in this time period"
            }

        # Calculate metrics
        total = len(complaints)
        processed = len([c for c in complaints if c.status != ComplaintStatus.NEW])

        by_status = defaultdict(int)
        by_category = defaultdict(int)
        by_urgency = defaultdict(int)

        for complaint in complaints:
            by_status[complaint.status.value] += 1
            if complaint.predicted_category:
                by_category[complaint.predicted_category.value] += 1
            if complaint.urgency:
                by_urgency[complaint.urgency.value] += 1

        return {
            "period_days": days,
            "total_complaints": total,
            "processed_complaints": processed,
            "processing_rate": calculate_percentage(processed, total),
            "status_breakdown": dict(by_status),
            "category_breakdown": dict(by_category),
            "urgency_breakdown": dict(by_urgency),
        }

    def get_time_savings_metrics(self) -> Dict:
        """
        Calculate time savings from AI automation

        Returns:
            Dictionary of time savings metrics
        """
        # Constants from requirements
        MANUAL_TIME_PER_COMPLAINT = 4.25  # hours
        HANDLER_HOURLY_COST = 35  # pounds

        # Get workflow results from database
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_processed,
                AVG(time_saved_hours) as avg_time_saved,
                SUM(time_saved_hours) as total_time_saved
            FROM workflow_results
        """)
        row = cursor.fetchone()

        if not row or row['total_processed'] == 0:
            return {
                "total_processed": 0,
                "message": "No completed workflows to analyze"
            }

        total_processed = row['total_processed']
        avg_time_saved = row['avg_time_saved'] or 0
        total_time_saved = row['total_time_saved'] or 0

        # Calculate costs
        manual_cost = total_processed * MANUAL_TIME_PER_COMPLAINT * HANDLER_HOURLY_COST
        ai_assisted_time = (total_processed * MANUAL_TIME_PER_COMPLAINT) - total_time_saved
        ai_cost = ai_assisted_time * HANDLER_HOURLY_COST
        cost_savings = manual_cost - ai_cost

        return {
            "total_processed": total_processed,
            "avg_time_saved_hours": round(avg_time_saved, 2),
            "total_time_saved_hours": round(total_time_saved, 2),
            "time_saved_percentage": calculate_percentage(
                avg_time_saved, MANUAL_TIME_PER_COMPLAINT
            ),
            "cost_savings": {
                "manual_cost_gbp": round(manual_cost, 2),
                "ai_assisted_cost_gbp": round(ai_cost, 2),
                "total_savings_gbp": round(cost_savings, 2),
                "savings_per_complaint_gbp": round(cost_savings / total_processed, 2) if total_processed > 0 else 0
            },
            "formatted": {
                "avg_time_saved": format_duration(avg_time_saved),
                "total_time_saved": format_duration(total_time_saved)
            }
        }

    def get_quality_metrics(self) -> Dict:
        """
        Calculate quality and accuracy metrics

        Returns:
            Dictionary of quality metrics
        """
        complaints = self.db.get_all_complaints()

        if not complaints:
            return {"message": "No complaints to analyze"}

        # Filter to processed complaints
        processed = [
            c for c in complaints
            if c.predicted_category and c.confidence_score is not None
        ]

        if not processed:
            return {"message": "No processed complaints to analyze"}

        # Calculate confidence statistics
        confidence_scores = [c.confidence_score for c in processed]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        min_confidence = min(confidence_scores)
        max_confidence = max(confidence_scores)

        # High confidence predictions (>= 85%)
        high_confidence = len([s for s in confidence_scores if s >= 0.85])
        high_confidence_rate = calculate_percentage(high_confidence, len(processed))

        # Review requirements
        requiring_review = len([c for c in processed if c.requires_review])
        review_rate = calculate_percentage(requiring_review, len(processed))

        # Approved vs rejected
        approved = len([c for c in processed if c.status == ComplaintStatus.APPROVED])
        rejected = len([c for c in processed if c.status == ComplaintStatus.REJECTED])

        approval_rate = calculate_percentage(approved, approved + rejected) if (approved + rejected) > 0 else 0

        return {
            "total_processed": len(processed),
            "confidence_metrics": {
                "average_confidence": round(avg_confidence, 3),
                "min_confidence": round(min_confidence, 3),
                "max_confidence": round(max_confidence, 3),
                "high_confidence_count": high_confidence,
                "high_confidence_rate": high_confidence_rate
            },
            "review_metrics": {
                "requiring_review": requiring_review,
                "review_rate": review_rate,
                "approved": approved,
                "rejected": rejected,
                "approval_rate": approval_rate
            }
        }

    def get_sla_compliance_metrics(self) -> Dict:
        """
        Calculate SLA compliance metrics

        Returns:
            Dictionary of SLA metrics
        """
        complaints = self.db.get_all_complaints()

        if not complaints:
            return {"message": "No complaints to analyze"}

        # Current status
        total = len(complaints)
        overdue = 0
        urgent = 0  # Within 3 days
        on_track = 0

        for complaint in complaints:
            days_until = (complaint.deadline_date - datetime.utcnow()).days

            if days_until < 0:
                overdue += 1
            elif days_until <= 3:
                urgent += 1
            else:
                on_track += 1

        return {
            "total_complaints": total,
            "overdue": overdue,
            "overdue_rate": calculate_percentage(overdue, total),
            "urgent": urgent,
            "urgent_rate": calculate_percentage(urgent, total),
            "on_track": on_track,
            "on_track_rate": calculate_percentage(on_track, total)
        }

    def generate_summary_report(self) -> str:
        """
        Generate a comprehensive summary report

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("  COMPLAINT RESOLUTION SYSTEM - METRICS REPORT")
        lines.append(f"  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append("=" * 80)

        # Processing metrics
        proc_metrics = self.get_processing_metrics()
        lines.append("\n📊 PROCESSING METRICS (Last 30 days)")
        lines.append("-" * 80)
        lines.append(f"Total Complaints: {proc_metrics.get('total_complaints', 0)}")
        lines.append(f"Processed: {proc_metrics.get('processed_complaints', 0)} "
                    f"({proc_metrics.get('processing_rate', 0)}%)")

        if 'status_breakdown' in proc_metrics:
            lines.append("\nStatus Breakdown:")
            for status, count in proc_metrics['status_breakdown'].items():
                lines.append(f"  - {status}: {count}")

        # Time savings
        time_metrics = self.get_time_savings_metrics()
        if 'total_processed' in time_metrics and time_metrics['total_processed'] > 0:
            lines.append("\n⏱️  TIME SAVINGS")
            lines.append("-" * 80)
            lines.append(f"Complaints Processed: {time_metrics['total_processed']}")
            lines.append(f"Avg Time Saved: {time_metrics['formatted']['avg_time_saved']} "
                        f"({time_metrics['time_saved_percentage']}%)")
            lines.append(f"Total Time Saved: {time_metrics['formatted']['total_time_saved']}")

            if 'cost_savings' in time_metrics:
                lines.append(f"\n💰 Cost Savings:")
                lines.append(f"  Total: £{time_metrics['cost_savings']['total_savings_gbp']:,.2f}")
                lines.append(f"  Per Complaint: £{time_metrics['cost_savings']['savings_per_complaint_gbp']:.2f}")

        # Quality metrics
        quality_metrics = self.get_quality_metrics()
        if 'total_processed' in quality_metrics:
            lines.append("\n✅ QUALITY METRICS")
            lines.append("-" * 80)
            conf = quality_metrics['confidence_metrics']
            lines.append(f"Average Confidence: {conf['average_confidence']:.1%}")
            lines.append(f"High Confidence Rate: {conf['high_confidence_rate']:.1f}%")

            review = quality_metrics['review_metrics']
            lines.append(f"\nHuman Review Rate: {review['review_rate']:.1f}%")
            if review['approved'] + review['rejected'] > 0:
                lines.append(f"Approval Rate: {review['approval_rate']:.1f}%")

        # SLA compliance
        sla_metrics = self.get_sla_compliance_metrics()
        if 'total_complaints' in sla_metrics:
            lines.append("\n📅 SLA COMPLIANCE")
            lines.append("-" * 80)
            lines.append(f"On Track: {sla_metrics['on_track']} ({sla_metrics['on_track_rate']:.1f}%)")
            lines.append(f"Urgent (≤3 days): {sla_metrics['urgent']} ({sla_metrics['urgent_rate']:.1f}%)")
            lines.append(f"Overdue: {sla_metrics['overdue']} ({sla_metrics['overdue_rate']:.1f}%)")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)


class PerformanceTracker:
    """Tracks individual operation performance"""

    def __init__(self):
        self.operations = []

    def track_operation(
        self,
        operation_type: str,
        duration_seconds: float,
        success: bool,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Track an operation

        Args:
            operation_type: Type of operation (e.g., "policy_analysis")
            duration_seconds: Duration in seconds
            success: Whether operation succeeded
            metadata: Optional metadata
        """
        self.operations.append({
            "type": operation_type,
            "duration_seconds": duration_seconds,
            "success": success,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_stats(self, operation_type: Optional[str] = None) -> Dict:
        """
        Get statistics for tracked operations

        Args:
            operation_type: Optional filter by operation type

        Returns:
            Statistics dictionary
        """
        ops = self.operations
        if operation_type:
            ops = [o for o in ops if o['type'] == operation_type]

        if not ops:
            return {"message": "No operations tracked"}

        durations = [o['duration_seconds'] for o in ops]
        successes = [o for o in ops if o['success']]

        return {
            "total_operations": len(ops),
            "successful": len(successes),
            "success_rate": calculate_percentage(len(successes), len(ops)),
            "avg_duration_seconds": round(sum(durations) / len(durations), 2),
            "min_duration_seconds": round(min(durations), 2),
            "max_duration_seconds": round(max(durations), 2)
        }
