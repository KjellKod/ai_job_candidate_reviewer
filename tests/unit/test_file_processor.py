"""Unit tests for file processor."""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch
import pytest

from file_processor import FileProcessor
from config import Config
from models import JobFiles, CandidateFiles


class TestFileProcessor:
    """Test file processing functionality."""

    def test_initialization(self):
        """Test file processor initialization."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

            assert processor.config == config

    def test_file_size_validation_valid(self):
        """Test file size validation with valid file."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        # Create a small test file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_file = f.name

        try:
            is_valid, error = processor._validate_file_size(temp_file)

            assert is_valid is True
            assert error is None
        finally:
            os.unlink(temp_file)

    def test_file_size_validation_too_large(self):
        """Test file size validation with oversized file."""
        # Create a temporary .env file with small limit
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".env", delete=False
        ) as env_file:
            env_file.write("MAX_FILE_SIZE_MB=1\n")
            env_file_path = env_file.name

        try:
            with patch.dict(os.environ, {}, clear=True):
                config = Config(env_file=env_file_path)

                # Verify config loaded correctly
                assert config.max_file_size_mb == 1

                processor = FileProcessor(config)

                # Create a file larger than 1MB
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    f.write(b"x" * (2 * 1024 * 1024))  # 2MB file
                    temp_file = f.name

                try:
                    is_valid, error = processor._validate_file_size(temp_file)

                    assert is_valid is False
                    assert "exceeds limit" in error
                    assert "2.0MB" in error
                finally:
                    os.unlink(temp_file)
        finally:
            os.unlink(env_file_path)

    def test_candidate_file_grouping(self):
        """Test grouping candidate files by name."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        # Create temporary files to test with
        temp_files = []
        candidate_files = {}

        try:
            # Create actual temporary files with proper naming
            test_files = [
                ("resume_john_doe.pdf", "resume"),
                ("coverletter_john_doe.pdf", "coverletter"),
                ("application_john_doe.txt", "application"),
                ("resume_jane_smith.pdf", "resume"),
                ("application_jane_smith.txt", "application"),
            ]

            for filename, file_type in test_files:
                # Create temp file with the desired name structure
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, prefix="", suffix=f"_{filename}"
                )
                temp_files.append(temp_file.name)

                # Rename to have the proper structure for the test
                proper_name = temp_file.name.replace(
                    temp_file.name.split("/")[-1], filename
                )
                os.rename(temp_file.name, proper_name)
                temp_files[-1] = proper_name  # Update the list with new name
                candidate_files[proper_name] = file_type

            grouped = processor._group_files_by_candidate(candidate_files)

            # Should have exactly 2 candidates
            assert len(grouped) == 2

            # Check that we have the expected candidates (names will be extracted from filenames)
            candidate_names = list(grouped.keys())

            # Find john_doe and jane_smith equivalents
            john_candidate = None
            jane_candidate = None

            for name in candidate_names:
                files = grouped[name]
                if len(files) == 3:  # john_doe should have 3 files
                    john_candidate = name
                elif len(files) == 2:  # jane_smith should have 2 files
                    jane_candidate = name

            assert (
                john_candidate is not None
            ), f"Should find candidate with 3 files, got: {grouped}"
            assert (
                jane_candidate is not None
            ), f"Should find candidate with 2 files, got: {grouped}"

            # Verify john_doe equivalent has all file types
            john_files = grouped[john_candidate]
            assert "resume" in john_files
            assert "coverletter" in john_files
            assert "application" in john_files

            # Verify jane_smith equivalent has only resume and application
            jane_files = grouped[jane_candidate]
            assert "resume" in jane_files
            assert "application" in jane_files
            assert "coverletter" not in jane_files

        finally:
            # Clean up temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass

    def test_pdf_text_extraction_empty_file(self):
        """Test PDF text extraction with empty file."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        # Create empty PDF (this will fail, which is expected)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_file = f.name

        try:
            text, error = processor.extract_text_from_pdf(temp_file)

            # Should return empty text and an error
            assert text == ""
            assert error is not None
            assert "Error extracting text" in error
        finally:
            os.unlink(temp_file)

    def test_text_file_extraction(self):
        """Test text file extraction."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        # Create a text file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("Test content\nLine 2\nLine 3")
            temp_file = f.name

        try:
            text, error = processor.extract_text_from_file(temp_file)

            assert error is None
            assert "Test content" in text
            assert "Line 2" in text
            assert "Line 3" in text
        finally:
            os.unlink(temp_file)

    def test_unsupported_file_type(self):
        """Test handling of unsupported file types."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            processor = FileProcessor(config)

        # Create a file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_file = f.name

        try:
            text, error = processor.extract_text_from_file(temp_file)

            assert text == ""
            assert error is not None
            assert "Unsupported file type" in error
        finally:
            os.unlink(temp_file)
