# Development Guide

Guide for developers working on the AI Complaint Resolution System.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Testing](#testing)
- [Adding Features](#adding-features)
- [Debugging](#debugging)
- [Release Process](#release-process)

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Docker (optional, for containerized development)
- Anthropic API key

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd ai-complaint-resolution

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black flake8 mypy

# Setup environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Initialize database
python cli.py init
```

---

## Project Structure

```
ai-complaint-resolution/
├── src/                      # Source code
│   ├── __init__.py
│   ├── models.py            # Data models (Pydantic)
│   ├── config.py            # Configuration management
│   ├── database.py          # Database operations
│   ├── utils.py             # Utility functions
│   ├── validators.py        # Validation logic
│   ├── metrics.py           # Metrics and reporting
│   ├── policy_analyzer.py   # AI policy analysis
│   ├── complaint_classifier.py  # AI classification
│   ├── response_generator.py    # AI response generation
│   └── workflow.py          # Orchestration
│
├── scripts/                  # Utility scripts
│   ├── seed_data.py         # Database seeding
│   ├── process_complaint.py # Example processing
│   └── review_complaint.py  # Example review
│
├── tests/                    # Test suite
│   ├── conftest.py          # Test fixtures
│   ├── test_validators.py  # Validator tests
│   └── test_utils.py        # Utility tests
│
├── docs/                     # Documentation
│   ├── API.md               # API documentation
│   ├── TROUBLESHOOTING.md   # Troubleshooting guide
│   └── DEVELOPMENT.md       # This file
│
├── config/                   # Configuration files
│   └── config.yaml          # Application config
│
├── cli.py                    # Main CLI entry point
├── Dockerfile                # Docker image
├── docker-compose.yml        # Docker orchestration
├── Makefile                  # Common tasks
├── requirements.txt          # Dependencies
└── README.md                 # Main documentation
```

### Module Responsibilities

- **models.py**: Define all data structures using Pydantic
- **config.py**: Centralized configuration (env vars + YAML)
- **database.py**: Database operations (currently SQLite)
- **utils.py**: Shared utility functions
- **validators.py**: Input validation and business rules
- **metrics.py**: Performance tracking and reporting
- **policy_analyzer.py**: Claude-powered policy analysis
- **complaint_classifier.py**: Claude-powered classification
- **response_generator.py**: Claude-powered response drafting
- **workflow.py**: Orchestrates the complete workflow

---

## Code Style

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters (not 80)
- **Strings**: Double quotes preferred
- **Imports**: Grouped (stdlib, third-party, local)
- **Type hints**: Required for all public functions

### Example

```python
"""
Module docstring describing the module.
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime

from anthropic import Anthropic  # Third-party

from .models import Complaint, PolicyDocument  # Local
from .config import settings


logger = logging.getLogger(__name__)


class PolicyAnalyzer:
    """
    Class docstring describing the class.

    Attributes:
        api_key: Anthropic API key
        client: Anthropic client instance
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the policy analyzer."""
        self.api_key = api_key or settings.anthropic_api_key
        self.client = Anthropic(api_key=self.api_key)

    def analyze_policy(
        self,
        policy: PolicyDocument,
        complaint: Complaint
    ) -> Dict:
        """
        Analyze a policy document.

        Args:
            policy: Policy to analyze
            complaint: Complaint context

        Returns:
            Analysis results dictionary

        Raises:
            ValueError: If policy or complaint is invalid
        """
        # Implementation
        pass
```

### Running Code Formatters

```bash
# Format code with black
make format

# Run linter
make lint

# Type checking (if mypy is configured)
mypy src/
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_validators.py

# Run specific test
pytest tests/test_validators.py::TestComplaintValidator::test_valid_complaint

# Run with verbose output
pytest -v
```

### Writing Tests

#### Unit Test Example

```python
# tests/test_my_module.py
import pytest
from src.my_module import my_function

def test_my_function_success():
    """Test my_function with valid input."""
    result = my_function("input")
    assert result == "expected"

def test_my_function_invalid_input():
    """Test my_function raises error for invalid input."""
    with pytest.raises(ValueError):
        my_function(None)
```

#### Using Fixtures

```python
def test_with_complaint(sample_complaint):
    """Test using fixture from conftest.py."""
    assert sample_complaint.complaint_id == "TEST-001"
```

#### Integration Test Example

```python
def test_full_workflow(sample_complaint, sample_policy, temp_db):
    """Test complete workflow integration."""
    from src.workflow import ComplaintWorkflow

    workflow = ComplaintWorkflow()
    result = workflow.process_complaint(sample_complaint, sample_policy)

    assert 'stages' in result
    assert result['requires_review'] is not None
```

### Test Coverage Goals

- **Minimum coverage**: 70%
- **Target coverage**: 85%
- **Critical modules**: 90%+ (validators, workflow, database)

---

## Adding Features

### Adding a New Complaint Category

1. **Update enum** (`src/models.py`):
```python
class ComplaintCategory(str, Enum):
    # ... existing categories
    NEW_CATEGORY = "new_category"
```

2. **Update config** (`config/config.yaml`):
```yaml
complaint_categories:
  - new_category
```

3. **Update classifier** (`src/complaint_classifier.py`):
```python
# Add to categorization prompt
CATEGORIES:
- new_category: Description of new category
```

4. **Add tests** (`tests/test_classifier.py`):
```python
def test_classify_new_category(sample_complaint):
    # Test classification of new category
    pass
```

5. **Update documentation** (`README.md`, `docs/API.md`)

---

### Adding a New Language

1. **Update config** (`config/config.yaml`):
```yaml
supported_languages:
  - pt  # Portuguese
```

2. **Add policy document** in the new language

3. **Test**:
```python
def test_portuguese_response():
    complaint.customer_language = "pt"
    draft = generator.generate_response(complaint)
    assert draft.language == "pt"
```

---

### Adding a New Validation Rule

1. **Add to validator** (`src/validators.py`):
```python
def validate_special_rule(complaint: Complaint) -> Tuple[bool, str]:
    """Validate special business rule."""
    if not meets_criteria(complaint):
        return False, "Does not meet special criteria"
    return True, "OK"
```

2. **Integrate into validation chain**:
```python
def validate_complaint(complaint: Complaint) -> Tuple[bool, List[str]]:
    errors = []

    # Existing validations...

    # New validation
    is_valid, message = validate_special_rule(complaint)
    if not is_valid:
        errors.append(message)

    return len(errors) == 0, errors
```

3. **Add tests**:
```python
def test_special_rule_validation():
    # Test the new rule
    pass
```

---

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or via environment:
```bash
LOG_LEVEL=DEBUG python cli.py process COMP-2024-001
```

### Using Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use built-in breakpoint() (Python 3.7+)
breakpoint()
```

### Debugging API Calls

```python
# Log API requests/responses
from src.policy_analyzer import PolicyAnalyzer

analyzer = PolicyAnalyzer()

# Add logging to see request/response
import logging
logging.getLogger('anthropic').setLevel(logging.DEBUG)
```

### Common Debugging Techniques

1. **Print intermediate values**:
```python
print(f"DEBUG: complaint_id={complaint.complaint_id}")
print(f"DEBUG: policy content length={len(policy.content)}")
```

2. **Check data at each stage**:
```python
result = workflow.process_complaint(complaint, policy)
print(f"Classification: {result['stages']['classification']}")
print(f"Policy Analysis: {result['stages']['policy_analysis']}")
```

3. **Validate assumptions**:
```python
assert complaint.complaint_id is not None, "Complaint ID should not be None"
```

---

## Database Migrations

Currently using SQLite with simple schema. For changes:

1. **Backup existing data**:
```bash
cp complaint_resolution.db complaint_resolution.db.backup
```

2. **Update schema** in `src/database.py`:
```python
cursor.execute("""
    ALTER TABLE complaints
    ADD COLUMN new_field TEXT
""")
```

3. **Test migration** on copy of production data

4. **For PostgreSQL** (recommended for production), use Alembic:
```bash
pip install alembic
alembic init migrations
# Configure and create migrations
```

---

## Performance Optimization

### Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
workflow.process_complaint(complaint, policy)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### Caching Policy Documents

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_policy_cached(policy_id: str) -> PolicyDocument:
    return db.get_policy(policy_id)
```

### Batch Processing

```python
# Process multiple complaints efficiently
complaints = db.get_complaints_by_status(ComplaintStatus.NEW)
policies = {p.policy_id: p for p in db.get_all_policies()}

results = workflow.batch_process(complaints, policies)
```

---

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

1. **Update version** in `src/__init__.py`:
```python
__version__ = "0.2.0"
```

2. **Run full test suite**:
```bash
pytest
```

3. **Update documentation**:
- README.md
- CHANGELOG.md
- API.md

4. **Create git tag**:
```bash
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

5. **Build and test Docker image**:
```bash
docker-compose build
docker-compose up -d
# Test the image
docker-compose down
```

6. **Deploy** to production environment

---

## Git Workflow

### Branch Naming

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-fix` - Urgent production fixes

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Portuguese language support
fix: handle missing policy gracefully
docs: update API documentation
test: add tests for new validator
refactor: improve error handling in workflow
```

### Pull Request Process

1. Create feature branch
2. Make changes
3. Add tests
4. Update documentation
5. Create PR with description
6. Pass CI/CD checks
7. Code review
8. Merge to develop

---

## CI/CD (Future)

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=src
```

---

## Resources

- [Anthropic Claude Documentation](https://docs.anthropic.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)

---

## Getting Help

- Check existing issues in repository
- Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Ask in team chat
- Create detailed issue with reproduction steps
