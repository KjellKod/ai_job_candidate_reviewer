#!/usr/bin/env python3
"""Debug typo detection."""

from pathlib import Path

from config import Config
from file_processor import FileProcessor


def main():
    """Debug typo detection."""
    config = Config()
    processor = FileProcessor(config, interactive=True)

    intake_path = Path(config.intake_path)

    print("🔍 All files in intake:")
    for file_path in intake_path.iterdir():
        if file_path.is_file():
            print(f"   {file_path.name}")

    print("\n🔍 Testing typo detection directly:")

    # Test specific files
    test_files = ["resum_john_doe.pdf", "applicaton_john_doe.txt"]
    expected_prefixes = ["resume_", "coverletter_", "application_"]

    for filename in test_files:
        file_path = intake_path / filename
        if file_path.exists():
            print(f"\n📁 Testing: {filename}")
            result = processor._try_typo_correction(file_path, expected_prefixes)
            print(f"   Result: {result}")


if __name__ == "__main__":
    main()
