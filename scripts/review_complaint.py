"""
Example script: Human review workflow for complaints
Demonstrates the human-in-the-loop review and approval process
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import logging
from src.workflow import ComplaintWorkflow
from src.database import Database
from src.models import ComplaintStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_separator(title: str = ""):
    """Print a visual separator"""
    width = 80
    if title:
        padding = (width - len(title) - 2) // 2
        print("\n" + "=" * padding + f" {title} " + "=" * padding)
    else:
        print("\n" + "=" * width)


def review_complaint(complaint_id: str, reviewer_name: str):
    """
    Interactive review of a complaint

    Args:
        complaint_id: ID of the complaint to review
        reviewer_name: Name of the reviewer
    """
    db = Database()
    workflow = ComplaintWorkflow()

    try:
        # Retrieve complaint
        complaint = db.get_complaint(complaint_id)
        if not complaint:
            print(f"\n❌ Error: Complaint {complaint_id} not found")
            return

        # Check if complaint is ready for review
        if complaint.status not in [ComplaintStatus.AWAITING_REVIEW]:
            print(f"\n⚠️  Warning: Complaint status is '{complaint.status.value}'")
            print(f"Expected status: 'awaiting_review'")
            print(f"\nProceed anyway? (y/n): ", end="")
            if input().lower() != 'y':
                return

        # Display complaint details
        print_separator("COMPLAINT REVIEW")
        print(f"\n📋 Complaint ID: {complaint.complaint_id}")
        print(f"👤 Customer: {complaint.customer_name}")
        print(f"🌍 Language: {complaint.customer_language}")
        print(f"📄 Policy: {complaint.policy_number}")
        print(f"📅 Deadline: {complaint.deadline_date.strftime('%Y-%m-%d')}")

        print("\n📝 Original Complaint:")
        print("-" * 80)
        print(complaint.complaint_text.strip())
        print("-" * 80)

        # Display AI analysis
        if complaint.predicted_category:
            print(f"\n🤖 AI Classification:")
            print(f"   Category: {complaint.predicted_category.value}")
            print(f"   Urgency: {complaint.urgency.value if complaint.urgency else 'N/A'}")
            print(f"   Confidence: {complaint.confidence_score:.2%}" if complaint.confidence_score else "")

        # Display draft response
        if complaint.draft_response:
            print("\n✉️  AI-Generated Response:")
            print("-" * 80)
            print(complaint.draft_response.strip())
            print("-" * 80)
        else:
            print("\n⚠️  No draft response available")

        # Review decision
        print_separator("REVIEW DECISION")
        print("\nOptions:")
        print("  [A] Approve response as-is")
        print("  [M] Modify response before approving")
        print("  [R] Reject and flag for rework")
        print("  [C] Cancel review")

        decision = input("\nYour decision (A/M/R/C): ").strip().upper()

        if decision == 'A':
            # Approve as-is
            review_notes = input("\nReview notes (optional): ").strip()
            workflow.approve_response(
                complaint=complaint,
                reviewer_name=reviewer_name,
                review_notes=review_notes or "Approved without modifications"
            )
            db.save_complaint(complaint)
            print("\n✅ Complaint approved!")
            print(f"Status: {complaint.status.value}")

        elif decision == 'M':
            # Modify and approve
            print("\nEnter your modifications to the response:")
            print("(Type 'END' on a new line when finished)\n")
            lines = []
            while True:
                line = input()
                if line == 'END':
                    break
                lines.append(line)

            modifications = '\n'.join(lines)
            review_notes = input("\nReview notes (optional): ").strip()

            workflow.approve_response(
                complaint=complaint,
                reviewer_name=reviewer_name,
                review_notes=review_notes or "Approved with modifications",
                modifications=modifications
            )
            db.save_complaint(complaint)
            print("\n✅ Complaint approved with modifications!")
            print(f"Status: {complaint.status.value}")

        elif decision == 'R':
            # Reject
            rejection_reason = input("\nReason for rejection (required): ").strip()
            if not rejection_reason:
                print("❌ Rejection reason is required")
                return

            workflow.reject_response(
                complaint=complaint,
                reviewer_name=reviewer_name,
                rejection_reason=rejection_reason
            )
            db.save_complaint(complaint)
            print("\n❌ Complaint rejected and flagged for rework")
            print(f"Status: {complaint.status.value}")

        elif decision == 'C':
            print("\n⏸️  Review cancelled")
            return

        else:
            print("\n❌ Invalid decision")
            return

        # Summary
        print_separator("REVIEW COMPLETE")
        print(f"Reviewed by: {reviewer_name}")
        print(f"Complaint ID: {complaint_id}")
        print(f"Final Status: {complaint.status.value}")
        if complaint.review_date:
            print(f"Review Date: {complaint.review_date.strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        logger.error(f"Error during review: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")

    finally:
        db.close()


def list_pending_reviews():
    """List all complaints awaiting review"""
    db = Database()
    complaints = db.get_complaints_by_status(ComplaintStatus.AWAITING_REVIEW)
    db.close()

    if not complaints:
        print("\n✅ No complaints pending review")
        return

    print_separator("COMPLAINTS AWAITING REVIEW")
    print(f"\nTotal: {len(complaints)} complaints\n")
    print(f"{'ID':<20} {'Customer':<20} {'Urgency':<10} {'Deadline'}")
    print("-" * 70)

    for complaint in complaints:
        urgency = complaint.urgency.value if complaint.urgency else 'N/A'
        print(
            f"{complaint.complaint_id:<20} "
            f"{complaint.customer_name:<20} "
            f"{urgency:<10} "
            f"{complaint.deadline_date.strftime('%Y-%m-%d')}"
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Review and approve AI-processed complaints"
    )
    parser.add_argument(
        "complaint_id",
        nargs="?",
        help="ID of the complaint to review"
    )
    parser.add_argument(
        "--reviewer",
        default="Reviewer",
        help="Name of the reviewer"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all complaints awaiting review"
    )

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("  Complaint Review System - Human Approval Workflow")
    print("=" * 80)

    if args.list:
        list_pending_reviews()
    elif args.complaint_id:
        review_complaint(args.complaint_id, args.reviewer)
    else:
        print("\nUsage:")
        print("  python scripts/review_complaint.py <complaint_id> [--reviewer <name>]")
        print("  python scripts/review_complaint.py --list")
        print("\nExamples:")
        print("  python scripts/review_complaint.py COMP-2024-001 --reviewer 'John Smith'")
        print("  python scripts/review_complaint.py --list")


if __name__ == "__main__":
    main()
