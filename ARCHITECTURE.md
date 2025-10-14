# AI Job Candidate Reviewer - Architecture

## File Structure & Responsibilities

### 🔧 Core Components

| File | Responsibility | Can Run Standalone? |
|------|---------------|-------------------|
| `candidate_reviewer.py` | Main CLI interface and orchestration | ✅ (Main entry point) |
| `open_api_test_connection.py` | **ONLY** OpenAI connection testing & model selection | ✅ (Standalone tester) |
| `ai_client.py` | AI evaluation and insights generation | ❌ (Library component) |
| `policy/filter_enforcer.py` | Deterministic screening filter enforcement | ❌ (Library component) |
| `feedback_manager.py` | Feedback collection, insights generation, re-evaluation | ❌ (Library component) |
| `config.py` | Configuration and environment management | ❌ (Library component) |
| `models.py` | Type-safe data structures | ❌ (Library component) |
| `file_processor.py` | File handling, PDF extraction, organization | ❌ (Library component) |
| `output_generator.py` | CSV/HTML reports and terminal display | ❌ (Library component) |

### 🧪 Testing & Documentation

| File | Purpose |
|------|---------|
| `tests/unit/` | Unit tests (73 tests passing) |
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

### Basic Evaluation Flow

```
User Input → Config → Connection Tester → AI Client → File Processor → Output Generator
```

1. **Config** loads environment and validates settings
2. **Connection Tester** finds best available model
3. **AI Client** uses selected model for evaluations
4. **File Processor** handles PDF extraction and organization
5. **Output Generator** creates CSV, HTML, and terminal displays

### Evaluation with Screening Filters

```
Job Setup → Screening Filters Defined → AI Evaluation → Policy Enforcement → Output
```

1. **Screening filters** loaded from `screening_filters.json`
2. **AI Client** evaluates candidate and checks filter conditions
3. **AI** marks failed filters in `detailed_notes` field
4. **Policy Enforcer** deterministically applies penalties (double-checks AI)
5. **Output** shows which filters were triggered

### Feedback and Learning Loop

```
Feedback → Insights Generation → Re-evaluation → Updated Reports
```

1. **Feedback Manager** collects human feedback on evaluations
2. **Insights generated** after every 2 feedback records
3. **Re-evaluation** applies insights and updated filters
4. **Evaluation history** preserved in `evaluation_history.json`
5. **Reports regenerated** with updated scores

## Identity-Based Duplicate Detection

### Design

The system implements content-aware deduplication during candidate intake using identity matching rather than just filename comparison.

### Components

**Identifier Extraction** (`file_processor.py`):
- Regex patterns extract: emails, phone numbers, LinkedIn profiles, GitHub profiles
- Identifiers normalized for comparison (lowercase emails, digits-only phones, canonical URLs)
- Handles multiple identifiers per candidate

**Metadata Persistence**:
- Each candidate directory contains `candidate_meta.json` with extracted identifiers
- Metadata loaded at intake time to check for existing candidates
- Enables cross-batch duplicate detection

**Deduplication Logic** (`_determine_target_directory`):

| Scenario | Identifiers Overlap? | Action |
|----------|---------------------|--------|
| Same name, matching IDs | ✅ Yes | Merge into existing directory |
| Different names, matching IDs | ✅ Yes | Flag as potential fake, create `{name}__DUPLICATE_CHECK` and warn |
| Same name, no overlap | ❌ No (both have IDs) | Create `name__2` directory |
| Same name, no overlap | ❌ No (missing IDs) | Use existing directory |
| No existing match | - | Create new directory |

### Benefits

- **Prevents duplicate processing** of same candidate
- **Detects fake candidates** using different names with same contact info (without merging by default)
- **Handles name collisions** intelligently (different people with same name)
- **No false positives** - empty identifiers don't match

### Privacy

All identifier extraction happens locally. Identifiers are:
- Extracted from user-provided documents
- Stored in local `candidate_meta.json` files
- Never sent to OpenAI separately (only as part of full document text)

### Reporting Integration

- The intake step writes `DUPLICATE_WARNING.txt` into both involved profiles when identifiers overlap across different names
- `output_generator.py` reads these warnings and:
  - Adds "🚨 DUPLICATE" tag in terminal output with a short summary
  - Adds a "Flags" column in CSV with `DUPLICATE_IDENTIFIERS`
  - Adds a red banner in HTML per affected candidate with the warning summary

This architecture ensures clean separation of concerns while maintaining ease of use and debugging capabilities.

## Screening Filters Architecture

### Two-Layer Enforcement System

The system uses a hybrid approach to ensure reliable filter enforcement:

**Layer 1: AI Evaluation** (`ai_client.py`)
- Reads `screening_filters.json` during evaluation
- Includes filter conditions in evaluation prompt
- AI evaluates candidate against filters
- If filter matches, AI:
  - Writes "Failed filters: filter-id-1, filter-id-2" at top of `detailed_notes`
  - Applies penalties (score deductions, recommendation caps)
  - Includes reasoning in evaluation

**Layer 2: Policy Enforcement** (`policy/filter_enforcer.py`)
- Runs after AI evaluation completes
- Parses "Failed filters: ..." from `detailed_notes`
- Deterministically applies penalties
- Ensures AI didn't make calculation errors
- Validates recommendation caps/sets

### Why Two Layers?

**Problem:** AI models can be inconsistent. An AI might:
- Forget to apply a penalty
- Calculate deductions incorrectly  
- Set wrong recommendation value

**Solution:** Policy layer provides deterministic enforcement:
- Always applies exact penalties specified in filters
- Catches AI mistakes
- Ensures consistent behavior across evaluations

### Filter Lifecycle

```
1. Creation
   ├─ Interactive (during feedback when rejecting)
   └─ Manual (edit screening_filters.json)

2. Storage
   └─ Per-job: data/jobs/{job_name}/screening_filters.json

3. Application
   ├─ Load filters when evaluating
   ├─ AI checks conditions
   ├─ AI applies penalties
   └─ Policy layer enforces (double-check)

4. Reporting
   ├─ Failed filters shown in detailed_notes
   ├─ Flags in CSV/HTML reports
   └─ Clear explanation of why candidate was filtered
```

### Filter Schema

```json
{
  "version": 1,
  "updated_at": "ISO-8601 timestamp",
  "filters": [
    {
      "id": "unique-filter-id",
      "title": "Human-readable title",
      "when": "Condition description for AI",
      "action": {
        "set_recommendation": "NO | MAYBE | YES | ...",
        "cap_recommendation": "NO | MAYBE | YES | ...",
        "deduct_points": 0-100
      },
      "enabled": true,
      "source": "human | system",
      "rationale": "Why this filter exists"
    }
  ]
}
```

### Integration Points

- **candidate_reviewer.py**: CLI for feedback and filter creation
- **ai_client.py**: Reads filters, includes in prompt
- **policy/filter_enforcer.py**: Post-evaluation enforcement
- **feedback_manager.py**: Re-evaluation with filters
- **output_generator.py**: Display filter results in reports

## Re-evaluation System

### Features

**Smart Re-evaluation** (`feedback_manager.py`):
- Processes candidates in score order (highest first)
- Skips rejected candidates by default (unless explicitly specified)
- Shows score deltas: "was 60 → now 75 | Δ +15"
- Cleans up stale duplicate warnings before re-evaluation
- Progress indicators: "Re-evaluating 3/10..."

**Evaluation History Tracking**:
- Previous evaluations saved to `evaluation_history.json`
- Enables auditing and rollback
- Tracks how insights/filters improved evaluations

**Insights Application**:
- Loads job insights from `insights.json`
- Passes insights to AI during evaluation
- Insights help AI better match human preferences

### Re-evaluation Triggers

1. **After feedback** - Manual re-evaluation after providing feedback
2. **After insights** - System suggests re-evaluation when new insights generated
3. **After filter changes** - Re-evaluate to apply new/modified filters

### Performance Optimization

- **Highest scores first**: Focus on top candidates
- **Skip rejected**: Don't waste API calls on already-rejected candidates
- **Batch reports**: Generate reports once after all re-evaluations complete

## See Also

- **[SCREENING_FILTERS.md](SCREENING_FILTERS.md)** - Complete guide to screening filters
- **[README.md](README.md)** - User documentation
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development guide
