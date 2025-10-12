#!/bin/bash
# Pre-push validation script
# Run this before pushing to ensure CI will pass

set -e  # Exit on first error

echo "🚀 Pre-Push Validation Script"
echo "=============================="
echo ""

# Check if we're in the right directory
if [ ! -f "candidate_reviewer.py" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# 1. Format code with black
echo "1️⃣  Formatting code with black..."
python3 -m black . || { echo "❌ Black formatting failed"; exit 1; }
echo "✅ Black formatting complete"
echo ""

# 2. Sort imports with isort
echo "2️⃣  Sorting imports with isort..."
python3 -m isort . || { echo "❌ isort failed"; exit 1; }
echo "✅ Import sorting complete"
echo ""

# 3. Check linting with flake8
echo "3️⃣  Checking code quality with flake8..."
python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || { echo "❌ Flake8 found critical errors"; exit 1; }
echo "✅ Flake8 check passed"
echo ""

# 4. Run all tests
echo "4️⃣  Running test suite..."
# Create test data directory if it doesn't exist (for local testing)
mkdir -p test_data/{intake,jobs,candidates,output}
export BASE_DATA_PATH=./test_data
python3 -m pytest tests/ -v --tb=short || { echo "❌ Tests failed"; exit 1; }
echo "✅ All tests passed"
echo ""

# 5. Verify installation
echo "5️⃣  Verifying installation..."
python3 verify_installation.py || { echo "❌ Installation verification failed"; exit 1; }
echo "✅ Installation verified"
echo ""

# Summary
echo "=============================="
echo "🎉 All checks passed!"
echo "✅ Code formatted (black)"
echo "✅ Imports sorted (isort)"
echo "✅ Linting passed (flake8)"
echo "✅ Tests passed (pytest)"
echo "✅ Installation verified"
echo ""
echo "👍 Ready to push to GitHub!"
echo "=============================="

