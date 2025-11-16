"""
Example script: Process a single complaint through the complete workflow
Demonstrates the end-to-end complaint resolution process
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
import logging
from datetime import datetime

from src.workflow import ComplaintWorkflow
from src.database import Database
from src.models import ComplaintStatus

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_separator(title: str = ""):
    """Print a visual separator"""
    width = 80
    if title:
        padding = (width - len(title) - 2) // 2
        print("\n" + "=" * padding + f" {title} " + "=" * padding)
    else:
        print("\n" + "=" * width)


def print_complaint_details(complaint):
    """Print complaint details in a readable format"""
    print_separator("COMPLAINT DETAILS")
    print(f"ID: {complaint.complaint_id}")
    print(f"Customer: {complaint.customer_name}")
    print(f"Language: {complaint.customer_language}")
    print(f"Policy: {complaint.policy_number}")
    print(f"Claim Reference: {complaint.claim_reference or 'N/A'}")
    print(f"Received: {complaint.received_date.strftime('%Y-%m-%d')}")
    print(f"Deadline: {complaint.deadline_date.strftime('%Y-%m-%d')}")
    print(f"Status: {complaint.status.value}")
    print("\nComplaint Text:")
    print("-" * 80)
    print(complaint.complaint_text.strip())
    print("-" * 80)


def print_workflow_results(result: dict):
    """Print workflow results in a readable format"""
    print_separator("WORKFLOW RESULTS")

    # Classification
    if "classification" in result["stages"]:
        cls = result["stages"]["classification"]["result"]
        print("\n📋 CLASSIFICATION:")
        print(f"   Category: {cls['predicted_category']}")
        print(f"   Confidence: {cls['confidence']:.2%}")
        print(f"   Urgency: {cls['urgency_level']}")
        print(f"   Indicators: {', '.join(cls['urgency_indicators'])}")
        print(f"   Est. Handling Time: {cls['estimated_handling_time']} hours")

    # Policy Analysis
    if "policy_analysis" in result["stages"]:
        pa = result["stages"]["policy_analysis"]["result"]
        print("\n📄 POLICY ANALYSIS:")
        print(f"   Coverage Decision: {pa['coverage_decision'].upper()}")
        print(f"   Confidence: {pa['confidence']:.2%}")
        print(f"   Requires Review: {'Yes' if pa['requires_human_review'] else 'No'}")
        print(f"\n   Reasoning:")
        print(f"   {pa['reasoning'][:300]}...")
        if pa['relevant_clauses']:
            print(f"\n   Relevant Clauses ({len(pa['relevant_clauses'])}):")
            for clause in pa['relevant_clauses'][:2]:
                print(f"   - {clause[:100]}...")

    # Response Generation
    if "response_generation" in result["stages"]:
        resp = result["stages"]["response_generation"]["result"]
        print("\n✉️  GENERATED RESPONSE:")
        print(f"   Language: {resp['language']}")
        print(f"   Tone Scores:")
        for key, value in resp.get('tone_score', {}).items():
            print(f"      {key}: {value:.2%}")
        print(f"\n   Response Preview:")
        print(f"   {resp['response_text'][:400]}...")

    # Metrics
    if "metrics" in result:
        print_separator("TIME SAVINGS")
        metrics = result["metrics"]
        print(f"⏱️  Manual Process Time: {metrics['estimated_manual_time_hours']:.2f} hours")
        print(f"⚡ AI-Assisted Time: {metrics['estimated_ai_assisted_time_hours']:.2f} hours")
        print(f"✅ Time Saved: {metrics['time_saved_hours']:.2f} hours ({metrics['time_saved_percentage']}%)")

    # Review Requirements
    if result.get("requires_review"):
        print_separator("HUMAN REVIEW REQUIRED")
        print(f"⚠️  This complaint requires human review for the following reasons:")
        for reason in result["review_reasons"]:
            print(f"   - {reason}")
    else:
        print_separator("READY FOR APPROVAL")
        print("✅ This complaint passed all automated checks and is ready for quick approval")


def process_complaint(complaint_id: str, auto_approve: bool = False):
    """
    Process a single complaint through the workflow

    Args:
        complaint_id: ID of the complaint to process
        auto_approve: If True, skip human review (for testing only)
    """
    logger.info(f"Processing complaint: {complaint_id}")

    # Initialize database and workflow
    db = Database()
    workflow = ComplaintWorkflow()

    try:
        # Retrieve complaint from database
        complaint = db.get_complaint(complaint_id)
        if not complaint:
            logger.error(f"Complaint {complaint_id} not found in database")
            print(f"\n❌ Error: Complaint {complaint_id} not found")
            print("Run 'python scripts/seed_data.py' to populate the database first")
            return

        # Retrieve associated policy
        policy = db.get_policy(complaint.policy_number)
        if not policy:
            logger.error(f"Policy {complaint.policy_number} not found")
            print(f"\n❌ Error: Policy {complaint.policy_number} not found")
            return

        # Print complaint details
        print_complaint_details(complaint)

        # Process through workflow
        print_separator("PROCESSING")
        print("⚙️  Running AI-powered analysis workflow...")
        print("   This may take 30-60 seconds...\n")

        result = workflow.process_complaint(
            complaint=complaint,
            policy=policy,
            auto_approve=auto_approve
        )

        # Save updated complaint
        db.save_complaint(complaint)

        # Save workflow results
        db.save_workflow_result(complaint_id, result)

        # Print results
        print_workflow_results(result)

        # Save detailed results to file
        output_file = Path(f"complaint_{complaint_id}_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print_separator("COMPLETE")
        print(f"✅ Processing complete!")
        print(f"📁 Detailed results saved to: {output_file}")
        print(f"💾 Complaint status updated in database")

        if result.get("requires_review"):
            print(f"\n👤 Next step: Human review required")
            print(f"   Use 'review_complaint.py {complaint_id}' to approve/reject")
        else:
            print(f"\n✅ Complaint ready for final approval")

    except Exception as e:
        logger.error(f"Error processing complaint: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        print(f"Check logs for details")

    finally:
        db.close()


def list_complaints():
    """List all complaints in the database"""
    db = Database()
    complaints = db.get_all_complaints()
    db.close()

    if not complaints:
        print("No complaints found in database.")
        print("Run 'python scripts/seed_data.py' to populate the database first")
        return

    print_separator("COMPLAINTS IN DATABASE")
    print(f"\nTotal: {len(complaints)} complaints\n")
    print(f"{'ID':<20} {'Customer':<20} {'Language':<8} {'Status':<15} {'Deadline'}")
    print("-" * 90)

    for complaint in complaints:
        print(
            f"{complaint.complaint_id:<20} "
            f"{complaint.customer_name:<20} "
            f"{complaint.customer_language:<8} "
            f"{complaint.status.value:<15} "
            f"{complaint.deadline_date.strftime('%Y-%m-%d')}"
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Process travel insurance complaints using AI"
    )
    parser.add_argument(
        "complaint_id",
        nargs="?",
        help="ID of the complaint to process (e.g., COMP-2024-001)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all complaints in database"
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve without human review (testing only)"
    )

    args = parser.parse_args()

    # Print header
    print("\n" + "=" * 80)
    print("  AI-Powered Travel Insurance Complaint Resolution - MVP Demo")
    print("  Collinson Insurance Automation System")
    print("=" * 80)

    if args.list:
        list_complaints()
    elif args.complaint_id:
        process_complaint(args.complaint_id, args.auto_approve)
    else:
        print("\nUsage:")
        print("  python scripts/process_complaint.py <complaint_id>")
        print("  python scripts/process_complaint.py --list")
        print("\nExamples:")
        print("  python scripts/process_complaint.py COMP-2024-001")
        print("  python scripts/process_complaint.py --list")


if __name__ == "__main__":
    main()
