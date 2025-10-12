# AI Job Candidate Reviewer - Architecture

## File Structure & Responsibilities

### 🔧 Core Components

| File | Responsibility | Can Run Standalone? |
|------|---------------|-------------------|
| `candidate_reviewer.py` | Main CLI interface and orchestration | ✅ (Main entry point) |
| `open_api_test_connection.py` | **ONLY** OpenAI connection testing & model selection | ✅ (Standalone tester) |
| `ai_client.py` | AI evaluation and insights generation | ❌ (Library component) |
| `config.py` | Configuration and environment management | ❌ (Library component) |
| `models.py` | Type-safe data structures | ❌ (Library component) |
| `file_processor.py` | File handling, PDF extraction, organization | ❌ (Library component) |
| `output_generator.py` | CSV/HTML reports and terminal display | ❌ (Library component) |

### 🧪 Testing & Documentation

| File | Purpose |
|------|---------|
| `tests/unit/` | Unit tests (18 tests passing) |
| `tests/integration/` | Integration tests |
| `CLAUDE_AGENT_DOCUMENT.md` | Complete system architecture document |
| `GETTING_STARTED.md` | Quick start guide |
| `ARCHITECTURE.md` | This file - architecture overview |

## Key Design Principles

### ✅ **Single Responsibility Principle (SRP)**
- `open_api_test_connection.py` **ONLY** handles connection testing
- `ai_client.py` **ONLY** handles AI evaluation and insights
- Each file has one clear purpose

### ✅ **Separation of Concerns**
- Connection testing is separate from AI evaluation
- File processing is separate from output generation
- Configuration is centralized but separate from business logic

### ✅ **Standalone Execution**
- `open_api_test_connection.py` can be run independently
- Provides human-readable output for debugging
- Useful for troubleshooting API issues

## Usage Examples

### Standalone Connection Testing
```bash
python3 open_api_test_connection.py
```
Output:
```
🔧 OpenAI API Connection Tester
========================================
🔄 Testing connection with model: gpt-4o-2024-11-20
✅ API connection successful
   Using: gpt-4o-2024-11-20 (Available GPT models: 65)
   Response time: 517ms

📋 Available GPT Models:
    1. chatgpt-4o-latest
    2. gpt-3.5-turbo
    ...
🎉 Connection test completed successfully!
```

### Main System Usage
```bash
python3 candidate_reviewer.py test-connection
python3 candidate_reviewer.py setup-job "job_name"
python3 candidate_reviewer.py process-candidates "job_name"
python3 candidate_reviewer.py show-candidates "job_name"
```

## Model Selection Logic

1. **Priority Order**: GPT-5 Pro → GPT-5 → GPT-4o latest → GPT-4o standard
2. **Automatic Fallback**: Tests each model availability
3. **User Override**: `OPENAI_MODEL` environment variable
4. **Graceful Degradation**: Always finds a working model

## Data Flow

```
User Input → Config → Connection Tester → AI Client → File Processor → Output Generator
```

1. **Config** loads environment and validates settings
2. **Connection Tester** finds best available model
3. **AI Client** uses selected model for evaluations
4. **File Processor** handles PDF extraction and organization
5. **Output Generator** creates CSV, HTML, and terminal displays

This architecture ensures clean separation of concerns while maintaining ease of use and debugging capabilities.
