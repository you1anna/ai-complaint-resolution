#!/usr/bin/env python3
"""
Demo Script: Complete Import Workflow
Demonstrates the full e2e flow of importing and processing an unstructured complaint
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Database
from src.workflow import ComplaintWorkflow
from src.utils import setup_logging
import logging

setup_logging("INFO")
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def demo_import_workflow():
    """Demonstrate the complete import and processing workflow"""

    print_section("AI COMPLAINT RESOLUTION - IMPORT WORKFLOW DEMO")

    # Initialize components
    print("\n📦 Initializing system...")
    db = Database()
    workflow = ComplaintWorkflow()

    # Step 1: Import complaint from file
    print_section("STEP 1: Import Complaint from File")

    sample_file = Path(__file__).parent.parent / "test_data" / "sample_complaint.txt"

    if not sample_file.exists():
        print(f"\n❌ Sample file not found: {sample_file}")
        print("Please ensure test_data/sample_complaint.txt exists")
        return 1

    print(f"\n📄 Importing from: {sample_file.name}")
    print(f"   File size: {sample_file.stat().st_size:,} bytes")

    try:
        complaint = db.import_complaint_from_file(sample_file)

        print("\n✅ Import successful!")
        print(f"\n📋 Complaint Details:")
        print(f"   ID: {complaint.complaint_id}")
        print(f"   Customer: {complaint.customer_name}")
        print(f"   Policy: {complaint.policy_number}")
        print(f"   Language: {complaint.customer_language}")
        print(f"   Received: {complaint.received_date.strftime('%Y-%m-%d')}")
        print(f"   Deadline: {complaint.deadline_date.strftime('%Y-%m-%d')}")
        print(f"   Status: {complaint.status.value}")

    except ValueError as e:
        print(f"\n❌ Import failed: {e}")
        return 1

    # Step 2: Process with AI
    print_section("STEP 2: AI Processing")

    print("\n🤖 Processing complaint with AI workflow...")
    print("   This will:")
    print("   - Classify the complaint category")
    print("   - Determine urgency level")
    print("   - Analyze relevant policy clauses")
    print("   - Generate a draft response")
    print("\n⏳ Please wait (this may take 30-60 seconds)...\n")

    try:
        result = workflow.process_complaint(complaint)

        print("✅ AI processing complete!")

        # Display classification
        if "classification" in result.get("stages", {}):
            cls = result["stages"]["classification"]["result"]
            print(f"\n📊 CLASSIFICATION:")
            print(f"   Category: {cls['predicted_category']}")
            print(f"   Confidence: {cls['confidence']:.1%}")
            print(f"   Urgency: {cls['urgency_level']}")

        # Display policy analysis
        if "policy_analysis" in result.get("stages", {}):
            policy = result["stages"]["policy_analysis"]["result"]
            print(f"\n📜 POLICY ANALYSIS:")
            print(f"   Coverage Decision: {policy['coverage_decision']}")
            print(f"   Confidence: {policy['confidence_score']:.1%}")
            if policy.get('relevant_clauses'):
                print(f"   Relevant Clauses: {len(policy['relevant_clauses'])} found")

        # Display time savings
        if "metrics" in result:
            metrics = result["metrics"]
            print(f"\n⏱️  TIME SAVINGS:")
            print(f"   Manual Time: {metrics['estimated_manual_time_hours']:.2f}h")
            print(f"   AI-Assisted Time: {metrics['estimated_ai_assisted_time_hours']:.2f}h")
            print(f"   Time Saved: {metrics['time_saved_hours']:.2f}h ({metrics['time_saved_percentage']}%)")

        # Reload complaint to get updated data
        complaint = db.get_complaint(complaint.complaint_id)

    except Exception as e:
        print(f"\n❌ Processing failed: {e}")
        logger.error("Processing error", exc_info=True)
        return 1

    # Step 3: Show draft response
    print_section("STEP 3: Review Draft Response")

    if complaint.draft_response:
        print("\n✉️  AI-Generated Response:")
        print("-" * 80)
        print(complaint.draft_response)
        print("-" * 80)

    # Step 4: Human review decision
    if complaint.requires_review:
        print("\n⚠️  HUMAN REVIEW REQUIRED:")
        review_reasons = []
        if complaint.urgency and complaint.urgency.value == 'high':
            review_reasons.append("High urgency complaint")
        if complaint.confidence_score and complaint.confidence_score < 0.85:
            review_reasons.append(f"Low confidence score ({complaint.confidence_score:.1%})")

        for reason in review_reasons:
            print(f"   - {reason}")

    # Summary
    print_section("DEMO COMPLETE")

    print("\n✅ Successfully demonstrated complete workflow:")
    print("   1. ✓ Imported unstructured complaint from file")
    print("   2. ✓ Extracted metadata automatically")
    print("   3. ✓ Classified and analyzed with AI")
    print("   4. ✓ Generated draft response")
    print("   5. ✓ Flagged for human review")

    print(f"\n💡 Next Steps:")
    print(f"   - Review complaint: python cli.py review {complaint.complaint_id}")
    print(f"   - View all complaints: python cli.py list")
    print(f"   - View metrics: python cli.py metrics")

    print("\n📚 To import your own files:")
    print("   python cli.py import complaint <your-file.pdf>")
    print("   python cli.py import complaint <your-file.docx> --policy-number POL123")

    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(demo_import_workflow())
