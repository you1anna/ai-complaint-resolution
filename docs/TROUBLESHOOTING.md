# Troubleshooting Guide

Common issues and solutions for the AI Complaint Resolution System.

---

## Table of Contents

- [Setup Issues](#setup-issues)
- [API and Authentication](#api-and-authentication)
- [Processing Errors](#processing-errors)
- [Database Issues](#database-issues)
- [Performance Problems](#performance-problems)
- [Docker Issues](#docker-issues)

---

## Setup Issues

### Issue: `.env` file not found

**Symptoms:**
```
FileNotFoundError: .env file not found
```

**Solution:**
```bash
# Create .env from template
cp .env.example .env

# Edit and add your API key
nano .env  # or use your preferred editor
```

---

### Issue: Dependencies installation fails

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Solution:**
```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# If specific package fails, try installing separately
pip install anthropic --upgrade
```

---

### Issue: Python version mismatch

**Symptoms:**
```
SyntaxError: invalid syntax
```

**Solution:**
```bash
# Check Python version (must be 3.11+)
python --version

# If version is too old, install Python 3.11+
# On Ubuntu/Debian:
sudo apt install python3.11

# Create venv with correct version
python3.11 -m venv venv
source venv/bin/activate
```

---

## API and Authentication

### Issue: API key not set

**Symptoms:**
```
ValueError: ANTHROPIC_API_KEY must be set in environment or provided
```

**Solution:**
```bash
# Check if .env exists and has API key
cat .env | grep ANTHROPIC_API_KEY

# If missing, add it:
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env

# Verify configuration
python cli.py validate
```

---

### Issue: API key invalid format

**Symptoms:**
```
API key doesn't match expected format (sk-ant-...)
```

**Solution:**
- Anthropic API keys must start with `sk-ant-`
- Get a valid key from: https://console.anthropic.com/
- Never commit API keys to git (use .gitignore)

```bash
# Correct format:
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
```

---

### Issue: Rate limit exceeded

**Symptoms:**
```
anthropic.RateLimitError: Rate limit exceeded
```

**Solution:**
```python
# Add retry logic in your code
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        result = workflow.process_complaint(complaint, policy)
        break
    except RateLimitError:
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
```

---

### Issue: API timeout

**Symptoms:**
```
ReadTimeout: Request timed out
```

**Solution:**
- Check your internet connection
- Try again (temporary network issue)
- For large policies, the API may take longer - this is normal

---

## Processing Errors

### Issue: Complaint not found

**Symptoms:**
```
❌ Complaint COMP-2024-001 not found
```

**Solution:**
```bash
# List all complaints to check ID
python cli.py list

# If database is empty, seed it
python cli.py init

# Verify complaint ID format (case-sensitive)
```

---

### Issue: Policy not found for complaint

**Symptoms:**
```
❌ Policy EASY-IT-2024-001 not found
```

**Solution:**
```python
# Check which policies exist
from src.database import Database
db = Database()
policies = db.get_all_policies()
for p in policies:
    print(p.policy_id)

# Add missing policy
from src.models import PolicyDocument
from datetime import datetime

policy = PolicyDocument(
    policy_id="EASY-IT-2024-001",
    policy_name="easyJet IT Policy",
    language="it",
    content="...",  # Policy text
    version="1.0",
    effective_date=datetime.utcnow()
)
db.save_policy(policy)
```

---

### Issue: JSON parsing error from AI response

**Symptoms:**
```
Failed to parse analysis response: Expecting value: line 1...
```

**Solution:**
- This usually means Claude returned a response in an unexpected format
- The system has fallback handling, but if it persists:

```python
# Check logs for the actual response
import logging
logging.basicConfig(level=logging.DEBUG)

# The raw response will be logged
```

- If Claude consistently fails to return valid JSON, check:
  - API key permissions
  - Model version (ensure using Claude 3.5 Sonnet)
  - Prompt formatting

---

### Issue: Validation errors prevent processing

**Symptoms:**
```
❌ Complaint validation failed:
   - Complaint text is too short (minimum 10 characters)
```

**Solution:**
```python
# Fix the validation issue
from src.validators import ComplaintValidator

is_valid, errors = ComplaintValidator.validate_complaint(complaint)
if not is_valid:
    print("Errors to fix:", errors)

# Common fixes:
complaint.complaint_text = "Updated complaint text with sufficient length"
complaint.customer_language = "en"  # Must be supported language
complaint.deadline_date = datetime.utcnow() + timedelta(days=15)
```

---

## Database Issues

### Issue: Database locked

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Close all Python processes using the database
pkill -f python

# Or restart your session

# For production, use PostgreSQL instead of SQLite
# Update .env:
DATABASE_URL=postgresql://user:pass@localhost:5432/complaints
```

---

### Issue: Database corruption

**Symptoms:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solution:**
```bash
# Backup existing database
cp complaint_resolution.db complaint_resolution.db.backup

# Try to recover
sqlite3 complaint_resolution.db ".dump" | sqlite3 recovered.db

# If recovery fails, reinitialize (will lose data)
rm complaint_resolution.db
python cli.py init
```

---

### Issue: Cannot write to database

**Symptoms:**
```
sqlite3.OperationalError: attempt to write a readonly database
```

**Solution:**
```bash
# Check file permissions
ls -l complaint_resolution.db

# Fix permissions
chmod 644 complaint_resolution.db

# Check directory permissions
chmod 755 .
```

---

## Performance Problems

### Issue: Processing is very slow

**Symptoms:**
- Each complaint takes >2 minutes to process

**Solutions:**

1. **Check API latency**:
   ```python
   import time
   start = time.time()
   result = analyzer.analyze_policy_for_complaint(policy, complaint)
   print(f"API call took: {time.time() - start:.2f}s")
   ```

2. **Optimize policy documents**:
   - Very long policies (>100 pages) will be slow
   - Consider pre-processing to extract relevant sections

3. **Batch processing**:
   ```python
   # Instead of processing one by one
   results = workflow.batch_process(complaints, policies)
   ```

4. **Check internet connection**:
   - Slow connection = slow API calls
   - Test with: `ping api.anthropic.com`

---

### Issue: High memory usage

**Symptoms:**
- System becomes slow or crashes with many complaints

**Solutions:**

```python
# Process in batches and clear memory
import gc

for batch in batches_of_complaints:
    results = workflow.batch_process(batch, policies)
    # Save results
    gc.collect()  # Force garbage collection

# Close database connections when done
db.close()
```

---

## Docker Issues

### Issue: Docker build fails

**Symptoms:**
```
ERROR: failed to solve: process "/bin/sh -c pip install..."
```

**Solution:**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild
docker-compose build --no-cache

# Check Dockerfile syntax
docker build -t test .
```

---

### Issue: Container exits immediately

**Symptoms:**
```
docker-compose up -d
# Container shows as "Exited (1)"
```

**Solution:**
```bash
# Check logs
docker-compose logs complaint-resolution

# Run interactively to see error
docker-compose run complaint-resolution /bin/bash

# Common issue: .env not mounted
# Ensure .env exists and is in docker-compose.yml volumes
```

---

### Issue: API key not available in Docker

**Symptoms:**
```
ANTHROPIC_API_KEY not set in environment
```

**Solution:**
```yaml
# In docker-compose.yml, ensure environment variables are set:
environment:
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# Or create .env file and Docker will auto-load it
```

```bash
# Verify environment in container
docker-compose exec complaint-resolution env | grep ANTHROPIC
```

---

## Common Error Messages

### `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Ensure you're running from project root
cd /path/to/ai-complaint-resolution

# Or add to PYTHONPATH
export PYTHONPATH=/path/to/ai-complaint-resolution:$PYTHONPATH
```

---

### `UnicodeDecodeError` when processing complaints

**Solution:**
```python
# Ensure UTF-8 encoding
with open(file, 'r', encoding='utf-8') as f:
    content = f.read()

# When saving to database
complaint.complaint_text = text.encode('utf-8').decode('utf-8')
```

---

### `KeyError` when accessing workflow results

**Solution:**
```python
# Always check if key exists before accessing
if 'metrics' in result:
    print(result['metrics'])

# Or use .get() with default
time_saved = result.get('metrics', {}).get('time_saved_hours', 0)
```

---

## Getting Help

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
LOG_LEVEL=DEBUG python cli.py process COMP-2024-001
```

### Check System Status

```bash
# Validate all components
python cli.py validate

# View metrics
python cli.py metrics
```

### Collect Diagnostic Information

```bash
# Python version
python --version

# Installed packages
pip list

# Configuration
python -c "from src.config import settings; print(settings.dict())"

# Database stats
python -c "from src.database import Database; db = Database(); print(len(db.get_all_complaints()))"
```

---

## Still Having Issues?

1. **Check the logs**: Look for ERROR or WARNING messages
2. **Review configuration**: Run `python cli.py validate`
3. **Simplify**: Try with a minimal example first
4. **Update**: Ensure you have the latest code: `git pull`
5. **Clean start**: `make clean && make init`

---

## Reporting Bugs

When reporting issues, please include:

1. **Error message**: Full traceback
2. **Environment**: Python version, OS, Docker version (if applicable)
3. **Steps to reproduce**: Exact commands run
4. **Configuration**: (sanitized - no API keys!)
5. **Logs**: Relevant log output with DEBUG level

Example:
```
Python: 3.11.5
OS: Ubuntu 22.04
Docker: 24.0.5

Steps:
1. python cli.py init
2. python cli.py process COMP-2024-001

Error:
  File "src/workflow.py", line 123
  ...full traceback...

Logs:
  2024-11-15 14:30:00 - ERROR - ...
```
