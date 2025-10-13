"""Unit tests for identity-based candidate deduplication."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from config import Config
from file_processor import FileProcessor


class TestIdentifierExtraction:
    """Test extraction of candidate identifiers from text."""

    def test_extract_email(self):
        """Test email extraction."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        text = "Contact me at john.doe@example.com or jane_smith@test.org"
        identifiers = processor._extract_identifiers_from_text(text)

        assert "john.doe@example.com" in identifiers["emails"]
        assert "jane_smith@test.org" in identifiers["emails"]
        assert len(identifiers["emails"]) == 2

    def test_extract_phone(self):
        """Test phone number extraction."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        text = "Call me at (555) 123-4567 or +1 555-987-6543"
        identifiers = processor._extract_identifiers_from_text(text)

        # Phones are normalized to digits only
        assert "5551234567" in identifiers["phones"]
        assert "15559876543" in identifiers["phones"]

    def test_extract_linkedin_profile(self):
        """Test LinkedIn profile extraction."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        text = """
        LinkedIn: linkedin.com/in/john-doe-123
        Or find me at linkedin.com/in/jane_smith
        """
        identifiers = processor._extract_identifiers_from_text(text)

        assert "https://linkedin.com/in/john-doe-123" in identifiers["linkedin"]
        assert "https://linkedin.com/in/jane_smith" in identifiers["linkedin"]

    def test_extract_github_profile(self):
        """Test GitHub profile extraction."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        text = """
        GitHub: https://github.com/johndoe
        Check out github.com/janesmith
        """
        identifiers = processor._extract_identifiers_from_text(text)

        assert "https://github.com/johndoe" in identifiers["github"]
        assert "https://github.com/janesmith" in identifiers["github"]

    def test_extract_mixed_identifiers(self):
        """Test extraction of multiple identifier types."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        text = """
        John Doe
        Email: john.doe@example.com
        Phone: (555) 123-4567
        LinkedIn: linkedin.com/in/johndoe
        GitHub: github.com/johndoe
        """
        identifiers = processor._extract_identifiers_from_text(text)

        assert len(identifiers["emails"]) == 1
        assert len(identifiers["phones"]) == 1
        assert len(identifiers["linkedin"]) == 1
        assert len(identifiers["github"]) == 1

    def test_empty_text(self):
        """Test extraction from empty text."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        identifiers = processor._extract_identifiers_from_text("")

        assert len(identifiers["emails"]) == 0
        assert len(identifiers["phones"]) == 0
        assert len(identifiers["linkedin"]) == 0
        assert len(identifiers["github"]) == 0

    def test_no_identifiers(self):
        """Test extraction from text without identifiers."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        text = "Just some random text without any contact information"
        identifiers = processor._extract_identifiers_from_text(text)

        assert len(identifiers["emails"]) == 0
        assert len(identifiers["phones"]) == 0
        assert len(identifiers["linkedin"]) == 0
        assert len(identifiers["github"]) == 0


class TestIdentifierOverlap:
    """Test identifier overlap detection."""

    def test_email_overlap(self):
        """Test detection of overlapping emails."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        a = {
            "emails": {"john@example.com", "jane@example.com"},
            "phones": set(),
            "linkedin": set(),
            "github": set(),
        }
        b = {
            "emails": {"john@example.com"},
            "phones": set(),
            "linkedin": set(),
            "github": set(),
        }

        assert processor._identifiers_overlap(a, b)

    def test_phone_overlap(self):
        """Test detection of overlapping phones."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        a = {
            "emails": set(),
            "phones": {"5551234567"},
            "linkedin": set(),
            "github": set(),
        }
        b = {
            "emails": set(),
            "phones": {"5551234567", "5559876543"},
            "linkedin": set(),
            "github": set(),
        }

        assert processor._identifiers_overlap(a, b)

    def test_no_overlap(self):
        """Test detection when there is no overlap."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        a = {
            "emails": {"john@example.com"},
            "phones": {"5551234567"},
            "linkedin": set(),
            "github": set(),
        }
        b = {
            "emails": {"jane@example.com"},
            "phones": {"5559876543"},
            "linkedin": set(),
            "github": set(),
        }

        assert not processor._identifiers_overlap(a, b)

    def test_empty_sets_no_match(self):
        """Test that empty identifier sets don't match."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        a = {"emails": set(), "phones": set(), "linkedin": set(), "github": set()}
        b = {"emails": set(), "phones": set(), "linkedin": set(), "github": set()}

        assert not processor._identifiers_overlap(a, b)

    def test_mixed_identifier_overlap(self):
        """Test overlap with multiple identifier types."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        a = {
            "emails": {"john@example.com"},
            "phones": set(),
            "linkedin": {"https://linkedin.com/in/johndoe"},
            "github": set(),
        }
        b = {
            "emails": {"jane@example.com"},
            "phones": set(),
            "linkedin": {"https://linkedin.com/in/johndoe"},
            "github": set(),
        }

        assert processor._identifiers_overlap(a, b)


class TestMetadataPersistence:
    """Test saving and loading candidate metadata."""

    def test_save_and_load_metadata(self):
        """Test saving and loading candidate metadata."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_dir = Path(tmpdir) / "john_doe"
            candidate_dir.mkdir()

            identifiers = {
                "emails": {"john@example.com"},
                "phones": {"5551234567"},
                "linkedin": {"https://linkedin.com/in/johndoe"},
                "github": {"https://github.com/johndoe"},
            }

            # Save metadata
            processor._save_candidate_metadata(str(candidate_dir), identifiers)

            # Verify file exists
            meta_path = candidate_dir / "candidate_meta.json"
            assert meta_path.exists()

            # Load and verify
            data = json.loads(meta_path.read_text())
            assert "john@example.com" in data["emails"]
            assert "5551234567" in data["phones"]
            assert "https://linkedin.com/in/johndoe" in data["linkedin"]
            assert "https://github.com/johndoe" in data["github"]

    def test_load_all_candidate_metadata(self):
        """Test loading metadata for all candidates in a job."""
        with tempfile.TemporaryDirectory() as tmpdir:
            candidates_dir = Path(tmpdir) / "candidates"
            candidates_dir.mkdir()

            with patch.dict(
                os.environ, {"CANDIDATES_PATH": str(candidates_dir)}, clear=True
            ):
                config = Config()
                processor = FileProcessor(config)

                job_dir = candidates_dir / "test_job"
                job_dir.mkdir()

                # Create two candidate directories with metadata
                for name, email in [
                    ("john_doe", "john@example.com"),
                    ("jane_smith", "jane@example.com"),
                ]:
                    cand_dir = job_dir / name
                    cand_dir.mkdir()

                    identifiers = {
                        "emails": {email},
                        "phones": set(),
                        "linkedin": set(),
                        "github": set(),
                    }
                    processor._save_candidate_metadata(str(cand_dir), identifiers)

                # Load all metadata (inside context manager so config is valid)
                records = processor._load_all_candidate_metadata("test_job")

                assert len(records) == 2
                names = {rec["name"] for rec in records}
                assert "john_doe" in names
                assert "jane_smith" in names

                # Verify email content
                john_record = next(rec for rec in records if rec["name"] == "john_doe")
                assert "john@example.com" in john_record["emails"]


class TestHasAnyIdentifiers:
    """Test checking if identifiers exist."""

    def test_has_email(self):
        """Test detection when email exists."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        identifiers = {
            "emails": {"john@example.com"},
            "phones": set(),
            "linkedin": set(),
            "github": set(),
        }

        assert processor._has_any_identifiers(identifiers)

    def test_has_multiple(self):
        """Test detection when multiple identifiers exist."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        identifiers = {
            "emails": {"john@example.com"},
            "phones": {"5551234567"},
            "linkedin": set(),
            "github": set(),
        }

        assert processor._has_any_identifiers(identifiers)

    def test_no_identifiers(self):
        """Test detection when no identifiers exist."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        identifiers = {
            "emails": set(),
            "phones": set(),
            "linkedin": set(),
            "github": set(),
        }

        assert not processor._has_any_identifiers(identifiers)
