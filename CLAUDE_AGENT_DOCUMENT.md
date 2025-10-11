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
- `--provide-feedback "job_name" "candidate_name"`: Interactive feedback collection
- `--re-evaluate "job_name" [candidate_names]`: Re-evaluate with updated insights
- `--show-insights "job_name"`: Display current AI insights for job

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
    timestamp: datetime
    ai_insights_used: Optional[str] = None  # Insights applied during evaluation

@dataclass
class HumanFeedback:
    evaluation_id: str
    human_recommendation: str  # STRONG_YES, YES, MAYBE, NO, STRONG_NO
    human_score: Optional[int] = None  # 0-100, optional
    feedback_notes: str
    specific_corrections: Dict[str, str]  # field -> corrected_value
    timestamp: datetime

@dataclass  
class JobInsights:
    job_name: str
    generated_insights: str  # AI-generated insights from feedback patterns
    feedback_count: int
    last_updated: datetime
    effectiveness_metrics: Dict[str, float]  # accuracy improvements, etc.

@dataclass
class FeedbackRecord:
    candidate_name: str
    original_evaluation: Evaluation
    human_feedback: HumanFeedback
    insights_generated: Optional[str] = None
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
    max_file_size_mb: int = 2
```

### 7. Feedback System (`feedback_manager.py`)
**Responsibility**: Human feedback collection and AI learning system

**Key Functions**:
- Collect human feedback on AI evaluations
- Build job-specific insights from feedback patterns
- Enable re-evaluation of candidates with updated insights
- Track feedback effectiveness over time

**Architecture**:
```python
class FeedbackManager:
    def __init__(self, config: Config)
    def collect_feedback(self, job_name: str, candidate_name: str, feedback: HumanFeedback) -> None
    def build_insights(self, job_name: str) -> JobInsights  
    def trigger_re_evaluation(self, job_name: str, candidate_names: List[str] = None) -> None
    def get_feedback_history(self, job_name: str) -> List[FeedbackRecord]
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
│   ├── warning_flags.txt
│   └── insights.json              # AI-generated insights from feedback
├── candidates/{job_name}/
│   └── {candidate_name}/
│       ├── resume.pdf
│       ├── cover_letter.pdf  
│       ├── application.txt
│       ├── evaluation.json        # Current AI evaluation
│       ├── evaluation_history.json # Previous evaluations
│       └── feedback.json          # Human feedback records
└── output/{job_name}/
    ├── candidate_scores.csv
    ├── summary_report.html
    ├── detailed_reviews/
    └── feedback_summary.json      # Aggregated feedback metrics
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

### 4. Feedback Learning Flow
```
AI Evaluation → Human Review → Feedback Collection → Insight Generation → Updated Job Context → Re-evaluation (Optional)
```

### 5. File Size Validation Flow
```
File Upload → Size Check (2MB limit) → Accept/Reject → Error Message (if rejected)
```

## API Integration Strategy

### OpenAI Integration
- **Model**: GPT-5 (latest available model)
- **Connection Testing**: Minimal API call to verify connectivity  
- **Rate Limiting**: Built-in retry logic with exponential backoff
- **Error Handling**: Graceful degradation with clear error messages
- **Prompt Engineering**: Structured prompts for consistent evaluation format
- **Feedback Integration**: Dynamic prompt enhancement using job-specific insights

### Enhanced Evaluation Prompt Structure (with Feedback Learning)
```
You are evaluating job candidates. Analyze the following:

JOB DESCRIPTION:
{job_description}

IDEAL CANDIDATE PROFILE:  
{ideal_candidate}

WARNING FLAGS:
{warning_flags}

AI INSIGHTS FROM PREVIOUS FEEDBACK:
{job_insights}
Note: These insights were generated from human feedback on previous evaluations for this role.

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
  "detailed_notes": "comprehensive evaluation",
  "insights_applied": "which specific insights influenced this evaluation"
}
```

### Insight Generation Prompt (for Feedback Learning)
```
Based on the following human feedback patterns for the job "{job_name}", generate specific insights that will improve future candidate evaluations:

JOB CONTEXT:
- Description: {job_description}
- Ideal Candidate: {ideal_candidate} 
- Warning Flags: {warning_flags}

FEEDBACK PATTERNS:
{aggregated_feedback_data}

Generate insights in this JSON format:
{
  "evaluation_criteria_refinements": "specific adjustments to scoring criteria",
  "strength_identification_patterns": "what human reviewers consistently value",
  "concern_identification_patterns": "what human reviewers consistently flag", 
  "scoring_calibration": "adjustments to overall scoring approach",
  "recommendation_logic": "refined logic for recommendation categories"
}
```

## Testing Strategy

### Unit Tests (Fast, No External Dependencies)
- **File Processing**: Test with temporary files and known content (including 2MB size limit)
- **Data Models**: Validate serialization, validation rules, feedback structures
- **Output Generation**: Test CSV/terminal formatting with mock data
- **Configuration**: Test environment loading with temporary .env files
- **Feedback System**: Test insight generation logic, feedback aggregation

### Integration Tests (Real External Dependencies)  
- **API Connectivity**: Test real OpenAI calls with GPT-5 (test account)
- **End-to-End Pipeline**: Process real files through complete workflow
- **Feedback Loop**: Test complete feedback → insight → re-evaluation cycle
- **Error Scenarios**: Network failures, invalid files, missing API keys, oversized files

### Test Organization
```
tests/
├── unit/
│   ├── test_file_processor.py
│   ├── test_models.py  
│   ├── test_output_generator.py
│   ├── test_config.py
│   └── test_feedback_manager.py
├── integration/
│   ├── test_api_client.py
│   ├── test_end_to_end_pipeline.py
│   ├── test_feedback_loop.py
│   └── test_error_scenarios.py
└── fixtures/
    ├── sample_job_description.pdf
    ├── sample_resume.pdf
    ├── sample_responses.json
    ├── sample_feedback.json
    └── large_file_2mb_plus.pdf
```

## Implementation Phases

### Phase 1: Foundation & Core Pipeline
1. Setup project structure and dependencies (`requirements.txt`)
2. Implement configuration management with 2MB file size limits (`config.py`)  
3. Create data models including feedback structures (`models.py`)
4. Build API client with GPT-5 integration and connection testing (`open_api_test_connection.py`)
5. Implement file processing with size validation (`file_processor.py`)
6. Build output generation (`output_generator.py`)  
7. Create main CLI interface for basic operations (`candidate_reviewer.py`)

### Phase 2: Feedback System & Learning
1. Implement feedback manager (`feedback_manager.py`)
2. Add feedback collection CLI commands (`--provide-feedback`)
3. Build insight generation from feedback patterns  
4. Implement re-evaluation functionality (`--re-evaluate`)
5. Add insight display functionality (`--show-insights`)
6. Enhanced prompt engineering with dynamic insight integration

### Phase 3: Optimization & Polish
1. Serial processing optimization with future concurrency design
2. Advanced error handling and user guidance
3. Result caching and incremental processing
4. Comprehensive test suite (unit + integration)
5. Performance monitoring and feedback effectiveness tracking

## Error Handling Strategy

### User-Friendly Errors
- Missing API key → Clear instructions to add to .env
- No files in intake → Instructions on file placement and naming
- Oversized files (≥2MB) → Clear file size limit message with suggestions
- API failures → Connection troubleshooting steps  
- Invalid file formats → Supported format guidance
- Missing feedback context → Guidance on providing meaningful feedback

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

## Requirements Clarifications (Confirmed)

1. **API Model Selection**: Use GPT-5 (latest model available)
2. **File Size Limits**: Reject files 2MB or larger with clear error message  
3. **Processing Strategy**: Serial processing initially, designed for future concurrency scaling
4. **Result Persistence**: Store structured JSON (agent-processable + human-readable)
5. **Incremental Updates**: Re-evaluate existing candidates when job description changes (rare scenarios)
6. **Human Feedback Loop**: Critical feature - implement comprehensive feedback system for continuous improvement

This document provides the foundation for building a robust, maintainable AI Job Candidate Reviewer system following the specified principles and requirements.
