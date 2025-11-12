# AI-Powered Travel Insurance Complaint Resolution System

**MVP End-to-End Implementation for Collinson Insurance**

This project demonstrates an AI-powered system for automating travel insurance complaint handling, reducing processing time from 4.25 hours to approximately 1 hour (75% reduction) while maintaining human oversight.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Development](#development)
- [Business Impact](#business-impact)

---

## 🎯 Overview

This MVP addresses the core challenges faced by Collinson's Customer Relations team:

- **Problem**: Manual complaint processing requires 4.25 hours per case, 60% spent on data gathering and policy analysis
- **Solution**: AI-powered workflow that automates analysis, categorization, and response generation
- **Result**: 75% time reduction, improved consistency, and maintained human oversight

### Key Deliverables

1. **Policy Analysis** - Claude AI analyzes multilingual policy documents and extracts relevant clauses (2.5h → 15min)
2. **Complaint Categorization** - Intelligent classification and urgency triage
3. **Response Generation** - Multilingual, FCA-compliant response drafting (45min → 15min)
4. **Human-in-the-Loop** - AI proposes, human approves workflow

---

## ✨ Features

### Core Capabilities

- **🤖 AI-Powered Policy Analysis**
  - Parses 50+ page multilingual policy documents
  - Extracts relevant terms, exclusions, and coverage decisions
  - Supports English, Italian, German, French, Spanish

- **📊 Intelligent Triage**
  - Automatic complaint categorization (8 categories)
  - Urgency detection (high/medium/low)
  - Deadline tracking and escalation warnings

- **✍️ Multilingual Response Generation**
  - Generates professional, empathetic responses in customer's language
  - FCA-compliant tone and language
  - Includes English translation for internal review

- **👤 Human Review Workflow**
  - AI handles analysis, human makes final decision
  - Configurable confidence thresholds
  - Approval/modification/rejection workflow

- **💾 Data Management**
  - SQLite database for complaints and policies
  - Complete audit trail
  - Workflow metrics and time savings tracking

---

## 🏗️ Architecture

```
┌─────────────┐
│  Complaint  │
│   Intake    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   ComplaintWorkflow (Orchestrator)      │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  1. ComplaintClassifier          │  │
│  │     - Categorize complaint       │  │
│  │     - Determine urgency          │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  2. PolicyAnalyzer               │  │
│  │     - Parse policy document      │  │
│  │     - Extract relevant clauses   │  │
│  │     - Determine coverage         │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  3. ResponseGenerator            │  │
│  │     - Draft response             │  │
│  │     - Multilingual support       │  │
│  │     - FCA compliance             │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Human     │
│   Review    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Approved   │
│  Response   │
└─────────────┘
```

### Technology Stack

- **Language**: Python 3.11+
- **LLM**: Anthropic Claude 3.5 Sonnet
- **Database**: SQLite (easily upgradeable to PostgreSQL)
- **ML**: scikit-learn for classification
- **Containerization**: Docker + Docker Compose

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional but recommended)
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Installation

#### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd ai-complaint-resolution

# 2. Create .env file
cp .env.example .env

# 3. Edit .env and add your API key
# ANTHROPIC_API_KEY=your_api_key_here

# 4. Build and run
docker-compose up -d

# 5. Access the container
docker-compose exec complaint-resolution /bin/bash

# 6. Inside container, seed the database
python scripts/seed_data.py

# 7. Process a complaint
python scripts/process_complaint.py COMP-2024-001
```

#### Option 2: Local Python Environment

```bash
# 1. Clone the repository
git clone <repository-url>
cd ai-complaint-resolution

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env

# 5. Edit .env and add your API key
# ANTHROPIC_API_KEY=your_api_key_here

# 6. Seed the database with dummy data
python scripts/seed_data.py

# 7. Process a complaint
python scripts/process_complaint.py COMP-2024-001
```

---

## 📖 Usage Examples

### 1. List All Complaints

```bash
python scripts/process_complaint.py --list
```

**Output:**
```
COMPLAINTS IN DATABASE

Total: 5 complaints

ID                   Customer             Language Status          Deadline
------------------------------------------------------------------------------------------
COMP-2024-001        Marco Rossi          it       new             2024-11-22
COMP-2024-002        Sarah Williams       en       new             2024-11-24
...
```

### 2. Process a Single Complaint

```bash
python scripts/process_complaint.py COMP-2024-001
```

**What happens:**
1. Loads complaint and policy from database
2. Classifies complaint (category, urgency)
3. Analyzes policy document for coverage
4. Generates multilingual response
5. Flags for human review if needed
6. Saves results to database and JSON file

**Output includes:**
- Classification results
- Policy analysis with coverage decision
- AI-generated response
- Time savings metrics
- Review requirements

### 3. Review and Approve

```bash
# List complaints awaiting review
python scripts/review_complaint.py --list

# Review a specific complaint
python scripts/review_complaint.py COMP-2024-001 --reviewer "John Smith"
```

**Interactive options:**
- **[A]** Approve as-is
- **[M]** Modify before approving
- **[R]** Reject for rework
- **[C]** Cancel review

### 4. Batch Processing (Python API)

```python
from src.workflow import ComplaintWorkflow
from src.database import Database

# Initialize
db = Database()
workflow = ComplaintWorkflow()

# Get all new complaints
complaints = db.get_complaints_by_status("new")
policies = {p.policy_id: p for p in db.get_all_policies()}

# Process batch
results = workflow.batch_process(complaints, policies)

# Review results
for result in results:
    print(f"Processed: {result['complaint_id']}")
    print(f"Time saved: {result['metrics']['time_saved_hours']:.2f}h")
```

---

## 📁 Project Structure

```
ai-complaint-resolution/
├── src/                          # Core modules
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── models.py                 # Data models (Pydantic)
│   ├── database.py               # SQLite database operations
│   ├── policy_analyzer.py        # AI policy analysis
│   ├── complaint_classifier.py   # Complaint categorization
│   ├── response_generator.py     # Response drafting
│   └── workflow.py               # E2E orchestration
│
├── scripts/                      # Example scripts
│   ├── seed_data.py              # Populate database with dummy data
│   ├── process_complaint.py      # Main processing script
│   └── review_complaint.py       # Human review workflow
│
├── config/                       # Configuration files
│   └── config.yaml               # Application settings
│
├── data/                         # Data directory (created at runtime)
│   └── complaint_resolution.db   # SQLite database
│
├── tests/                        # Unit tests (future)
│
├── .env.example                  # Environment template
├── .gitignore
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker image
├── docker-compose.yml            # Docker orchestration
└── README.md                     # This file
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Optional (with defaults)
CLAUDE_MODEL=claude-3-5-sonnet-20241022
DATABASE_URL=sqlite:///./complaint_resolution.db
LOG_LEVEL=INFO
ENABLE_HUMAN_REVIEW=true
CONFIDENCE_THRESHOLD=0.85
```

### Application Settings (config/config.yaml)

- **Supported languages**: en, it, de, fr, es
- **Complaint categories**: 8 predefined categories
- **Urgency indicators**: High/medium/low criteria
- **SLA timelines**: International (15 days), UK (56 days)
- **Human review rules**: Confidence thresholds, category rules

---

## 🔧 Development

### Adding New Language Support

1. Update `config/config.yaml`:
```yaml
supported_languages:
  - en
  - it
  - pt  # Add Portuguese
```

2. Add policy documents in the new language

3. Test with complaints in that language

### Adding New Complaint Categories

1. Update `src/models.py`:
```python
class ComplaintCategory(str, Enum):
    # ... existing categories
    NEW_CATEGORY = "new_category"
```

2. Update `config/config.yaml`:
```yaml
complaint_categories:
  - new_category
```

3. Update classification prompts in `complaint_classifier.py`

### Switching to PostgreSQL

1. Update `requirements.txt`:
```
psycopg2-binary>=2.9.0
```

2. Update `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/complaints
```

3. Database operations remain unchanged (SQLAlchemy abstraction)

---

## 💼 Business Impact

### Metrics (Based on Requirements)

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Avg. Handling Time** | 4.25 hours | ~1 hour | 75% reduction |
| **Policy Analysis Time** | 2.5 hours | 15 min | 90% reduction |
| **Response Drafting** | 45 min | 15 min | 67% reduction |
| **Error Rate** | 11.7% | <5% (target) | 57% reduction |
| **Monthly Capacity** | 10 complaints/handler | 30-40 complaints/handler | 3-4x increase |

### Cost Savings

- **Monthly handler cost**: £29,750 → £11,175 (62% reduction)
- **Annual savings**: £216K - £252K
- **Payback period**: 4-10 months
- **ROI**: 200-300% in first year

### Operational Benefits

✅ **Regulatory Compliance**: Consistent 15-day SLA adherence
✅ **Quality**: Standardized, FCA-compliant responses
✅ **Scalability**: Handle volume increases without headcount
✅ **Team Wellbeing**: Reduce burnout, focus on complex cases
✅ **Audit Trail**: Complete documentation of all decisions

---

## 🛡️ Risk Mitigation

### Human Oversight

- **Always review high-urgency cases**
- **Configurable confidence thresholds**
- **Full audit trail of AI decisions**
- **Easy modification of AI responses**

### Data Privacy

- Local SQLite database (no cloud storage)
- No PII sent to external APIs (only complaint text for analysis)
- Docker isolation for deployment

### Accuracy Safeguards

- Confidence scoring on all predictions
- Flag unclear cases for human review
- Multiple validation steps

---

## 📚 Next Steps

### Immediate (MVP → Production)

1. **Data Audit**: Review historical complaints for quality
2. **Integration**: Connect to iCaseWork, GoTrex, Hepstar APIs
3. **Training**: Handler training on review workflow
4. **Pilot**: Test with 1-2 handlers for 2 weeks

### Short-term (Months 1-3)

1. **Analytics Dashboard**: Track metrics, time savings, quality
2. **ML Model Training**: Train custom classifier on Collinson data
3. **API Development**: REST API for system integration
4. **Enhanced Monitoring**: Alerting, performance tracking

### Long-term (Months 3-12)

1. **Pattern Detection**: Identify systemic issues
2. **Predictive Analytics**: Forecast complaint volumes, outcomes
3. **Continuous Learning**: Feedback loops to improve accuracy
4. **Multi-system Integration**: Full automation with legacy systems

---

## 🤝 Support

For questions or issues:

1. Check the [Usage Examples](#usage-examples) section
2. Review the code comments in `src/` modules
3. Check logs in the console output
4. Contact the development team

---

## 📄 License

Internal use only - Collinson Insurance / AIBV Project

---

## 🎓 Project Context

This MVP was developed as part of the **AIBV Project 1: AI-Powered Travel Insurance Complaint Resolution** for Collinson Insurance.

**Objective**: Demonstrate feasibility and value of AI-powered complaint automation while maintaining essential human judgment and regulatory compliance.

**Approach**: Human-AI collaboration where AI handles analytical tasks (policy analysis, categorization, drafting) and humans provide final approval, relationship management, and edge case handling.

---

**Built with Claude 3.5 Sonnet** | **Python 3.11+** | **Docker Ready**
