# Unstructured Data Import - Demo Guide

This guide demonstrates the new capability to import complaints and policies from unstructured document files (PDF, DOCX, TXT).

---

## 🚀 Quick Demo (2 minutes)

### Automated Demo Script

The fastest way to see the complete workflow:

```bash
# Run the automated demo (imports → processes → shows results)
python scripts/demo_import_workflow.py
```

This will:
1. ✅ Import a sample complaint from file
2. ✅ Extract metadata automatically (name, policy #, language)
3. ✅ Process it with AI (classify, analyze, generate response)
4. ✅ Show time savings and draft response

---

## 📋 Manual Demo Steps

### Step 1: Import a Complaint

Three sample complaints are provided for testing different scenarios:

**Scenario A: Medical Trip Cancellation (Italian)**
```bash
python cli.py import complaint test_data/sample_complaint.txt
```

**Scenario B: Baggage Loss (German)**
```bash
python cli.py import complaint test_data/complaint_baggage_loss.txt
```

**Scenario C: Trip Cancellation - Family Emergency (French)**
```bash
python cli.py import complaint test_data/complaint_cancellation.txt
```

**Expected Output:**
```
================================================================================
  Importing COMPLAINT from file
================================================================================

📄 File: sample_complaint.txt
   Size: 2,156 bytes
   Type: .txt

⏳ Parsing document and extracting complaint data...

✅ Complaint imported successfully!

📋 Complaint Details:
   ID: COMP-2024-IT-001
   Customer: Maria Rossi
   Policy: EJ-2024-987654
   Language: it
   Received: 2024-11-15
   Deadline: 2024-11-30

📝 Complaint Text Preview:
   FORMAL COMPLAINT - TRAVEL INSURANCE CLAIM DENIAL...

💡 Next Steps:
   - Process complaint: python cli.py process COMP-2024-IT-001
   - View all complaints: python cli.py list
```

### Step 2: View Imported Complaints

```bash
python cli.py list
```

You should see your imported complaint(s) with status `new`.

### Step 3: Process with AI

```bash
# Use the complaint ID from the import step
python cli.py process COMP-2024-IT-001
```

This will:
- Classify the complaint (category, urgency)
- Analyze policy coverage
- Generate a draft response in the customer's language
- Calculate time savings

**Processing takes ~30-60 seconds** depending on complaint complexity.

### Step 4: Review the AI Analysis

```bash
python cli.py review COMP-2024-IT-001 --reviewer "Your Name"
```

You can:
- **[A]** Approve the AI response
- **[R]** Reject and provide feedback
- **[C]** Cancel to review later

---

## 🔧 Advanced Import Options

### Override Extracted Fields

If automatic extraction misses fields or you want to override:

```bash
# Provide policy number manually
python cli.py import complaint complaint.pdf \
  --policy-number EJ-2024-123456

# Override customer name and language
python cli.py import complaint complaint.docx \
  --customer-name "John Smith" \
  --language en \
  --policy-number POL-789

# Specify complaint ID (otherwise auto-generated)
python cli.py import complaint complaint.txt \
  --complaint-id COMP-CUSTOM-001
```

### Import Policy Documents

```bash
# Import a policy (requires --policy-id)
python cli.py import policy policy.pdf \
  --policy-id POL-EASY-2024 \
  --policy-name "easyJet Travel Insurance Policy" \
  --language en \
  --version "2.1" \
  --effective-date 2024-01-01
```

---

## 📊 What Gets Extracted Automatically?

### From Complaint Files:

| Field | Auto-Detected | Can Override |
|-------|---------------|--------------|
| Complaint ID | ✅ (or auto-generated) | ✅ `--complaint-id` |
| Customer Name | ✅ Pattern matching | ✅ `--customer-name` |
| Policy Number | ✅ Pattern matching | ✅ `--policy-number` |
| Date Received | ✅ Multiple formats | ✅ (via API only) |
| Language | ✅ Auto-detection | ✅ `--language` |
| Complaint Text | ✅ Full text | ❌ |

### Supported Date Formats:
- `2024-11-15` (ISO)
- `15/11/2024` (DD/MM/YYYY)
- `15-11-2024` (DD-MM-YYYY)
- `11/15/2024` (MM/DD/YYYY)

### Language Detection:
Auto-detects: 🇬🇧 English, 🇮🇹 Italian, 🇩🇪 German, 🇫🇷 French, 🇪🇸 Spanish

---

## 💡 Tips for Best Results

### For Complaint Files:

1. **Include policy number in the document** - saves manual entry
2. **Use clear labels** - "Policy Number:", "Customer Name:", etc.
3. **Consistent date format** - ISO format (YYYY-MM-DD) works best
4. **Keep complaint text clear** - avoid excessive formatting

### For Policy Files:

1. **Always provide `--policy-id`** - required for import
2. **Provide metadata** - language, version, effective date
3. **Clean PDF/DOCX files work best** - scanned images not yet supported

---

## 🧪 Testing Different File Formats

### Test with TXT (fastest)
```bash
python cli.py import complaint test_data/sample_complaint.txt
```

### Test with DOCX (requires python-docx)
```bash
# Create a .docx version of a complaint
# Then: python cli.py import complaint complaint.docx
```

### Test with PDF (requires pypdf)
```bash
# Save complaint as PDF
# Then: python cli.py import complaint complaint.pdf
```

---

## ❓ Troubleshooting

### "Policy number is required but could not be extracted"

**Solution:** Provide it manually:
```bash
python cli.py import complaint file.pdf --policy-number EJ-2024-123456
```

### "Failed to parse file: DOCX parsing not available"

**Solution:** Install dependencies:
```bash
pip install python-docx pypdf python-magic
```

### "File not found"

**Solution:** Use absolute path or check file exists:
```bash
python cli.py import complaint /full/path/to/complaint.pdf
```

### Import succeeds but fields are wrong

**Solution:** Override specific fields:
```bash
python cli.py import complaint file.txt \
  --customer-name "Correct Name" \
  --language it
```

---

## 📈 Workflow Comparison

### Before (Manual Entry):
1. Open complaint email/letter
2. Manually type all details into database
3. Copy-paste complaint text
4. Manually set dates, language, etc.
5. **Time: ~10-15 minutes per complaint**

### After (Import):
1. Save complaint as file (PDF/DOCX/TXT)
2. Run: `python cli.py import complaint file.pdf`
3. **Time: ~30 seconds**
4. **Accuracy: Higher (no manual typing errors)**

---

## 🎯 Real-World Usage

### Daily Workflow Example:

```bash
# Morning: Import new complaints received via email
python cli.py import complaint emails/complaint_001.pdf
python cli.py import complaint emails/complaint_002.docx
python cli.py import complaint emails/complaint_003.txt

# View all new complaints
python cli.py list --status new

# Process each one
python cli.py process COMP-XXXXXXXX

# Review and approve
python cli.py review COMP-XXXXXXXX --reviewer "Joelle"

# Check daily metrics
python cli.py metrics
```

### Batch Import (Python API):

```python
from pathlib import Path
from src.database import Database

db = Database()

# Import all PDF complaints in a folder
complaint_folder = Path("incoming_complaints")
for pdf_file in complaint_folder.glob("*.pdf"):
    try:
        complaint = db.import_complaint_from_file(pdf_file)
        print(f"✅ Imported {complaint.complaint_id}")
    except ValueError as e:
        print(f"❌ Failed to import {pdf_file.name}: {e}")
```

---

## 🔄 Next Steps

After running this demo:

1. ✅ Try importing your own complaint files
2. ✅ Process them through the AI workflow
3. ✅ Review the generated responses
4. ✅ Check the time savings metrics

**For full system documentation, see:**
- `README.md` - Complete system overview
- `REQUIREMENTS.md` - Functional requirements (all phases)
- `test_data/README.md` - Import testing guide
