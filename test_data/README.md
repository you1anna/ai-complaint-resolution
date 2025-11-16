# Test Data for Unstructured Input

This directory contains sample files for testing the document import functionality.

## Sample Files

### `sample_complaint.txt`
A sample complaint letter in text format that can be used to test the complaint import feature.

**Usage:**
```bash
# Import the sample complaint
python cli.py import complaint test_data/sample_complaint.txt

# Or with manual policy number override
python cli.py import complaint test_data/sample_complaint.txt --policy-number EJ-2024-987654
```

## Creating Your Own Test Files

You can create additional test files in the following formats:

### Supported Formats
- **PDF** (`.pdf`) - Policy documents, complaint letters
- **DOCX** (`.docx`) - Microsoft Word documents
- **TXT** (`.txt`) - Plain text files

### Complaint Document Format

For best results, include the following information in your complaint documents:

**Required:**
- Complaint text/description
- Policy number (or provide via `--policy-number` flag)

**Optional (will be auto-detected or can be overridden):**
- Complaint ID
- Customer name
- Date received
- Customer language

**Example:**
```
Customer Name: John Smith
Policy Number: POL-2024-123456
Date Received: 2024-11-15

[Complaint text here...]
```

### Policy Document Format

Policy documents can be in any format (PDF, DOCX, TXT). When importing, you must provide:

**Required:**
- `--policy-id`: Unique identifier for the policy
- File path to the policy document

**Optional:**
- `--policy-name`: Descriptive name
- `--language`: Policy language (en, it, de, fr, es)
- `--version`: Policy version number
- `--effective-date`: When the policy takes effect (YYYY-MM-DD)

**Example:**
```bash
python cli.py import policy policy.pdf \
  --policy-id POL-EASY-2024 \
  --policy-name "easyJet Travel Insurance Policy" \
  --language en \
  --version "2.1" \
  --effective-date 2024-01-01
```

## Testing Import Functionality

### Test 1: Import Sample Complaint
```bash
python cli.py import complaint test_data/sample_complaint.txt
```

Expected output:
- Complaint ID auto-generated or extracted
- Customer name extracted: "Maria Rossi"
- Policy number extracted: "EJ-2024-987654"
- Language detected: "it" (Italian)

### Test 2: Import with Overrides
```bash
python cli.py import complaint test_data/sample_complaint.txt \
  --customer-name "Maria Rossi" \
  --policy-number "EJ-2024-987654" \
  --language it
```

### Test 3: Process Imported Complaint
```bash
# After importing
python cli.py list
python cli.py process <complaint-id-from-import>
```

## Notes

- The document parser uses pattern matching to extract structured data
- If extraction fails for required fields (like policy number), you'll get an error with suggestions
- Language detection is automatic but can be overridden
- Dates are parsed in multiple formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, MM/DD/YYYY
- Generated complaint IDs follow the format: COMP-XXXXXXXX (8 random hex characters)
