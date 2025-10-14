# Getting Started with AI Job Candidate Reviewer

## Phase 1 Implementation Complete! 🎉

The core pipeline is now implemented and ready for testing. Here's how to get started:

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

## Basic Usage

### 1. Test API Connection
```bash
# Using main system
python3 candidate_reviewer.py test-connection

# Or test connection independently
python3 open_api_test_connection.py
```

### 2. Setup a Job
Place these files in `data/intake/`:
- `job_description.pdf` (required)
- `ideal_candidate.txt` (optional)
- `warning_flags.txt` (optional)

Then run:
```bash
python candidate_reviewer.py setup-job "software_engineer"
```

### 3. Process Candidates
Place candidate files in `data/intake/`:
- `resume_john_doe.pdf`
- `coverletter_john_doe.pdf` (optional)
- `application_john_doe.txt` (optional)

Then run:
```bash
python candidate_reviewer.py process-candidates "software_engineer"
```

### 4. View Results
```bash
python candidate_reviewer.py show-candidates "software_engineer"
```

### 5. List All Jobs
```bash
python candidate_reviewer.py list-jobs
```

## File Organization

The system automatically organizes files:

```
data/
├── intake/                    # Drop files here
├── jobs/software_engineer/    # Job context files
├── candidates/software_engineer/
│   └── john_doe/             # Individual candidate files & evaluations
└── output/software_engineer/  # CSV reports & HTML summaries
```

## What's Implemented

✅ **Core Pipeline**
- Configuration management with 2MB file limits
- PDF text extraction and file processing
- OpenAI GPT-5 (or GPT-4 equivalent, you can control what models are available for your API key through [OpenAI --> Settings](https://platform.openai.com/settings/organization/general) --> Limits)
- CSV and HTML report generation
- Terminal display with color coding
- Complete CLI interface

✅ **Key Features**
- File size validation (2MB limit)
- Structured data models with JSON serialization
- Error handling and user-friendly messages
- Automatic file organization
- Score-based candidate ranking

✅ **Advanced Features (Fully Implemented)**

1. **Feedback System** (`feedback_manager.py`) ✅
   - Human feedback collection via `provide-feedback` command
   - Interactive prompts for rating and comments
   - Feedback history tracking per candidate

2. **AI Learning & Insights** ✅
   - Automatic insights generation after every 2 feedback records
   - `show-insights` command to view AI learning
   - `re-evaluate` command to apply insights to all candidates
   - Evaluation history tracking in `evaluation_history.json`
   - Score delta display (e.g., "was 60 → now 75 | Δ +15")

3. **Screening Filters** (`policy/filter_enforcer.py`) ✅
   - Define hard rules that AI must enforce
   - Interactive filter creation during feedback
   - Deterministic policy enforcement (two-layer architecture)
   - Filter management via `screening_filters.json`
   - Actions: `set_recommendation`, `cap_recommendation`, `deduct_points`

4. **Smart Duplicate Detection** ✅
   - Identity-based matching (email, phone, LinkedIn, GitHub)
   - Automatic duplicate/fake candidate detection
   - Name collision handling
   - Duplicate warnings in reports

5. **Re-evaluation System** ✅
   - Smart re-evaluation with score deltas
   - Skip rejected candidates by default
   - Process highest-scoring candidates first
   - Clean up stale duplicate warnings
   - Apply both insights and filters

## Quick Feature Tour

### Provide Feedback
```bash
python3 candidate_reviewer.py provide-feedback "job_name" "candidate_name"
```
- Rate candidate (STRONG_YES to STRONG_NO)
- Provide score (0-100)
- Explain what AI got wrong
- Optionally create screening filter (if rejecting)

### View AI Learning
```bash
python3 candidate_reviewer.py show-insights "job_name"
```
Shows patterns the AI learned from your feedback.

### Re-evaluate with Insights
```bash
python3 candidate_reviewer.py re-evaluate "job_name"
```
Applies insights and updated filters to all candidates, showing score changes.

### Create Screening Filters
During feedback, when rejecting a candidate:
```
📝 Would you like to create a screening filter from this rejection? (y/n): y
```
Define rules like "Require 5+ years Python experience" that automatically reject similar candidates.

## Advanced Usage

See these guides for detailed information:
- **[Screening Filters Guide](SCREENING_FILTERS.md)** - Complete guide to automated policy enforcement
- **[README.md](README.md)** - Full user documentation with all features
- **[Architecture Guide](ARCHITECTURE.md)** - Technical architecture and design decisions

## Testing the System

Try it out with sample files:
1. Create a simple job description PDF
2. Create a sample resume PDF  
3. Follow the usage steps above
4. Check the generated CSV and HTML reports

The system is designed to be robust - it will provide clear error messages if anything goes wrong and guide you through fixing issues.

**Ready for production testing!** 🚀
