# Development Guide

## Quick Commands

### Before Pushing Code

Run the automated pre-push script:

```bash
./pre-push.sh
```

This will automatically:
1. ✅ Format code with `black`
2. ✅ Sort imports with `isort`
3. ✅ Check code quality with `flake8`
4. ✅ Run all tests with `pytest`
5. ✅ Verify installation

### Manual Commands

If you need to run steps individually:

```bash
# Format code
python3 -m black .

# Sort imports
python3 -m isort .

# Check linting (critical errors only)
python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Check linting (all issues, non-blocking)
python3 -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

# Run tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/unit/test_config.py -v

# Run tests with coverage
python3 -m pytest tests/ -v --cov=. --cov-report=term-missing

# Verify installation
python3 verify_installation.py
```

## Running Tests

### All Tests
```bash
python3 -m pytest tests/ -v
```

### Unit Tests Only
```bash
python3 -m pytest tests/unit/ -v
```

### Integration Tests Only
```bash
python3 -m pytest tests/integration/ -v
```

### Specific Test
```bash
python3 -m pytest tests/unit/test_typo_detection.py::TestTypoDetection::test_typo_detection_with_resume_typo -v
```

### With Coverage
```bash
python3 -m pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html  # View coverage report
```

## Code Quality Tools

### Black (Code Formatter)
- **Purpose**: Enforces consistent code style
- **Config**: `pyproject.toml` (line-length: 88)
- **Run**: `python3 -m black .`
- **Check only**: `python3 -m black --check .`

### isort (Import Sorter)
- **Purpose**: Organizes imports (stdlib → third-party → local)
- **Config**: `pyproject.toml` (profile: "black")
- **Run**: `python3 -m isort .`
- **Check only**: `python3 -m isort --check-only .`

### flake8 (Linter)
- **Purpose**: Catches syntax errors, undefined names, style issues
- **Config**: `.flake8`
- **Run**: `python3 -m flake8 .`

## Git Workflow

### Before Committing
```bash
# Run pre-push checks
./pre-push.sh

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature: descriptive message"
```

### Before Pushing
```bash
# Ensure all checks pass
./pre-push.sh

# Push to GitHub
git push origin main
```

## CI/CD Pipeline

When you push to GitHub, the following runs automatically:

1. **Test Suite** (Python 3.9, 3.10, 3.11, 3.12)
   - Unit tests
   - Integration tests
   - Code coverage reporting

2. **Code Quality**
   - Black formatting check
   - isort import check
   - flake8 linting

3. **Security Scan**
   - Bandit security analysis
   - API key detection

4. **Cross-Platform** (Ubuntu, Windows, macOS)
   - Compatibility tests

5. **Documentation Validation**
   - Required docs present

6. **Optional: API Integration Tests** (main branch only)
   - Uses `OPENAI_API_KEY` secret
   - Tests real API calls

## Troubleshooting

### "Import errors" in CI
Run: `python3 -m isort .`

### "Black formatting errors" in CI
Run: `python3 -m black .`

### "Flake8 errors" in CI
Check the error and fix the code, then run: `python3 -m flake8 .`

### Tests pass locally but fail in CI
- Check Python version (CI tests 3.9-3.12)
- Check that all dependencies are in `requirements.txt`
- Review the CI logs on GitHub Actions

## Quick Reference

| Task | Command |
|------|---------|
| **Pre-push check** | `./pre-push.sh` |
| **Format code** | `python3 -m black .` |
| **Sort imports** | `python3 -m isort .` |
| **Run all tests** | `python3 -m pytest tests/ -v` |
| **Run with coverage** | `python3 -m pytest tests/ --cov=.` |
| **Check linting** | `python3 -m flake8 .` |
| **Verify install** | `python3 verify_installation.py` |

## See Also

- `GITHUB_ACTIONS_SETUP.md` - CI/CD configuration
- `GITHUB_ACTIONS_SUMMARY.md` - CI/CD overview
- `SECURITY_TESTING_GUIDELINES.md` - Security best practices
- `LINTING_STRATEGY.md` - Detailed linting rules

