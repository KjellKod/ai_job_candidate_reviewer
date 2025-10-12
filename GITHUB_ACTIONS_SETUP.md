# GitHub Actions Setup Guide

## Required Setup for CI/CD Pipeline

### 1. Basic Test Suite (No Secrets Required)

The main test suite runs **without any API keys** and includes:
- ✅ Unit tests (all mocked)
- ✅ Integration tests (mock AI client)
- ✅ Security tests
- ✅ Code quality checks (linting, formatting)
- ✅ Cross-platform compatibility tests

**No GitHub Secrets needed** - the pipeline will work immediately after pushing to GitHub.

### 2. Optional: Real API Integration Tests

If you want to add **optional** real API integration tests that actually call OpenAI's API:

#### Step 1: Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these **Repository Secrets**:

| Secret Name | Description | Example Value | Required |
|-------------|-------------|---------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-proj-abc123...` | Optional* |
| `OPENAI_MODEL` | Preferred OpenAI model | `gpt-4` or `gpt-3.5-turbo` | Optional |

*Only required if you want real API integration tests

#### Step 2: Update Repository Owner

In `.github/workflows/test.yml`, update line 242:

```yaml
if: github.event_name == 'push' && github.ref == 'refs/heads/main' && github.repository_owner == 'your-username'
```

Replace `'your-username'` with your actual GitHub username.

#### Step 3: Create Real API Integration Tests

Create tests marked with `@pytest.mark.api_integration`:

```python
import pytest
from ai_client import AIClient
from config import Config

@pytest.mark.api_integration
def test_real_openai_api_call():
    """Test actual OpenAI API integration (requires real API key)."""
    config = Config()
    
    # This test only runs when OPENAI_API_KEY is available
    if not config.openai_api_key:
        pytest.skip("Real API key not available")
    
    ai_client = AIClient(config.openai_api_key, config.preferred_model)
    # ... actual API test logic
```

### 3. Security Best Practices

#### ✅ Safe Practices:
- Main test suite runs without any real API keys
- API integration tests only run on main branch pushes
- Secrets are only available to the repository owner
- Tests gracefully skip when secrets aren't available

#### ❌ Avoid These Mistakes:
- Never hardcode API keys in test files
- Don't make API integration tests required for PRs
- Don't expose secrets in test output or logs

### 4. Workflow Behavior

| Scenario | Unit Tests | Integration Tests | API Integration Tests |
|----------|------------|-------------------|----------------------|
| Fork/PR | ✅ Pass | ✅ Pass | ⏭️ Skipped |
| Main branch (no secrets) | ✅ Pass | ✅ Pass | ⏭️ Skipped |
| Main branch (with secrets) | ✅ Pass | ✅ Pass | ✅ Pass |

### 5. Manual Testing

To run the full test suite locally:

```bash
# Run all tests except API integration
pytest -m "not api_integration"

# Run only API integration tests (requires .env with real API key)
pytest -m "api_integration"

# Run all tests (will skip API integration if no key)
pytest
```

### 6. Monitoring and Costs

- **Unit/Integration tests**: Free (no API calls)
- **API integration tests**: Uses your OpenAI API quota
- **Recommendation**: Only enable API integration tests if you need them

### 7. Troubleshooting

**Q: Tests are failing with "No API key" errors**
A: This is expected and safe. The main test suite doesn't need real API keys.

**Q: API integration tests aren't running**
A: Check that:
1. You're on the main branch
2. Repository owner is correct in the workflow
3. `OPENAI_API_KEY` secret is set
4. The condition in the workflow matches your setup

**Q: I don't want any real API calls**
A: Perfect! Just use the default setup. The main test suite is completely isolated and secure.

## Summary

- **Default setup**: No secrets needed, full test coverage with mocks
- **Optional API tests**: Add `OPENAI_API_KEY` secret for real API integration tests
- **Security**: All secrets are optional and safely handled
- **Cost**: Main tests are free, API tests use your OpenAI quota
