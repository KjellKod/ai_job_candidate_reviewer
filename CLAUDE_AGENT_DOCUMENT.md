# Claude Agent Document: AI Job Candidate Reviewer Implementation

## Project Overview

This document outlines the implementation strategy for the AI Job Candidate Reviewer system - a pipeline-based application that automates first-pass resume screening while maintaining human control and feedback loops.

### System Purpose
- Automate initial candidate screening using AI
- Provide consistent, structured candidate evaluations  
- Learn from human feedback to improve accuracy over time
- Generate actionable rankings and detailed reports

## Architecture Principles

### Core Design Principles
1. **Single Responsibility Principle (SRP)**: Each class/module has one clear purpose
2. **Don't Repeat Yourself (DRY)**: Shared logic extracted to reusable components
3. **Test-Driven Development (TDD)**: Write tests first, minimal mocking
4. **Pipeline Architecture**: Clean data flow through discrete processing stages
5. **Configuration-Driven**: Environment variables and config files over hard-coded values

### Testing Philosophy
- **Integration tests over unit tests**: Test real workflows with real data
- **Minimal mocking**: Only mock external services (OpenAI API) and filesystem at boundaries
- **Test data fixtures**: Use real PDF samples and expected outputs
- **End-to-end pipeline tests**: Verify complete workflows work correctly

## System Components

### 1. Core Pipeline Architecture

```
Input Stage → Processing Stage → AI Evaluation Stage → Output Stage
     ↓              ↓                    ↓                ↓
Job/Candidate → Document Parser → OpenAI Reviewer → Report Generator
   Intake        (PDF/TXT)        (API Client)       (CSV/HTML)
```

### 2. Component Breakdown

#### A. Configuration Management (`config/`)
- **Purpose**: Centralized configuration and environment handling
- **Responsibilities**:
  - Load `.env` variables (OPENAI_API_KEY)
  - Validate configuration completeness
  - Provide environment-specific settings
- **Files**:
  - `config.py` - Configuration loader and validator
  - `settings.py` - Default settings and constants

#### B. File Management (`file_manager/`)
- **Purpose**: Handle all file operations and organization
- **Responsibilities**:
  - File intake and organization
  - Directory structure management
  - File validation and parsing
- **Files**:
  - `intake_processor.py` - Process files from intake directories
  - `file_organizer.py` - Move and organize processed files
  - `document_parser.py` - Extract text from PDFs and documents

#### C. OpenAI Integration (`openai_client/`)
- **Purpose**: Handle all OpenAI API interactions
- **Responsibilities**:
  - API connection and authentication
  - Candidate evaluation requests
  - Response parsing and validation
- **Files**:
  - `openai_client.py` - Main API client
  - `openai_test_connection.py` - Connection testing utility
  - `prompts.py` - AI prompt templates and management

#### D. Evaluation Engine (`evaluation/`)
- **Purpose**: Core candidate evaluation logic
- **Responsibilities**:
  - Coordinate candidate assessment
  - Apply job-specific criteria
  - Score normalization and ranking
- **Files**:
  - `candidate_evaluator.py` - Main evaluation coordinator
  - `scoring_engine.py` - Score calculation and normalization
  - `criteria_matcher.py` - Match candidates to job requirements

#### E. Output Generation (`output/`)
- **Purpose**: Generate reports and rankings
- **Responsibilities**:
  - CSV file generation
  - HTML report creation  
  - Terminal display formatting
- **Files**:
  - `report_generator.py` - Create CSV and HTML reports
  - `ranking_display.py` - Terminal ranking output
  - `output_formatter.py` - Common formatting utilities

#### F. Command Line Interface (`cli/`)
- **Purpose**: User interaction and command handling
- **Responsibilities**:
  - Parse command line arguments
  - Coordinate pipeline execution
  - User feedback and error handling
- **Files**:
  - `candidate_reviewer.py` - Main CLI entry point
  - `command_handler.py` - Command parsing and dispatch
  - `user_interface.py` - Terminal interaction utilities

## Implementation Pipeline

### Stage 1: Foundation & Configuration
1. **Environment Setup**
   - Create project structure with clear module separation
   - Implement configuration management with `.env` support
   - Create OpenAI connection test utility

2. **File Management Foundation**
   - Build intake directory processing
   - Implement file organization system
   - Create document parsing utilities (PDF, TXT)

### Stage 2: OpenAI Integration
1. **API Client Development**
   - Implement OpenAI client with proper error handling
   - Create connection testing functionality
   - Build prompt template system

2. **Evaluation Framework**
   - Design candidate evaluation prompts
   - Implement response parsing and validation
   - Create scoring and ranking logic

### Stage 3: Pipeline Orchestration
1. **Core Pipeline**
   - Build job setup workflow
   - Implement candidate processing pipeline
   - Create evaluation coordination

2. **Output Generation**
   - Build CSV report generation
   - Implement terminal ranking display
   - Create HTML summary reports

### Stage 4: CLI Interface
1. **Command System**
   - Implement main CLI entry point
   - Build command parsing and validation
   - Create user feedback and error handling

2. **Integration Testing**
   - End-to-end pipeline tests
   - Error scenario testing
   - Performance validation

## Key Implementation Details

### 1. File Processing Strategy
```python
# Clean file organization pattern
data/
├── intake/                    # Drop zone for new files
│   ├── job_description.pdf    # Auto-detected
│   ├── ideal_candidate.txt    # Auto-detected
│   └── resume_name.pdf        # Pattern-based extraction
├── jobs/                      # Processed job data
│   └── {job_name}/
├── candidates/                # Processed candidate data
│   └── {job_name}/{candidate_name}/
└── output/                    # Generated reports
    └── {job_name}/
```

### 2. OpenAI Integration Pattern
```python
# Testable OpenAI client design
class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    def evaluate_candidate(self, job_context: JobContext, 
                          candidate_data: CandidateData) -> EvaluationResult:
        # Structured prompt generation and API call
        pass
    
    def test_connection(self) -> ConnectionResult:
        # Simple connection validation
        pass
```

### 3. Testing Strategy
```python
# Integration-focused testing approach
class TestCandidateEvaluation:
    def test_full_evaluation_pipeline(self):
        # Use real PDF files and expected outputs
        # Minimal mocking - only OpenAI API responses
        pass
    
    def test_file_processing_workflow(self):
        # Test with actual file fixtures
        # No mocking of file operations
        pass
```

### 4. Configuration Management
```python
# Environment-driven configuration
class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    DATA_DIR: str = "data"
    INTAKE_DIR: str = f"{DATA_DIR}/intake"
    # etc.
```

## Error Handling Strategy

### 1. Graceful Degradation
- Missing optional files (ideal_candidate.txt, warning_flags.txt) should not block processing
- Clear error messages for missing required files
- Validation at each pipeline stage with informative feedback

### 2. Recovery Mechanisms  
- Partial processing recovery (resume where left off)
- File validation before processing
- API error handling with retry logic

### 3. User Feedback
- Progress indicators for long-running operations
- Clear error messages with suggested fixes
- Helpful validation messages

## Success Criteria

### 1. Functional Requirements
- ✅ Process job descriptions and candidate files correctly
- ✅ Generate accurate OpenAI evaluations
- ✅ Create well-formatted CSV and terminal outputs
- ✅ Handle all documented CLI commands

### 2. Quality Requirements
- ✅ Clean, testable code following SRP and DRY principles
- ✅ Comprehensive test coverage with minimal mocking
- ✅ Clear error handling and user feedback
- ✅ Maintainable pipeline architecture

### 3. Performance Requirements  
- ✅ Process candidates efficiently (parallel where possible)
- ✅ Handle reasonable file sizes (typical resumes/job descriptions)
- ✅ Responsive CLI interface

## Next Steps

After this document is approved:

1. **Create project structure** with proper module organization
2. **Implement foundation components** (config, file management)
3. **Build OpenAI integration** with connection testing
4. **Develop core evaluation pipeline**
5. **Create CLI interface** and command handling
6. **Add comprehensive testing** throughout development
7. **Integration testing** and final validation

The implementation will follow TDD principles, building one component at a time with tests driving the design, ensuring each piece works correctly before moving to the next stage.