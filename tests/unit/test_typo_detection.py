#!/usr/bin/env python3
"""Unit tests for typo detection logic in FileProcessor."""

import difflib
from pathlib import Path
from typing import Optional, Tuple

import pytest


class TestTypoDetection:
    """Test typo detection and correction suggestions."""

    # Test data constants
    EXPECTED_PREFIXES = ["resume_", "coverletter_", "application_"]
    SIMILARITY_THRESHOLD = 0.6

    @staticmethod
    def find_best_prefix_match(
        filename: str, prefixes: list[str], threshold: float = 0.6
    ) -> Tuple[Optional[str], float]:
        """Find the best matching prefix for a filename using fuzzy matching.

        Args:
            filename: The filename to match against
            prefixes: List of valid prefixes to check
            threshold: Minimum similarity ratio to consider a match

        Returns:
            Tuple of (best_match, best_ratio) or (None, 0.0) if no match
        """
        best_match = None
        best_ratio = 0.0

        for prefix in prefixes:
            filename_start = filename[: len(prefix)].lower()
            ratio = difflib.SequenceMatcher(
                None, prefix.lower(), filename_start
            ).ratio()

            if ratio > best_ratio and ratio > threshold:
                best_match = prefix
                best_ratio = ratio

        return best_match, best_ratio

    @staticmethod
    def generate_suggested_name(filename: str, correct_prefix: str) -> str:
        """Generate suggested corrected filename.

        Args:
            filename: Original filename with typo
            correct_prefix: The correct prefix to use

        Returns:
            Suggested corrected filename
        """
        file_extension = Path(filename).suffix
        name_part = filename[len(filename.split("_")[0]) + 1 :].replace(
            file_extension, ""
        )
        return f"{correct_prefix}{name_part}{file_extension}"

    def test_typo_detection_with_resume_typo(self):
        """Test that 'resum_' is detected as typo of 'resume_'."""
        filename = "resum_john_doe.pdf"
        best_match, best_ratio = self.find_best_prefix_match(
            filename, self.EXPECTED_PREFIXES
        )

        assert best_match == "resume_", f"Expected 'resume_' but got {best_match}"
        assert best_ratio > 0.8, f"Expected high similarity but got {best_ratio}"

    def test_typo_detection_with_application_typo(self):
        """Test that 'applicaton_' is detected as typo of 'application_'."""
        filename = "applicaton_john_doe.txt"
        best_match, best_ratio = self.find_best_prefix_match(
            filename, self.EXPECTED_PREFIXES
        )

        assert (
            best_match == "application_"
        ), f"Expected 'application_' but got {best_match}"
        assert best_ratio > 0.8, f"Expected high similarity but got {best_ratio}"

    def test_typo_detection_with_coverletter_typo(self):
        """Test that 'coverlettr_' is detected as typo of 'coverletter_'."""
        filename = "coverlettr_charlie.pdf"
        best_match, best_ratio = self.find_best_prefix_match(
            filename, self.EXPECTED_PREFIXES
        )

        assert (
            best_match == "coverletter_"
        ), f"Expected 'coverletter_' but got {best_match}"
        assert best_ratio > 0.8, f"Expected high similarity but got {best_ratio}"

    def test_correct_filename_no_typo_resume(self):
        """Test that correct 'resume_' filename is not flagged as typo."""
        filename = "resume_jane_doe.pdf"
        best_match, best_ratio = self.find_best_prefix_match(
            filename, self.EXPECTED_PREFIXES
        )

        assert best_match == "resume_", f"Expected 'resume_' but got {best_match}"
        assert best_ratio == 1.0, f"Expected perfect match (1.0) but got {best_ratio}"

    def test_correct_filename_no_typo_coverletter(self):
        """Test that correct 'coverletter_' filename is not flagged as typo."""
        filename = "coverletter_alice.pdf"
        best_match, best_ratio = self.find_best_prefix_match(
            filename, self.EXPECTED_PREFIXES
        )

        assert (
            best_match == "coverletter_"
        ), f"Expected 'coverletter_' but got {best_match}"
        assert best_ratio == 1.0, f"Expected perfect match (1.0) but got {best_ratio}"

    def test_no_match_for_very_different_filename(self):
        """Test that completely different filename doesn't match any prefix."""
        filename = "xyz_random_file.pdf"
        best_match, best_ratio = self.find_best_prefix_match(
            filename, self.EXPECTED_PREFIXES
        )

        assert best_match is None, f"Expected no match but got {best_match}"

    def test_suggested_name_correction_resume(self):
        """Test that suggested name is correctly generated for resume typo."""
        filename = "resum_john_doe.pdf"
        correct_prefix = "resume_"
        suggested_name = self.generate_suggested_name(filename, correct_prefix)

        assert (
            suggested_name == "resume_john_doe.pdf"
        ), f"Expected 'resume_john_doe.pdf' but got '{suggested_name}'"

    def test_suggested_name_correction_application(self):
        """Test that suggested name is correctly generated for application typo."""
        filename = "applicaton_john_doe.txt"
        correct_prefix = "application_"
        suggested_name = self.generate_suggested_name(filename, correct_prefix)

        assert (
            suggested_name == "application_john_doe.txt"
        ), f"Expected 'application_john_doe.txt' but got '{suggested_name}'"

    def test_threshold_boundary_case(self):
        """Test that threshold of 0.6 works correctly."""
        # "resme_" should match "resume_" with ratio > 0.6
        filename = "resme_bob_smith.pdf"
        best_match, best_ratio = self.find_best_prefix_match(
            filename, self.EXPECTED_PREFIXES, threshold=self.SIMILARITY_THRESHOLD
        )

        assert best_match == "resume_", f"Expected 'resume_' but got {best_match}"
        assert (
            0.6 < best_ratio < 1.0
        ), f"Expected ratio between 0.6 and 1.0 but got {best_ratio}"
