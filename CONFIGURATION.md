# Configuration Guide

## Environment Variables

The AI Job Candidate Reviewer can be configured using environment variables in a `.env` file.

### Required Configuration

Create a `.env` file in the project root (or copy from `.env.example`):

```bash
cp .env.example .env
```

#### `OPENAI_API_KEY` (Required)

Your OpenAI API key for AI-powered candidate evaluation.

```env
OPENAI_API_KEY=sk-proj-your-api-key-here
```

**Get your API key:** https://platform.openai.com/api-keys

### Optional Configuration

#### `OPENAI_MODEL` (Optional)

Preferred OpenAI model. By default, the system automatically selects the best available model with this priority: `gpt-5` → `gpt-5-2025` → `gpt-5-mini` → `gpt-5-nano` → `gpt-4-turbo` → `gpt-4`.

```env
OPENAI_MODEL=gpt-5
```

**Options:**
- `gpt-5` (newest, most capable - auto-selected if available)
- `gpt-5-mini` (faster GPT-5 variant)
- `gpt-4-turbo` (faster GPT-4 variant)
- `gpt-4` (classic GPT-4)

**Note:** The system automatically falls back to the best available model from your OpenAI account. You only need to set this if you want to force a specific model.

#### `BASE_DATA_PATH` (Optional)

Base directory for all data storage. Defaults to `./data`.

```env
BASE_DATA_PATH=./data
```

**Use cases:**
- Testing with isolated test data: `BASE_DATA_PATH=./test_data`
- Custom storage location: `BASE_DATA_PATH=/var/app/data`
- Separating dev/prod data: `BASE_DATA_PATH=./data_dev`

**Directory structure:**
```
{BASE_DATA_PATH}/
├── intake/         # Drop files here for processing
├── jobs/           # Processed job descriptions
├── candidates/     # Processed candidate files
└── output/         # Generated reports (CSV, HTML)
```

#### Individual Path Overrides (Advanced)

Override specific paths instead of using `BASE_DATA_PATH`:

```env
INTAKE_PATH=./custom_intake
JOBS_PATH=./custom_jobs
CANDIDATES_PATH=./custom_candidates
OUTPUT_PATH=./custom_output
```

**Note:** If `BASE_DATA_PATH` is set, these default to subdirectories of it. These overrides are only needed for non-standard layouts.

#### `MAX_FILE_SIZE_MB` (Optional)

Maximum file size for uploads in megabytes. Defaults to `2`.

```env
MAX_FILE_SIZE_MB=5
```

## Configuration Examples

### Minimal Setup (Recommended)

```env
# .env
OPENAI_API_KEY=sk-proj-abc123...
```

All other settings use sensible defaults.

### Development Setup

```env
# .env
OPENAI_API_KEY=sk-proj-abc123...
OPENAI_MODEL=gpt-4-turbo  # Optional: force a specific model. See also [OpenAI --> Settings](https://platform.openai.com/settings/organization/general)
BASE_DATA_PATH=./data_dev
MAX_FILE_SIZE_MB=5
```

### Testing Setup

When running tests, set environment variables directly:

```bash
BASE_DATA_PATH=./test_data python3 -m pytest tests/
```

Or in your test script:
```bash
export BASE_DATA_PATH=./test_data
python3 -m pytest tests/
```

The CI/CD pipeline automatically uses `./test_data` to avoid conflicts with your local data.

## Configuration Priority

Settings are loaded in this order (highest priority first):

1. **Environment variables** (set in shell or `.env` file)
2. **Default values** (hardcoded in `config.py`)

## Viewing Current Configuration

To see your current configuration:

```python
from config import Config

config = Config()
print(config)
```

Output:
```
Config:
  Base Data Path: ./data
  Intake Path: ./data/intake
  Jobs Path: ./data/jobs
  Candidates Path: ./data/candidates
  Output Path: ./data/output
  Max File Size: 2MB
  API Key: *** (configured)
  Preferred Model: gpt-4
```

## Common Issues

### "No such directory" errors

The application automatically creates directories as needed. If you see this error, check:
- You have write permissions in the `BASE_DATA_PATH` location
- The path is valid and accessible

### "API key not configured"

Make sure:
1. `.env` file exists in project root
2. `OPENAI_API_KEY` is set in `.env`
3. No extra spaces or quotes around the value

### Tests using wrong data directory

Tests should use `./test_data` to avoid interfering with your actual data:

```bash
BASE_DATA_PATH=./test_data python3 -m pytest tests/
```

The `pre-push.sh` script handles this automatically.

## See Also

- `README.md` - Main project documentation
- `GETTING_STARTED.md` - Quick start guide
- `DEVELOPMENT.md` - Development workflow
- `.env.example` - Example environment file template

