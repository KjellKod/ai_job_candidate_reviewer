#!/usr/bin/env python3
"""Verify installation and dependencies for AI Job Candidate Reviewer."""

import sys
import importlib
from pathlib import Path


def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(
        f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        "openai",
        "python-dotenv",
        "click",
        "pydantic",
        "PyPDF2",
        "python-magic",
        "pandas",
    ]

    missing = []
    for package in required_packages:
        try:
            # Handle package name variations
            import_name = package
            if package == "python-dotenv":
                import_name = "dotenv"
            elif package == "python-magic":
                import_name = "magic"
            elif package == "PyPDF2":
                import_name = "PyPDF2"

            importlib.import_module(import_name)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)

    return missing


def check_files():
    """Check if core files exist."""
    required_files = [
        "config.py",
        "models.py",
        "open_api_test_connection.py",
        "file_processor.py",
        "output_generator.py",
        "candidate_reviewer.py",
        "requirements.txt",
    ]

    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing.append(file)

    return missing


def main():
    """Main verification function."""
    print("🔍 AI Job Candidate Reviewer - Installation Verification\n")

    # Check Python version
    print("📋 Python Version:")
    python_ok = check_python_version()

    # Check dependencies
    print("\n📦 Dependencies:")
    missing_deps = check_dependencies()

    # Check files
    print("\n📄 Core Files:")
    missing_files = check_files()

    # Summary
    print("\n" + "=" * 50)
    if python_ok and not missing_deps and not missing_files:
        print("🎉 Installation verification successful!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and add your OpenAI API key")
        print("2. Run: python3 candidate_reviewer.py test-connection")
        print("3. See GETTING_STARTED.md for usage instructions")
    else:
        print("❌ Installation issues found:")

        if not python_ok:
            print("   • Upgrade Python to 3.8 or higher")

        if missing_deps:
            print("   • Install missing dependencies:")
            print(f"     pip install {' '.join(missing_deps)}")
            print("   • Or install all: pip install -r requirements.txt")

        if missing_files:
            print("   • Missing core files:")
            for file in missing_files:
                print(f"     - {file}")

        sys.exit(1)


if __name__ == "__main__":
    main()
