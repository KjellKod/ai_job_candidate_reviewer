#!/usr/bin/env python3
"""Test typo detection logic."""

import difflib
from pathlib import Path

def test_typo_detection():
    """Test the typo detection logic."""
    
    expected_prefixes = ['resume_', 'coverletter_', 'application_']
    test_files = [
        'resum_john_doe.pdf',
        'applicaton_john_doe.txt',
        'resume_jane_doe.pdf',  # Correct
        'resme_bob_smith.pdf',
        'coverletter_alice.pdf',  # Correct
        'coverlettr_charlie.pdf'
    ]
    
    for filename in test_files:
        print(f"\n📁 Testing: {filename}")
        
        # Find best matching prefix
        best_match = None
        best_ratio = 0.0
        
        for prefix in expected_prefixes:
            # Check similarity with the start of filename
            filename_start = filename[:len(prefix)].lower()
            ratio = difflib.SequenceMatcher(None, prefix.lower(), filename_start).ratio()
            
            print(f"   {prefix} vs {filename_start} = {ratio:.2f}")
            
            if ratio > best_ratio and ratio > 0.6:  # 60% similarity threshold
                best_match = prefix
                best_ratio = ratio
        
        if best_match:
            file_extension = Path(filename).suffix
            name_part = filename[len(filename.split('_')[0]) + 1:].replace(file_extension, '')
            suggested_name = f"{best_match}{name_part}{file_extension}"
            
            print(f"   ✅ Best match: {best_match} ({best_ratio:.1%})")
            print(f"   🔧 Suggested: {suggested_name}")
        else:
            print(f"   ❌ No good match found")

if __name__ == "__main__":
    test_typo_detection()
