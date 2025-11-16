# API Documentation

This document describes the Python API for the AI Complaint Resolution System.

---

## Core Modules

### 1. Workflow Orchestration

```python
from src.workflow import ComplaintWorkflow
from src.models import Complaint, PolicyDocument

# Initialize workflow
workflow = ComplaintWorkflow(api_key="your_anthropic_key")

# Process a complaint
result = workflow.process_complaint(
    complaint=complaint,
    policy=policy,
    auto_approve=False  # Require human review
)

# Access results
print(result['stages']['classification'])
print(result['metrics']['time_saved_hours'])
```

### 2. Policy Analysis

```python
from src.policy_analyzer import PolicyAnalyzer

analyzer = PolicyAnalyzer(api_key="your_anthropic_key")

# Analyze policy for specific complaint
analysis = analyzer.analyze_policy_for_complaint(policy, complaint)

print(analysis.coverage_decision)  # "covered", "not_covered", "partial", "unclear"
print(analysis.relevant_clauses)
print(analysis.exclusions_applied)
print(analysis.confidence)
```

### 3. Complaint Classification

```python
from src.complaint_classifier import ComplaintClassifier

classifier = ComplaintClassifier(api_key="your_anthropic_key")

# Classify complaint
classification = classifier.classify_complaint(complaint)

print(classification.predicted_category)  # ComplaintCategory enum
print(classification.urgency_level)  # UrgencyLevel enum
print(classification.confidence)
print(classification.estimated_handling_time)  # hours
```

### 4. Response Generation

```python
from src.response_generator import ResponseGenerator

generator = ResponseGenerator(api_key="your_anthropic_key")

# Generate response
draft = generator.generate_response(
    complaint=complaint,
    policy_analysis=policy_analysis,
    classification=classification
)

print(draft.response_text)  # In customer's language
print(draft.language)
print(draft.tone_score)  # empathy, professionalism, compliance
```

### 5. Database Operations

```python
from src.database import Database
from src.models import ComplaintStatus

# Initialize database
db = Database()

# Save complaint
db.save_complaint(complaint)

# Retrieve complaint
complaint = db.get_complaint("COMP-2024-001")

# Get complaints by status
awaiting_review = db.get_complaints_by_status(ComplaintStatus.AWAITING_REVIEW)

# Save policy
db.save_policy(policy)

# Get policy
policy = db.get_policy("EASY-IT-2024-001")

# Close connection
db.close()
```

### 6. Metrics and Reporting

```python
from src.metrics import MetricsCollector
from src.database import Database

db = Database()
collector = MetricsCollector(db)

# Get processing metrics
metrics = collector.get_processing_metrics(days=30)
print(metrics['processing_rate'])

# Get time savings
savings = collector.get_time_savings_metrics()
print(savings['total_time_saved_hours'])
print(savings['cost_savings']['total_savings_gbp'])

# Generate report
report = collector.generate_summary_report()
print(report)
```

### 7. Validation

```python
from src.validators import (
    ComplaintValidator,
    PolicyValidator,
    WorkflowValidator,
    validate_api_configuration
)

# Validate complaint
is_valid, errors = ComplaintValidator.validate_complaint(complaint)
if not is_valid:
    print("Validation errors:", errors)

# Check SLA compliance
is_compliant, message = ComplaintValidator.validate_sla_compliance(complaint)

# Validate for processing
is_ready, blockers = ComplaintValidator.validate_for_processing(complaint)

# Validate API configuration
is_valid, errors = validate_api_configuration()
```

### 8. Utility Functions

```python
from src.utils import (
    format_datetime,
    calculate_days_until,
    is_deadline_approaching,
    format_duration,
    ProgressTracker
)

# Date utilities
formatted = format_datetime(datetime.utcnow())
days_left = calculate_days_until(complaint.deadline_date)
is_urgent = is_deadline_approaching(complaint.deadline_date)

# Duration formatting
print(format_duration(2.5))  # "2h 30m"

# Progress tracking
tracker = ProgressTracker(total=100, description="Processing")
for i in range(100):
    # do work
    tracker.update()
```

---

## Data Models

### Complaint

```python
from src.models import Complaint, ComplaintStatus

complaint = Complaint(
    complaint_id="COMP-001",
    customer_name="John Doe",
    customer_language="en",
    policy_number="POL-001",
    claim_reference="CLM-001",  # Optional
    complaint_text="Complaint description...",
    received_date=datetime.utcnow(),
    deadline_date=datetime.utcnow() + timedelta(days=15),
    status=ComplaintStatus.NEW
)

# After processing
complaint.predicted_category  # ComplaintCategory
complaint.urgency  # UrgencyLevel
complaint.confidence_score  # float 0.0-1.0
complaint.draft_response  # str
complaint.requires_review  # bool
```

### Policy Document

```python
from src.models import PolicyDocument

policy = PolicyDocument(
    policy_id="POL-001",
    policy_name="Travel Insurance Policy",
    language="en",
    content="Full policy text...",
    version="2024.1",
    effective_date=datetime(2024, 1, 1)
)
```

### Classification Result

```python
from src.models import ClassificationResult

result = ClassificationResult(
    complaint_id="COMP-001",
    predicted_category=ComplaintCategory.CLAIM_REJECTION,
    confidence=0.92,
    urgency_level=UrgencyLevel.HIGH,
    urgency_indicators=["regulatory_deadline_approaching"],
    estimated_handling_time=1.5
)
```

---

## Enums

### ComplaintCategory

```python
from src.models import ComplaintCategory

ComplaintCategory.CLAIM_REJECTION
ComplaintCategory.SERVICE_QUALITY
ComplaintCategory.POLICY_INTERPRETATION
ComplaintCategory.MEDICAL_COVERAGE
ComplaintCategory.TRIP_CANCELLATION
ComplaintCategory.BAGGAGE_LOSS
ComplaintCategory.TRAVEL_DELAY
ComplaintCategory.COMMUNICATION_ISSUE
```

### UrgencyLevel

```python
from src.models import UrgencyLevel

UrgencyLevel.HIGH
UrgencyLevel.MEDIUM
UrgencyLevel.LOW
```

### ComplaintStatus

```python
from src.models import ComplaintStatus

ComplaintStatus.NEW
ComplaintStatus.ANALYZING
ComplaintStatus.AWAITING_REVIEW
ComplaintStatus.APPROVED
ComplaintStatus.REJECTED
ComplaintStatus.COMPLETED
```

---

## Complete Example: Process Complaint End-to-End

```python
from src.workflow import ComplaintWorkflow
from src.database import Database
from src.models import Complaint, PolicyDocument
from datetime import datetime, timedelta

# 1. Initialize
db = Database()
workflow = ComplaintWorkflow()

# 2. Create complaint
complaint = Complaint(
    complaint_id="COMP-2024-999",
    customer_name="Jane Smith",
    customer_language="en",
    policy_number="EASY-UK-2024-001",
    claim_reference="CLM-UK-20241115-999",
    complaint_text="I need to complain about my claim rejection...",
    received_date=datetime.utcnow(),
    deadline_date=datetime.utcnow() + timedelta(days=15),
    status=ComplaintStatus.NEW
)

# 3. Get policy
policy = db.get_policy("EASY-UK-2024-001")

# 4. Process complaint
result = workflow.process_complaint(complaint, policy)

# 5. Save results
db.save_complaint(complaint)
db.save_workflow_result(complaint.complaint_id, result)

# 6. Check if review needed
if result['requires_review']:
    print(f"Human review required: {result['review_reasons']}")

# 7. Approve (if human reviewer decides to approve)
if complaint.requires_review:
    workflow.approve_response(
        complaint=complaint,
        reviewer_name="John Reviewer",
        review_notes="Approved after review"
    )
    db.save_complaint(complaint)

# 8. Cleanup
db.close()

print(f"Complaint processed successfully!")
print(f"Time saved: {result['metrics']['time_saved_hours']:.2f} hours")
```

---

## Error Handling

All modules raise appropriate exceptions:

```python
try:
    result = workflow.process_complaint(complaint, policy)
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Processing error: {e}")
    # Log error, notify admin, etc.
```

---

## Configuration

Access configuration:

```python
from src.config import settings, SUPPORTED_LANGUAGES, SLA_TIMELINES

# Environment settings
print(settings.anthropic_api_key)
print(settings.claude_model)
print(settings.confidence_threshold)

# YAML configuration
print(SUPPORTED_LANGUAGES)  # ['en', 'it', 'de', 'fr', 'es']
print(SLA_TIMELINES)  # {'international': 15, 'uk_domestic': 56}
```

---

## Best Practices

1. **Always close database connections**:
   ```python
   db = Database()
   try:
       # operations
   finally:
       db.close()
   ```

2. **Validate before processing**:
   ```python
   is_valid, errors = ComplaintValidator.validate_for_processing(complaint)
   if not is_valid:
       raise ValueError(f"Validation failed: {errors}")
   ```

3. **Handle AI errors gracefully**:
   ```python
   try:
       result = analyzer.analyze_policy_for_complaint(policy, complaint)
   except Exception as e:
       logger.error(f"AI analysis failed: {e}")
       # Fallback or flag for manual review
   ```

4. **Always require human review for critical cases**:
   ```python
   if classification.urgency_level == UrgencyLevel.HIGH:
       complaint.requires_review = True
   ```

---

## Performance Considerations

- **Batch processing**: Use `workflow.batch_process()` for multiple complaints
- **Database**: Consider PostgreSQL for production (just change DATABASE_URL)
- **Caching**: Policy documents can be cached to reduce API calls
- **Async**: Future version may support async operations for better concurrency

---

## Testing

```python
import pytest
from tests.conftest import sample_complaint, sample_policy

def test_complaint_processing(sample_complaint, sample_policy):
    workflow = ComplaintWorkflow()
    result = workflow.process_complaint(sample_complaint, sample_policy)
    assert result['requires_review'] is not None
    assert 'metrics' in result
```

See `tests/` directory for full test suite.
