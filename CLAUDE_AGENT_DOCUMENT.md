# Claude Agent Document: AI Job Candidate Reviewer

## Project Overview

The AI Job Candidate Reviewer is a pipeline-based system that automates first-pass resume screening while maintaining human oversight. The system processes job descriptions and candidate materials (resumes, cover letters, applications) to generate structured evaluations and rankings.

## Core Architecture Principles

### Design Patterns
- **Single Responsibility Principle (SRP)**: Each component handles one specific aspect of the pipeline
- **DRY (Don't Repeat Yourself)**: Common functionality is abstracted into reusable modules
- **Test Driven Development (TDD)**: Core functionality is test-driven with minimal mocking
- **Pipeline Architecture**: Clear data flow from intake → processing → output

### Testing Philosophy
- **Minimal Mocking**: Use real file operations with temporary directories
- **Integration-Focused**: Test actual API calls with test keys when possible
- **Clear Test Structure**: Arrange-Act-Assert pattern with descriptive names
- **Fast Feedback**: Unit tests run quickly, integration tests are separate

## System Components

### 1. Core Pipeline (`candidate_reviewer.py`)
**Responsibility**: Main CLI interface and command orchestration

**Key Functions**:
- `--setup-job "job_name"`: Initialize job with description files
- `--process-candidates "job_name"`: Process candidate files  
- `--show-candidates "job_name"`: Display ranked results
- `--list-jobs`: Show available jobs
- `--test-connection`: Verify OpenAI API connectivity

**Architecture**:
```python
class CandidateReviewer:
    def __init__(self, config: Config, api_client: APIClient)
    def setup_job(self, job_name: str) -> JobSetupResult
    def process_candidates(self, job_name: str) -> ProcessingResult
    def show_candidates(self, job_name: str) -> DisplayResult
    def list_jobs() -> List[str]
```

### 2. API Client (`open_api_test_connection.py`)
**Responsibility**: OpenAI API interaction and connection testing

**Key Functions**:
- Test API connectivity with minimal request
- Handle API authentication and rate limiting
- Provide clean interface for AI evaluation calls

**Architecture**:
```python
class OpenAIClient:
    def __init__(self, api_key: str)
    def test_connection() -> ConnectionResult
    def evaluate_candidate(self, job_context: JobContext, candidate: Candidate) -> Evaluation
    def _make_request(self, messages: List[Dict]) -> APIResponse
```

### 3. File Processing (`file_processor.py`)
**Responsibility**: Handle intake, organization, and file operations

**Key Functions**:
- Process intake files with standard naming patterns
- Extract text from PDFs and documents  
- Organize files into structured directories
- Validate file formats and naming conventions

**Architecture**:
```python
class FileProcessor:
    def __init__(self, base_path: str)
    def process_job_intake(self, job_name: str) -> JobFiles
    def process_candidate_intake(self, job_name: str) -> List[CandidateFiles]
    def extract_text_from_pdf(self, file_path: str) -> str
    def organize_files(self, source: str, destination: str) -> None
```

### 4. Data Models (`models.py`)
**Responsibility**: Type-safe data structures and validation

**Key Classes**:
```python
@dataclass
class JobContext:
    name: str
    description: str
    ideal_candidate: Optional[str] = None
    warning_flags: Optional[str] = None

@dataclass  
class Candidate:
    name: str
    resume_text: str
    cover_letter: Optional[str] = None
    application: Optional[str] = None

@dataclass
class Evaluation:
    overall_score: int  # 0-100
    recommendation: str  # STRONG_YES, YES, MAYBE, NO, STRONG_NO  
    strengths: List[str]
    concerns: List[str]
    interview_priority: str  # HIGH, MEDIUM, LOW
    detailed_notes: str
```

### 5. Output Generation (`output_generator.py`)  
**Responsibility**: Generate CSV reports and terminal displays

**Key Functions**:
- Create structured CSV files for Excel/Sheets
- Generate terminal-friendly candidate rankings
- Produce detailed HTML reports
- Handle result sorting and formatting

**Architecture**:
```python
class OutputGenerator:
    def generate_csv(self, evaluations: List[Evaluation], output_path: str) -> None
    def display_terminal_ranking(self, evaluations: List[Evaluation]) -> None  
    def generate_html_report(self, job: JobContext, evaluations: List[Evaluation]) -> str
```

### 6. Configuration (`config.py`)
**Responsibility**: Environment and settings management  

**Key Functions**:
- Load environment variables (.env file)
- Validate required configurations
- Provide default settings and paths

**Architecture**:
```python
class Config:
    def __init__(self)
    def load_env(self) -> None
    def validate_required_settings(self) -> ValidationResult
    
    # Properties
    openai_api_key: str
    base_data_path: str  
    intake_path: str
    jobs_path: str
    candidates_path: str
    output_path: str
```

## File Organization Strategy

### Intake Structure (User Drops Files Here)
```
data/intake/
├── job_description.pdf          # For --setup-job
├── ideal_candidate.txt          # Optional for --setup-job  
├── warning_flags.txt           # Optional for --setup-job
├── resume_john_doe.pdf         # For --process-candidates
├── coverletter_john_doe.pdf    # Optional
└── application_john_doe.txt    # Optional
```

### Processed Structure (System Organizes)
```
data/
├── jobs/{job_name}/
│   ├── job_description.pdf
│   ├── ideal_candidate.txt
│   └── warning_flags.txt  
├── candidates/{job_name}/
│   └── {candidate_name}/
│       ├── resume.pdf
│       ├── cover_letter.pdf  
│       ├── application.txt
│       └── review.json
└── output/{job_name}/
    ├── candidate_scores.csv
    ├── summary_report.html
    └── detailed_reviews/
```

## Processing Pipeline

### 1. Job Setup Flow
```
Intake Files → Validation → Text Extraction → Job Context Creation → File Organization
```

### 2. Candidate Processing Flow  
```
Intake Files → Name Extraction → Text Extraction → AI Evaluation → Result Storage → CSV Generation
```

### 3. Display Flow
```
Stored Results → Ranking → Terminal Display / CSV Opening
```

## API Integration Strategy

### OpenAI Integration
- **Connection Testing**: Minimal API call to verify connectivity
- **Rate Limiting**: Built-in retry logic with exponential backoff
- **Error Handling**: Graceful degradation with clear error messages
- **Prompt Engineering**: Structured prompts for consistent evaluation format

### Sample Evaluation Prompt Structure
```
You are evaluating job candidates. Analyze the following:

JOB DESCRIPTION:
{job_description}

IDEAL CANDIDATE PROFILE:  
{ideal_candidate}

WARNING FLAGS:
{warning_flags}

CANDIDATE MATERIALS:
Resume: {resume_text}
Cover Letter: {cover_letter}  
Application: {application}

Provide evaluation in this exact JSON format:
{
  "overall_score": 0-100,
  "recommendation": "STRONG_YES|YES|MAYBE|NO|STRONG_NO",
  "strengths": ["strength1", "strength2"],
  "concerns": ["concern1", "concern2"], 
  "interview_priority": "HIGH|MEDIUM|LOW",
  "detailed_notes": "comprehensive evaluation"
}
```

## Testing Strategy

### Unit Tests (Fast, No External Dependencies)
- **File Processing**: Test with temporary files and known content
- **Data Models**: Validate serialization, validation rules
- **Output Generation**: Test CSV/terminal formatting with mock data
- **Configuration**: Test environment loading with temporary .env files

### Integration Tests (Real External Dependencies)  
- **API Connectivity**: Test real OpenAI calls with test account
- **End-to-End Pipeline**: Process real files through complete workflow
- **Error Scenarios**: Network failures, invalid files, missing API keys

### Test Organization
```
tests/
├── unit/
│   ├── test_file_processor.py
│   ├── test_models.py  
│   ├── test_output_generator.py
│   └── test_config.py
├── integration/
│   ├── test_api_client.py
│   ├── test_end_to_end_pipeline.py
│   └── test_error_scenarios.py
└── fixtures/
    ├── sample_job_description.pdf
    ├── sample_resume.pdf
    └── sample_responses.json
```

## Implementation Phases

### Phase 1: Foundation
1. Setup project structure and dependencies (`requirements.txt`)
2. Implement configuration management (`config.py`)  
3. Create data models (`models.py`)
4. Build API client with connection testing (`open_api_test_connection.py`)

### Phase 2: Core Pipeline
1. Implement file processing (`file_processor.py`)
2. Build output generation (`output_generator.py`)  
3. Create main CLI interface (`candidate_reviewer.py`)
4. Add comprehensive error handling

### Phase 3: Refinement  
1. Optimize prompt engineering for consistent results
2. Add advanced file format support
3. Implement result caching and incremental processing
4. Create comprehensive test suite

## Error Handling Strategy

### User-Friendly Errors
- Missing API key → Clear instructions to add to .env
- No files in intake → Instructions on file placement and naming
- API failures → Connection troubleshooting steps
- Invalid file formats → Supported format guidance

### Graceful Degradation
- Partial file processing continues even if some files fail
- Clear reporting of which files succeeded/failed
- Ability to resume processing from where it left off

## Security Considerations

### API Key Management
- Never log or display API keys
- Load from .env file only
- Validate key format before use
- Clear error messages for invalid keys

### File Processing  
- Validate file types before processing
- Sanitize extracted text content
- Limit file sizes to prevent memory issues
- Secure temporary file handling

## Performance Optimization

### File Processing
- Stream large PDF processing to manage memory
- Cache extracted text to avoid reprocessing
- Process candidates in parallel where possible
- Minimize API calls through intelligent batching

### API Usage
- Batch multiple candidates per API call when possible
- Implement intelligent retry logic with exponential backoff
- Cache results to avoid duplicate API calls for same candidate

## Questions for Clarification

1. **API Model Selection**: Should we default to GPT-4 or GPT-3.5-turbo for evaluations? What's the preference for cost vs. quality?

2. **File Size Limits**: What are reasonable limits for PDF file sizes? Should we compress or reject oversized files?

3. **Concurrent Processing**: How many candidates should we process simultaneously to balance speed vs. API rate limits?

4. **Result Persistence**: Should we store raw API responses for audit trails, or just the structured evaluations?

5. **Incremental Updates**: If a job description changes, should we re-evaluate all existing candidates or just process new ones?

6. **Human Feedback Loop**: The README mentions learning from feedback - should we implement a feedback mechanism in this phase or save for later?

This document provides the foundation for building a robust, maintainable AI Job Candidate Reviewer system following the specified principles and requirements.