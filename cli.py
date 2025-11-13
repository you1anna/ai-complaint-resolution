#!/usr/bin/env python3
"""
Main CLI entry point for AI Complaint Resolution System
Provides unified interface to all system functionality
"""
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from datetime import datetime

from src.config import settings
from src.database import Database
from src.workflow import ComplaintWorkflow
from src.metrics import MetricsCollector
from src.validators import validate_api_configuration
from src.utils import setup_logging


class CLI:
    """Main CLI application"""

    def __init__(self):
        self.db = None
        self.workflow = None

        # Setup logging
        setup_logging(settings.log_level)
        self.logger = logging.getLogger(__name__)

    def validate_setup(self) -> bool:
        """Validate system configuration"""
        is_valid, errors = validate_api_configuration()

        if not is_valid:
            print("\n❌ Configuration Error:")
            for error in errors:
                print(f"   - {error}")
            print("\nPlease check your .env file and ensure ANTHROPIC_API_KEY is set correctly.")
            return False

        return True

    def init_components(self):
        """Initialize database and workflow"""
        if not self.db:
            self.db = Database()
        if not self.workflow:
            self.workflow = ComplaintWorkflow()

    def cleanup(self):
        """Cleanup resources"""
        if self.db:
            self.db.close()

    def cmd_init(self, args):
        """Initialize the system and seed data"""
        print("\n" + "=" * 80)
        print("  Initializing AI Complaint Resolution System")
        print("=" * 80)

        if not self.validate_setup():
            return 1

        print("\n✅ Configuration valid")

        # Initialize database
        print("📦 Initializing database...")
        self.init_components()

        # Check if data already exists
        complaints = self.db.get_all_complaints()
        if complaints:
            print(f"\n⚠️  Database already contains {len(complaints)} complaints")
            response = input("Seed additional dummy data? (y/n): ")
            if response.lower() != 'y':
                print("Skipping seed data")
                return 0

        # Import and run seed data
        print("🌱 Seeding dummy data...")
        from scripts.seed_data import seed_database
        seed_database()

        print("\n✅ Initialization complete!")
        print("\nNext steps:")
        print("  - List complaints: python cli.py list")
        print("  - Process complaint: python cli.py process <complaint_id>")
        print("  - View metrics: python cli.py metrics")

        return 0

    def cmd_list(self, args):
        """List complaints"""
        # Only initialize database, not workflow (doesn't need API key)
        if not self.db:
            self.db = Database()

        complaints = self.db.get_all_complaints()

        if not complaints:
            print("\nNo complaints found in database.")
            print("Run 'python cli.py init' to seed data")
            return 0

        # Apply filters
        if args.status:
            from src.models import ComplaintStatus
            status_filter = ComplaintStatus(args.status)
            complaints = [c for c in complaints if c.status == status_filter]

        if args.urgency:
            from src.models import UrgencyLevel
            urgency_filter = UrgencyLevel(args.urgency)
            complaints = [c for c in complaints if c.urgency == urgency_filter]

        print("\n" + "=" * 90)
        print(f"  COMPLAINTS ({len(complaints)} total)")
        print("=" * 90)
        print(f"\n{'ID':<20} {'Customer':<20} {'Lang':<6} {'Status':<15} {'Deadline':<12} {'Urgency'}")
        print("-" * 90)

        for complaint in complaints:
            urgency = complaint.urgency.value if complaint.urgency else 'N/A'
            print(
                f"{complaint.complaint_id:<20} "
                f"{complaint.customer_name:<20} "
                f"{complaint.customer_language:<6} "
                f"{complaint.status.value:<15} "
                f"{complaint.deadline_date.strftime('%Y-%m-%d'):<12} "
                f"{urgency}"
            )

        return 0

    def cmd_process(self, args):
        """Process a complaint"""
        if not self.validate_setup():
            return 1

        self.init_components()

        # Get complaint
        complaint = self.db.get_complaint(args.complaint_id)
        if not complaint:
            print(f"\n❌ Complaint {args.complaint_id} not found")
            return 1

        # Get policy
        policy = self.db.get_policy(complaint.policy_number)
        if not policy:
            print(f"\n❌ Policy {complaint.policy_number} not found")
            return 1

        # Validate
        from src.validators import ComplaintValidator
        is_valid, errors = ComplaintValidator.validate_for_processing(complaint)
        if not is_valid:
            print("\n❌ Complaint validation failed:")
            for error in errors:
                print(f"   - {error}")
            return 1

        print("\n" + "=" * 80)
        print(f"  Processing Complaint: {args.complaint_id}")
        print("=" * 80)
        print(f"\n📋 Customer: {complaint.customer_name}")
        print(f"🌍 Language: {complaint.customer_language}")
        print(f"📄 Policy: {complaint.policy_number}")
        print(f"📅 Deadline: {complaint.deadline_date.strftime('%Y-%m-%d')}")

        print("\n⚙️  Running AI workflow...")
        print("   This may take 30-90 seconds...\n")

        # Process
        try:
            result = self.workflow.process_complaint(complaint, policy)

            # Save results
            self.db.save_complaint(complaint)
            self.db.save_workflow_result(args.complaint_id, result)

            # Display results
            self._display_workflow_results(result)

            # Save to file if requested
            if args.save:
                import json
                output_file = Path(f"complaint_{args.complaint_id}_results.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"\n📁 Results saved to: {output_file}")

            print("\n✅ Processing complete!")

            return 0

        except Exception as e:
            self.logger.error(f"Error processing complaint: {str(e)}", exc_info=True)
            print(f"\n❌ Error: {str(e)}")
            return 1

    def cmd_review(self, args):
        """Review a complaint"""
        self.init_components()

        complaint = self.db.get_complaint(args.complaint_id)
        if not complaint:
            print(f"\n❌ Complaint {args.complaint_id} not found")
            return 1

        # Validate for review
        from src.validators import WorkflowValidator
        is_ready, blockers = WorkflowValidator.validate_for_review(complaint)
        if not is_ready:
            print("\n❌ Complaint not ready for review:")
            for blocker in blockers:
                print(f"   - {blocker}")
            return 1

        # Display for review
        print("\n" + "=" * 80)
        print(f"  COMPLAINT REVIEW: {args.complaint_id}")
        print("=" * 80)
        print(f"\n📋 Customer: {complaint.customer_name}")
        print(f"🌍 Language: {complaint.customer_language}")

        if complaint.draft_response:
            print("\n✉️  AI-Generated Response:")
            print("-" * 80)
            print(complaint.draft_response)
            print("-" * 80)

        # Get decision
        print("\nReview Options:")
        print("  [A] Approve")
        print("  [R] Reject")
        print("  [C] Cancel")

        decision = input("\nYour decision (A/R/C): ").strip().upper()

        if decision == 'A':
            notes = input("Review notes (optional): ").strip()
            self.workflow.approve_response(complaint, args.reviewer, notes or "Approved")
            self.db.save_complaint(complaint)
            print("\n✅ Complaint approved!")

        elif decision == 'R':
            reason = input("Rejection reason (required): ").strip()
            if not reason:
                print("❌ Rejection reason is required")
                return 1
            self.workflow.reject_response(complaint, args.reviewer, reason)
            self.db.save_complaint(complaint)
            print("\n❌ Complaint rejected")

        else:
            print("\n⏸️  Review cancelled")

        return 0

    def cmd_metrics(self, args):
        """Display system metrics"""
        # Only initialize database, not workflow
        if not self.db:
            self.db = Database()

        collector = MetricsCollector(self.db)

        if args.type == 'summary':
            report = collector.generate_summary_report()
            print(report)

        elif args.type == 'processing':
            metrics = collector.get_processing_metrics(args.days)
            self._display_dict(metrics, "PROCESSING METRICS")

        elif args.type == 'savings':
            metrics = collector.get_time_savings_metrics()
            self._display_dict(metrics, "TIME SAVINGS METRICS")

        elif args.type == 'quality':
            metrics = collector.get_quality_metrics()
            self._display_dict(metrics, "QUALITY METRICS")

        elif args.type == 'sla':
            metrics = collector.get_sla_compliance_metrics()
            self._display_dict(metrics, "SLA COMPLIANCE METRICS")

        return 0

    def cmd_validate(self, args):
        """Validate system configuration"""
        print("\n" + "=" * 80)
        print("  System Validation")
        print("=" * 80)

        # API configuration
        print("\n🔑 API Configuration:")
        is_valid, errors = validate_api_configuration()
        if is_valid:
            print("   ✅ All checks passed")
        else:
            print("   ❌ Configuration issues:")
            for error in errors:
                print(f"      - {error}")

        # Database
        print("\n💾 Database:")
        try:
            self.init_components()
            complaints = self.db.get_all_complaints()
            policies = self.db.get_all_policies()
            print(f"   ✅ Connected")
            print(f"   📊 Complaints: {len(complaints)}")
            print(f"   📄 Policies: {len(policies)}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

        # Models
        print("\n🤖 AI Models:")
        print(f"   Model: {settings.claude_model}")
        print(f"   Confidence Threshold: {settings.confidence_threshold}")

        return 0 if is_valid else 1

    def _display_workflow_results(self, result):
        """Display workflow results"""
        print("\n" + "=" * 80)
        print("  WORKFLOW RESULTS")
        print("=" * 80)

        # Classification
        if "classification" in result.get("stages", {}):
            cls = result["stages"]["classification"]["result"]
            print("\n📋 CLASSIFICATION:")
            print(f"   Category: {cls['predicted_category']}")
            print(f"   Confidence: {cls['confidence']:.1%}")
            print(f"   Urgency: {cls['urgency_level']}")

        # Time savings
        if "metrics" in result:
            metrics = result["metrics"]
            print("\n⏱️  TIME SAVINGS:")
            print(f"   Manual: {metrics['estimated_manual_time_hours']:.2f}h")
            print(f"   AI-Assisted: {metrics['estimated_ai_assisted_time_hours']:.2f}h")
            print(f"   Saved: {metrics['time_saved_hours']:.2f}h ({metrics['time_saved_percentage']}%)")

        # Review status
        if result.get("requires_review"):
            print("\n⚠️  HUMAN REVIEW REQUIRED:")
            for reason in result["review_reasons"]:
                print(f"   - {reason}")

    def _display_dict(self, data, title):
        """Display dictionary as formatted output"""
        import json
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
        print(json.dumps(data, indent=2))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AI-Powered Travel Insurance Complaint Resolution System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py init                          # Initialize and seed database
  python cli.py list                          # List all complaints
  python cli.py list --status new             # List new complaints
  python cli.py process COMP-2024-001         # Process a complaint
  python cli.py review COMP-2024-001          # Review a complaint
  python cli.py metrics                       # View summary metrics
  python cli.py validate                      # Validate configuration
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Init command
    subparsers.add_parser('init', help='Initialize system and seed data')

    # List command
    list_parser = subparsers.add_parser('list', help='List complaints')
    list_parser.add_argument('--status', choices=['new', 'analyzing', 'awaiting_review', 'approved', 'rejected', 'completed'])
    list_parser.add_argument('--urgency', choices=['high', 'medium', 'low'])

    # Process command
    process_parser = subparsers.add_parser('process', help='Process a complaint')
    process_parser.add_argument('complaint_id', help='Complaint ID to process')
    process_parser.add_argument('--save', action='store_true', help='Save results to JSON file')

    # Review command
    review_parser = subparsers.add_parser('review', help='Review a complaint')
    review_parser.add_argument('complaint_id', help='Complaint ID to review')
    review_parser.add_argument('--reviewer', default='Reviewer', help='Reviewer name')

    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='View system metrics')
    metrics_parser.add_argument('--type', choices=['summary', 'processing', 'savings', 'quality', 'sla'],
                                default='summary', help='Type of metrics to display')
    metrics_parser.add_argument('--days', type=int, default=30, help='Number of days for processing metrics')

    # Validate command
    subparsers.add_parser('validate', help='Validate system configuration')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Create CLI instance and run command
    cli = CLI()
    try:
        command_method = getattr(cli, f'cmd_{args.command}')
        return command_method(args)
    except Exception as e:
        logging.error(f"Error executing command: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        return 1
    finally:
        cli.cleanup()


if __name__ == "__main__":
    sys.exit(main())
