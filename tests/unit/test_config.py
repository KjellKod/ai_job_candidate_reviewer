"""Unit tests for configuration management."""

import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

from config import Config, ValidationResult


class TestConfig:
    """Test configuration management."""
    
    def test_default_paths(self):
        """Test default path configuration."""
        config = Config()
        
        assert config.base_data_path == "./data"
        assert config.intake_path == "./data/intake"
        assert config.jobs_path == "./data/jobs"
        assert config.candidates_path == "./data/candidates"
        assert config.output_path == "./data/output"
        assert config.max_file_size_mb == 2
        assert config.max_file_size_bytes == 2 * 1024 * 1024
    
    def test_env_file_loading(self):
        """Test loading configuration from .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OPENAI_API_KEY=test_key_123\n")
            f.write("MAX_FILE_SIZE_MB=5\n")
            f.write("BASE_DATA_PATH=/tmp/test_data\n")
            env_file = f.name
        
        try:
            # Clear environment variables to ensure clean test
            with patch.dict(os.environ, {}, clear=True):
                config = Config(env_file=env_file)
                
                assert config.openai_api_key == "test_key_123"
                assert config.max_file_size_mb == 5
                assert config.base_data_path == "/tmp/test_data"
        finally:
            os.unlink(env_file)
    
    def test_validation_missing_api_key(self):
        """Test validation with missing API key."""
        # Create config without API key
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("# No API key\n")
            env_file = f.name
        
        try:
            # Clear environment variables to ensure clean test
            with patch.dict(os.environ, {}, clear=True):
                config = Config(env_file=env_file)
                result = config.validate_required_settings()
                
                assert not result.is_valid
                assert any("OPENAI_API_KEY is required" in error for error in result.errors)
        finally:
            os.unlink(env_file)
    
    def test_validation_invalid_file_size(self):
        """Test validation with invalid file size."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OPENAI_API_KEY=sk-test123\n")
            f.write("MAX_FILE_SIZE_MB=0\n")
            env_file = f.name
        
        try:
            # Clear environment variables to ensure clean test
            with patch.dict(os.environ, {}, clear=True):
                config = Config(env_file=env_file)
                result = config.validate_required_settings()
                
                assert not result.is_valid
                assert any("MAX_FILE_SIZE_MB must be greater than 0" in error for error in result.errors)
        finally:
            os.unlink(env_file)
    
    def test_get_job_path(self):
        """Test job path generation."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            path = config.get_job_path("test_job")
            
            assert path == "./data/jobs/test_job"
    
    def test_get_candidate_path(self):
        """Test candidate path generation."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            path = config.get_candidate_path("test_job", "john_doe")
            
            assert path == "./data/candidates/test_job/john_doe"
    
    def test_get_output_path(self):
        """Test output path generation."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            path = config.get_output_path("test_job")
            
            assert path == "./data/output/test_job"
