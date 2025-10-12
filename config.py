"""Configuration management for AI Job Candidate Reviewer."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


class Config:
    """Configuration manager for the AI Job Candidate Reviewer system."""

    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration.

        Args:
            env_file: Optional path to .env file. If None, looks for .env in
                current directory.
        """
        self.env_file = env_file or ".env"
        self.load_env()
        self._setup_paths()

    def load_env(self) -> None:
        """Load environment variables from .env file."""
        if os.path.exists(self.env_file):
            load_dotenv(self.env_file)

    def _setup_paths(self) -> None:
        """Setup and create necessary directory paths."""
        # Create base directories if they don't exist
        for path in [
            self.intake_path,
            self.jobs_path,
            self.candidates_path,
            self.output_path,
        ]:
            Path(path).mkdir(parents=True, exist_ok=True)

    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key from environment."""
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def base_data_path(self) -> str:
        """Get base data directory path."""
        return os.getenv("BASE_DATA_PATH", "./data")

    @property
    def intake_path(self) -> str:
        """Get intake directory path."""
        return os.getenv("INTAKE_PATH", f"{self.base_data_path}/intake")

    @property
    def jobs_path(self) -> str:
        """Get jobs directory path."""
        return os.getenv("JOBS_PATH", f"{self.base_data_path}/jobs")

    @property
    def candidates_path(self) -> str:
        """Get candidates directory path."""
        return os.getenv("CANDIDATES_PATH", f"{self.base_data_path}/candidates")

    @property
    def output_path(self) -> str:
        """Get output directory path."""
        return os.getenv("OUTPUT_PATH", f"{self.base_data_path}/output")

    @property
    def max_file_size_mb(self) -> int:
        """Get maximum file size limit in MB."""
        return int(os.getenv("MAX_FILE_SIZE_MB", "2"))

    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size limit in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def preferred_model(self) -> Optional[str]:
        """Get preferred OpenAI model."""
        return os.getenv("OPENAI_MODEL")

    def validate_required_settings(self) -> ValidationResult:
        """Validate that all required configuration is present and valid.

        Returns:
            ValidationResult with validation status and any errors/warnings.
        """
        errors = []
        warnings = []

        # Check required settings
        if not self.openai_api_key:
            errors.append(
                "OPENAI_API_KEY is required. Please add it to your .env file."
            )
        elif not self.openai_api_key.startswith(("sk-", "sk-proj-")):
            warnings.append(
                (
                    "OPENAI_API_KEY format looks unusual. Expected to start with "
                    "'sk-' or 'sk-proj-'."
                )
            )

        # Validate file size limit
        if self.max_file_size_mb <= 0:
            errors.append("MAX_FILE_SIZE_MB must be greater than 0.")
        elif self.max_file_size_mb > 10:
            warnings.append(
                (
                    f"MAX_FILE_SIZE_MB is set to {self.max_file_size_mb}MB. "
                    f"Large files may cause memory issues."
                )
            )

        # Check if paths are writable
        for path_name, path_value in [
            ("intake_path", self.intake_path),
            ("jobs_path", self.jobs_path),
            ("candidates_path", self.candidates_path),
            ("output_path", self.output_path),
        ]:
            try:
                Path(path_value).mkdir(parents=True, exist_ok=True)
                # Test write access
                test_file = Path(path_value) / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
            except (OSError, PermissionError) as e:
                errors.append(f"Cannot write to {path_name} ({path_value}): {e}")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    def get_job_path(self, job_name: str) -> str:
        """Get the directory path for a specific job.

        Args:
            job_name: Name of the job

        Returns:
            Path to the job directory
        """
        return f"{self.jobs_path}/{job_name}"

    def get_candidate_path(self, job_name: str, candidate_name: str) -> str:
        """Get the directory path for a specific candidate.

        Args:
            job_name: Name of the job
            candidate_name: Name of the candidate

        Returns:
            Path to the candidate directory
        """
        return f"{self.candidates_path}/{job_name}/{candidate_name}"

    def get_output_path(self, job_name: str) -> str:
        """Get the output directory path for a specific job.

        Args:
            job_name: Name of the job

        Returns:
            Path to the job output directory
        """
        return f"{self.output_path}/{job_name}"

    def candidate_exists(self, job_name: str, candidate_name: str) -> bool:
        """Check if a candidate has been processed and exists in the system.

        Args:
            job_name: Name of the job
            candidate_name: Name of the candidate to check

        Returns:
            True if candidate directory exists and contains files, False otherwise
        """
        from pathlib import Path

        candidate_path = Path(self.get_candidate_path(job_name, candidate_name))
        
        if not candidate_path.exists() or not candidate_path.is_dir():
            return False
        
        # Check if directory contains any files
        try:
            return any(candidate_path.iterdir())
        except (OSError, PermissionError):
            return False

    def get_candidates_for_job(self, job_name: str) -> list:
        """Get list of all candidate names for a job.

        Args:
            job_name: Name of the job

        Returns:
            List of candidate names (directory names) for the job.
            Returns empty list if job has no candidates or doesn't exist.
        """
        from pathlib import Path

        candidates_path = Path(self.candidates_path) / job_name
        
        if not candidates_path.exists():
            return []
        
        try:
            return [
                candidate_dir.name
                for candidate_dir in candidates_path.iterdir()
                if candidate_dir.is_dir()
            ]
        except (OSError, PermissionError):
            return []

    def __str__(self) -> str:
        """String representation of configuration (without sensitive data)."""
        return f"""Config:
  Base Data Path: {self.base_data_path}
  Intake Path: {self.intake_path}
  Jobs Path: {self.jobs_path}
  Candidates Path: {self.candidates_path}
  Output Path: {self.output_path}
  Max File Size: {self.max_file_size_mb}MB
  API Key: {'Set' if self.openai_api_key else 'Not Set'}"""
