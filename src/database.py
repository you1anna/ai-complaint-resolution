"""
Database management for complaint resolution system
Simple SQLite-based storage for MVP
"""
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import uuid

from .models import Complaint, PolicyDocument, ComplaintStatus
from .config import settings

logger = logging.getLogger(__name__)


class Database:
    """Simple SQLite database for storing complaints and policies"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection"""
        if db_path is None:
            db_path = str(settings.project_root / "complaint_resolution.db")

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

        logger.info(f"Database initialized at {db_path}")

    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()

        # Complaints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                complaint_id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                customer_language TEXT NOT NULL,
                policy_number TEXT NOT NULL,
                claim_reference TEXT,
                complaint_text TEXT NOT NULL,
                received_date TEXT NOT NULL,
                deadline_date TEXT NOT NULL,
                category TEXT,
                urgency TEXT,
                status TEXT NOT NULL,
                predicted_category TEXT,
                predicted_outcome TEXT,
                confidence_score REAL,
                draft_response TEXT,
                final_response TEXT,
                requires_review INTEGER DEFAULT 1,
                reviewed_by TEXT,
                review_notes TEXT,
                review_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Policies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                policy_id TEXT PRIMARY KEY,
                policy_name TEXT NOT NULL,
                language TEXT NOT NULL,
                content TEXT NOT NULL,
                version TEXT NOT NULL,
                effective_date TEXT NOT NULL,
                coverage_terms TEXT,
                exclusions TEXT,
                key_clauses TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Workflow results table (for analytics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id TEXT NOT NULL,
                workflow_data TEXT NOT NULL,
                time_saved_hours REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (complaint_id) REFERENCES complaints (complaint_id)
            )
        """)

        self.conn.commit()
        logger.info("Database tables created/verified")

    def save_complaint(self, complaint: Complaint) -> None:
        """Save or update a complaint"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO complaints (
                complaint_id, customer_name, customer_language, policy_number,
                claim_reference, complaint_text, received_date, deadline_date,
                category, urgency, status, predicted_category, predicted_outcome,
                confidence_score, draft_response, final_response, requires_review,
                reviewed_by, review_notes, review_date, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint.complaint_id,
            complaint.customer_name,
            complaint.customer_language,
            complaint.policy_number,
            complaint.claim_reference,
            complaint.complaint_text,
            complaint.received_date.isoformat(),
            complaint.deadline_date.isoformat(),
            complaint.category.value if complaint.category else None,
            complaint.urgency.value if complaint.urgency else None,
            complaint.status.value,
            complaint.predicted_category.value if complaint.predicted_category else None,
            complaint.predicted_outcome,
            complaint.confidence_score,
            complaint.draft_response,
            complaint.final_response,
            1 if complaint.requires_review else 0,
            complaint.reviewed_by,
            complaint.review_notes,
            complaint.review_date.isoformat() if complaint.review_date else None,
            datetime.utcnow().isoformat()
        ))

        self.conn.commit()
        logger.debug(f"Complaint {complaint.complaint_id} saved")

    def get_complaint(self, complaint_id: str) -> Optional[Complaint]:
        """Retrieve a complaint by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_complaint(row)

    def get_complaints_by_status(self, status: ComplaintStatus) -> List[Complaint]:
        """Get all complaints with a specific status"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM complaints WHERE status = ?", (status.value,))
        rows = cursor.fetchall()

        return [self._row_to_complaint(row) for row in rows]

    def get_all_complaints(self) -> List[Complaint]:
        """Get all complaints"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM complaints ORDER BY received_date DESC")
        rows = cursor.fetchall()

        return [self._row_to_complaint(row) for row in rows]

    def save_policy(self, policy: PolicyDocument) -> None:
        """Save or update a policy document"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO policies (
                policy_id, policy_name, language, content, version,
                effective_date, coverage_terms, exclusions, key_clauses
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            policy.policy_id,
            policy.policy_name,
            policy.language,
            policy.content,
            policy.version,
            policy.effective_date.isoformat(),
            json.dumps(policy.coverage_terms) if policy.coverage_terms else None,
            json.dumps(policy.exclusions) if policy.exclusions else None,
            json.dumps(policy.key_clauses) if policy.key_clauses else None
        ))

        self.conn.commit()
        logger.debug(f"Policy {policy.policy_id} saved")

    def get_policy(self, policy_id: str) -> Optional[PolicyDocument]:
        """Retrieve a policy by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM policies WHERE policy_id = ?", (policy_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_policy(row)

    def get_all_policies(self) -> List[PolicyDocument]:
        """Get all policies"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM policies")
        rows = cursor.fetchall()

        return [self._row_to_policy(row) for row in rows]

    def save_workflow_result(self, complaint_id: str, workflow_data: dict) -> None:
        """Save workflow execution results"""
        cursor = self.conn.cursor()

        time_saved = workflow_data.get("metrics", {}).get("time_saved_hours", 0)

        cursor.execute("""
            INSERT INTO workflow_results (complaint_id, workflow_data, time_saved_hours)
            VALUES (?, ?, ?)
        """, (complaint_id, json.dumps(workflow_data), time_saved))

        self.conn.commit()

    def _row_to_complaint(self, row: sqlite3.Row) -> Complaint:
        """Convert database row to Complaint object"""
        from .models import ComplaintCategory, UrgencyLevel

        return Complaint(
            complaint_id=row["complaint_id"],
            customer_name=row["customer_name"],
            customer_language=row["customer_language"],
            policy_number=row["policy_number"],
            claim_reference=row["claim_reference"],
            complaint_text=row["complaint_text"],
            received_date=datetime.fromisoformat(row["received_date"]),
            deadline_date=datetime.fromisoformat(row["deadline_date"]),
            category=ComplaintCategory(row["category"]) if row["category"] else None,
            urgency=UrgencyLevel(row["urgency"]) if row["urgency"] else None,
            status=ComplaintStatus(row["status"]),
            predicted_category=ComplaintCategory(row["predicted_category"]) if row["predicted_category"] else None,
            predicted_outcome=row["predicted_outcome"],
            confidence_score=row["confidence_score"],
            draft_response=row["draft_response"],
            final_response=row["final_response"],
            requires_review=bool(row["requires_review"]),
            reviewed_by=row["reviewed_by"],
            review_notes=row["review_notes"],
            review_date=datetime.fromisoformat(row["review_date"]) if row["review_date"] else None
        )

    def _row_to_policy(self, row: sqlite3.Row) -> PolicyDocument:
        """Convert database row to PolicyDocument object"""
        return PolicyDocument(
            policy_id=row["policy_id"],
            policy_name=row["policy_name"],
            language=row["language"],
            content=row["content"],
            version=row["version"],
            effective_date=datetime.fromisoformat(row["effective_date"]),
            coverage_terms=json.loads(row["coverage_terms"]) if row["coverage_terms"] else None,
            exclusions=json.loads(row["exclusions"]) if row["exclusions"] else None,
            key_clauses=json.loads(row["key_clauses"]) if row["key_clauses"] else None
        )

    def import_complaint_from_file(self, file_path: str | Path, **overrides) -> Complaint:
        """
        Import complaint from a document file (PDF, DOCX, TXT).

        Args:
            file_path: Path to document file
            **overrides: Optional fields to override extracted values

        Returns:
            Created Complaint object

        Raises:
            ValueError: If file cannot be parsed or required fields are missing
        """
        from .document_parser import extract_complaint_from_file
        from .models import ComplaintCategory, UrgencyLevel

        # Parse the document
        try:
            extracted_data = extract_complaint_from_file(file_path)
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            raise ValueError(f"Failed to parse file: {e}")

        # Generate complaint ID if not provided
        complaint_id = overrides.get('complaint_id') or extracted_data.get('complaint_id') or f"COMP-{uuid.uuid4().hex[:8].upper()}"

        # Extract or use provided values
        customer_name = overrides.get('customer_name') or extracted_data.get('customer_name') or "Unknown Customer"
        customer_language = overrides.get('customer_language') or extracted_data.get('customer_language') or 'en'
        policy_number = overrides.get('policy_number') or extracted_data.get('policy_number')
        complaint_text = overrides.get('complaint_text') or extracted_data.get('complaint_text')

        # Validate required fields
        if not policy_number:
            raise ValueError("Policy number is required but could not be extracted from the file. Please provide it manually.")
        if not complaint_text:
            raise ValueError("Complaint text could not be extracted from the file.")

        # Parse or generate dates
        if 'received_date' in overrides:
            if isinstance(overrides['received_date'], str):
                received_date = datetime.fromisoformat(overrides['received_date'])
            else:
                received_date = overrides['received_date']
        elif extracted_data.get('date_received'):
            try:
                # Try to parse the extracted date
                date_str = extracted_data['date_received']
                # Handle various date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y']:
                    try:
                        received_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    received_date = datetime.now()
            except Exception:
                received_date = datetime.now()
        else:
            received_date = datetime.now()

        # Calculate deadline (15 days from received date per requirements)
        if 'deadline_date' in overrides:
            if isinstance(overrides['deadline_date'], str):
                deadline_date = datetime.fromisoformat(overrides['deadline_date'])
            else:
                deadline_date = overrides['deadline_date']
        else:
            deadline_date = received_date + timedelta(days=15)

        # Create complaint object
        complaint = Complaint(
            complaint_id=complaint_id,
            customer_name=customer_name,
            customer_language=customer_language,
            policy_number=policy_number,
            claim_reference=overrides.get('claim_reference'),
            complaint_text=complaint_text,
            received_date=received_date,
            deadline_date=deadline_date,
            status=ComplaintStatus.NEW
        )

        # Save to database
        self.save_complaint(complaint)

        logger.info(f"Imported complaint {complaint_id} from file {file_path}")
        return complaint

    def import_policy_from_file(self, file_path: str | Path, **metadata) -> PolicyDocument:
        """
        Import policy document from a file (PDF, DOCX, TXT).

        Args:
            file_path: Path to document file
            **metadata: Required metadata (policy_id, policy_name, language, version, effective_date)

        Returns:
            Created PolicyDocument object

        Raises:
            ValueError: If file cannot be parsed or required metadata is missing
        """
        from .document_parser import parse_document

        # Parse the document
        try:
            parsed_doc = parse_document(file_path)
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            raise ValueError(f"Failed to parse file: {e}")

        # Extract required metadata
        policy_id = metadata.get('policy_id')
        policy_name = metadata.get('policy_name') or parsed_doc.metadata.title or Path(file_path).stem
        language = metadata.get('language', 'en')
        version = metadata.get('version', '1.0')

        if not policy_id:
            raise ValueError("Policy ID is required. Please provide it in metadata.")

        # Parse effective date
        if 'effective_date' in metadata:
            if isinstance(metadata['effective_date'], str):
                effective_date = datetime.fromisoformat(metadata['effective_date'])
            else:
                effective_date = metadata['effective_date']
        else:
            effective_date = datetime.now()

        # Create policy object
        policy = PolicyDocument(
            policy_id=policy_id,
            policy_name=policy_name,
            language=language,
            content=parsed_doc.text,
            version=version,
            effective_date=effective_date,
            coverage_terms=metadata.get('coverage_terms'),
            exclusions=metadata.get('exclusions'),
            key_clauses=metadata.get('key_clauses')
        )

        # Save to database
        self.save_policy(policy)

        logger.info(f"Imported policy {policy_id} from file {file_path}")
        return policy

    def close(self):
        """Close database connection"""
        self.conn.close()
        logger.info("Database connection closed")
