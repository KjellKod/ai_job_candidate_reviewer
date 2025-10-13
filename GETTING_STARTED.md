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

## Next Steps (Phase 2)

The foundation is solid! Next we'll implement:

1. **Feedback System** (`feedback_manager.py`)
2. **Human Feedback Collection** (`--provide-feedback`)
3. **AI Learning & Insights** (`--show-insights`, `--re-evaluate`)
4. **Enhanced Prompts** with dynamic insight integration

## Testing the System

Try it out with sample files:
1. Create a simple job description PDF
2. Create a sample resume PDF  
3. Follow the usage steps above
4. Check the generated CSV and HTML reports

The system is designed to be robust - it will provide clear error messages if anything goes wrong and guide you through fixing issues.

**Ready for production testing!** 🚀
