#!/usr/bin/env python3
"""Test file detection in intake."""

from config import Config
from file_processor import FileProcessor

def main():
    """Test file detection."""
    config = Config()
    processor = FileProcessor(config, interactive=True)
    
    print("🔍 Testing file detection in intake...")
    
    # Test finding candidate files
    candidate_files = processor._find_candidate_files()
    
    print(f"📁 Found {len(candidate_files)} candidate files:")
    for file_path, file_type in candidate_files.items():
        print(f"   {file_type}: {file_path}")

if __name__ == "__main__":
    main()
