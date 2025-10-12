"""File processing for AI Job Candidate Reviewer."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import difflib
import logging

import pypdf

# Suppress pypdf warnings about PDF structural issues
logging.getLogger("pypdf").setLevel(logging.ERROR)

from config import Config
from models import JobFiles, CandidateFiles, JobContext, Candidate


class FileProcessor:
    """Handle file intake, organization, and text extraction."""

    def __init__(self, config: Config, interactive: bool = True):
        """Initialize file processor.

        Args:
            config: Configuration object
            interactive: Whether to ask user for typo corrections
        """
        self.config = config
        self.interactive = interactive

    def process_job_intake(self, job_name: str) -> Tuple[JobFiles, List[str]]:
        """Process job setup files from intake directory.

        Args:
            job_name: Name of the job to setup

        Returns:
            Tuple of (JobFiles object, list of error messages)
        """
        errors = []
        job_files = JobFiles(job_name=job_name)

        # Look for job description file (required)
        job_desc_path = self._find_file_in_intake("job_description")
        if job_desc_path:
            size_ok, size_error = self._validate_file_size(job_desc_path)
            if size_ok:
                job_files.job_description_path = job_desc_path
            else:
                errors.append(f"Job description file: {size_error}")
        else:
            errors.append(
                "Job description file not found. Expected: job_description.pdf"
            )

        # Look for optional files
        ideal_candidate_path = self._find_file_in_intake("ideal_candidate")
        if ideal_candidate_path:
            size_ok, size_error = self._validate_file_size(ideal_candidate_path)
            if size_ok:
                job_files.ideal_candidate_path = ideal_candidate_path
            else:
                errors.append(f"Ideal candidate file: {size_error}")

        warning_flags_path = self._find_file_in_intake("warning_flags")
        if warning_flags_path:
            size_ok, size_error = self._validate_file_size(warning_flags_path)
            if size_ok:
                job_files.warning_flags_path = warning_flags_path
            else:
                errors.append(f"Warning flags file: {size_error}")

        return job_files, errors

    def process_candidate_intake(
        self, job_name: str
    ) -> Tuple[List[CandidateFiles], List[str]]:
        """Process candidate files from intake directory.

        Args:
            job_name: Name of the job

        Returns:
            Tuple of (list of CandidateFiles, list of error messages)
        """
        errors = []
        candidates = []

        # Check for unrecognized files before processing
        unrecognized = self._check_unrecognized_files()
        if unrecognized:
            print(f"\n⚠️  Found {len(unrecognized)} unrecognized file(s) in intake:")
            for filename, suggestion in unrecognized:
                if suggestion:
                    print(f"   • {filename}")
                    print(f"     → Suggestion: {suggestion}")
                else:
                    print(f"   • {filename} (cannot auto-suggest)")

            if self.interactive:
                try:
                    confirm = (
                        input("\nContinue processing recognized candidates? (y/N): ")
                        .strip()
                        .lower()
                    )
                    if confirm not in ["y", "yes"]:
                        errors.append(
                            "Processing cancelled by user. Please fix unrecognized files."
                        )
                        return candidates, errors
                except KeyboardInterrupt:
                    print("\n❌ Processing cancelled")
                    errors.append("Processing cancelled by user")
                    return candidates, errors
            else:
                # Non-interactive: warn but continue
                print("⚠️  Continuing in non-interactive mode...\n")

        # Find all candidate files in intake
        candidate_files = self._find_candidate_files()

        if not candidate_files:
            errors.append("No candidate files found in intake directory.")
            errors.append(
                "Expected naming: resume_firstname_lastname.pdf, coverletter_firstname_lastname.pdf, application_firstname_lastname.txt"
            )
            return candidates, errors

        # Group files by candidate name
        candidate_groups = self._group_files_by_candidate(candidate_files)

        for candidate_name, files in candidate_groups.items():
            candidate_file = CandidateFiles(candidate_name=candidate_name)

            # Validate file sizes and assign paths
            for file_type, file_path in files.items():
                size_ok, size_error = self._validate_file_size(file_path)
                if size_ok:
                    if file_type == "resume":
                        candidate_file.resume_path = file_path
                    elif file_type == "coverletter":
                        candidate_file.cover_letter_path = file_path
                    elif file_type == "application":
                        candidate_file.application_path = file_path
                else:
                    errors.append(f"{candidate_name} - {file_type}: {size_error}")

            # Ensure each candidate has at least a resume
            if candidate_file.resume_path:
                candidates.append(candidate_file)
            else:
                errors.append(f"{candidate_name}: No valid resume file found")

        return candidates, errors

    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, Optional[str]]:
        """Extract text from PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (extracted text, error message if any)
        """
        try:
            with open(file_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                text_content = []

                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())

                extracted_text = "\n".join(text_content).strip()

                if not extracted_text:
                    return "", "PDF appears to be empty or text could not be extracted"

                return extracted_text, None

        except Exception as e:
            return "", f"Error extracting text from PDF: {str(e)}"

    def extract_text_from_file(self, file_path: str) -> Tuple[str, Optional[str]]:
        """Extract text from various file types.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (extracted text, error message if any)
        """
        try:
            file_ext = Path(file_path).suffix.lower()

            if file_ext == ".pdf":
                return self.extract_text_from_pdf(file_path)
            elif file_ext in [".txt", ".md"]:
                with open(file_path, "r", encoding="utf-8") as file:
                    return file.read().strip(), None
            else:
                return "", f"Unsupported file type: {file_ext}"

        except Exception as e:
            return "", f"Error reading file: {str(e)}"

    def organize_job_files(self, job_files: JobFiles) -> Tuple[JobContext, List[str]]:
        """Organize job files and create JobContext.

        Args:
            job_files: JobFiles object with file paths

        Returns:
            Tuple of (JobContext, list of error messages)
        """
        errors = []

        # Create job directory
        job_dir = self.config.get_job_path(job_files.job_name)
        Path(job_dir).mkdir(parents=True, exist_ok=True)

        # Extract and organize job description (required)
        if not job_files.job_description_path:
            errors.append("Job description is required")
            return JobContext(name=job_files.job_name, description=""), errors

        description, desc_error = self.extract_text_from_file(
            job_files.job_description_path
        )
        if desc_error:
            errors.append(f"Job description: {desc_error}")
            description = ""
        else:
            # Move file to job directory
            self._move_file_to_job_dir(
                job_files.job_description_path, job_dir, "job_description"
            )

        # Extract ideal candidate (optional)
        ideal_candidate = None
        if job_files.ideal_candidate_path:
            ideal_text, ideal_error = self.extract_text_from_file(
                job_files.ideal_candidate_path
            )
            if ideal_error:
                errors.append(f"Ideal candidate: {ideal_error}")
            else:
                ideal_candidate = ideal_text
                self._move_file_to_job_dir(
                    job_files.ideal_candidate_path, job_dir, "ideal_candidate"
                )

        # Extract warning flags (optional)
        warning_flags = None
        if job_files.warning_flags_path:
            warning_text, warning_error = self.extract_text_from_file(
                job_files.warning_flags_path
            )
            if warning_error:
                errors.append(f"Warning flags: {warning_error}")
            else:
                warning_flags = warning_text
                self._move_file_to_job_dir(
                    job_files.warning_flags_path, job_dir, "warning_flags"
                )

        job_context = JobContext(
            name=job_files.job_name,
            description=description,
            ideal_candidate=ideal_candidate,
            warning_flags=warning_flags,
        )

        return job_context, errors

    def organize_candidate_files(
        self, candidate_files: CandidateFiles, job_name: str
    ) -> Tuple[Candidate, List[str]]:
        """Organize candidate files and create Candidate object.

        Args:
            candidate_files: CandidateFiles object with file paths
            job_name: Name of the job

        Returns:
            Tuple of (Candidate, list of error messages)
        """
        errors = []

        # Create candidate directory
        candidate_dir = self.config.get_candidate_path(
            job_name, candidate_files.candidate_name
        )
        Path(candidate_dir).mkdir(parents=True, exist_ok=True)

        # Extract resume text (required)
        if not candidate_files.resume_path:
            errors.append(f"{candidate_files.candidate_name}: Resume is required")
            return (
                Candidate(name=candidate_files.candidate_name, resume_text=""),
                errors,
            )

        resume_text, resume_error = self.extract_text_from_file(
            candidate_files.resume_path
        )
        if resume_error:
            errors.append(f"{candidate_files.candidate_name} resume: {resume_error}")
            resume_text = ""
        else:
            self._move_file_to_candidate_dir(
                candidate_files.resume_path, candidate_dir, "resume"
            )

        # Extract cover letter (optional)
        cover_letter = None
        if candidate_files.cover_letter_path:
            cover_text, cover_error = self.extract_text_from_file(
                candidate_files.cover_letter_path
            )
            if cover_error:
                errors.append(
                    f"{candidate_files.candidate_name} cover letter: {cover_error}"
                )
            else:
                cover_letter = cover_text
                self._move_file_to_candidate_dir(
                    candidate_files.cover_letter_path, candidate_dir, "cover_letter"
                )

        # Extract application (optional)
        application = None
        if candidate_files.application_path:
            app_text, app_error = self.extract_text_from_file(
                candidate_files.application_path
            )
            if app_error:
                errors.append(
                    f"{candidate_files.candidate_name} application: {app_error}"
                )
            else:
                application = app_text
                self._move_file_to_candidate_dir(
                    candidate_files.application_path, candidate_dir, "application"
                )

        candidate = Candidate(
            name=candidate_files.candidate_name,
            resume_text=resume_text,
            cover_letter=cover_letter,
            application=application,
            file_paths=candidate_files.get_file_paths(),
        )

        return candidate, errors

    def _find_file_in_intake(self, base_name: str) -> Optional[str]:
        """Find a file in intake directory by base name.

        Args:
            base_name: Base name of file (without extension)

        Returns:
            Full path to file if found, None otherwise
        """
        intake_path = Path(self.config.intake_path)

        # Look for common extensions
        for ext in [".pdf", ".txt", ".md"]:
            file_path = intake_path / f"{base_name}{ext}"
            if file_path.exists():
                return str(file_path)

        return None

    def _find_candidate_files(self) -> Dict[str, str]:
        """Find all candidate files in intake directory with typo correction.

        Returns:
            Dictionary mapping file paths to their types
        """
        intake_path = Path(self.config.intake_path)
        candidate_files = {}

        if not intake_path.exists():
            return candidate_files

        # Patterns for candidate files:
        #   - Prefix style: {type}_{firstname}_{lastname}.{ext}
        #   - Suffix style: {firstname}_{lastname}_{type}.{ext}
        prefix_patterns = [
            (r"^resume_(.+)\.(pdf|txt)$", "resume"),
            (r"^coverletter_(.+)\.(pdf|txt)$", "coverletter"),
            (r"^cover_(.+)\.(pdf|txt)$", "coverletter"),
            (r"^cover_letter_(.+)\.(pdf|txt)$", "coverletter"),
            (r"^application_(.+)\.(txt|md)$", "application"),
            (r"^questionnaire_(.+)\.(txt|md)$", "application"),
        ]
        suffix_patterns = [
            (r"^(.+)_resume\.(pdf|txt)$", "resume"),
            (r"^(.+)_coverletter\.(pdf|txt)$", "coverletter"),
            (r"^(.+)_cover\.(pdf|txt)$", "coverletter"),
            (r"^(.+)_cover_letter\.(pdf|txt)$", "coverletter"),
            (r"^(.+)_application\.(txt|md)$", "application"),
            (r"^(.+)_questionnaire\.(txt|md)$", "application"),
        ]

        # Expected prefixes for typo detection
        expected_prefixes = [
            "resume_",
            "coverletter_",
            "cover_",
            "cover_letter_",
            "application_",
            "questionnaire_",
        ]

        for file_path in intake_path.iterdir():
            if file_path.is_file():
                filename = file_path.name
                matched = False

                # Try exact pattern matching first (prefix)
                for pattern, file_type in prefix_patterns:
                    match = re.match(pattern, filename, re.IGNORECASE)
                    if match:
                        candidate_files[str(file_path)] = file_type
                        matched = True
                        break
                # Try suffix-style patterns
                if not matched:
                    for pattern, file_type in suffix_patterns:
                        match = re.match(pattern, filename, re.IGNORECASE)
                        if match:
                            candidate_files[str(file_path)] = file_type
                            matched = True
                            break

                # If no exact match, try typo correction
                if not matched:
                    corrected_path = self._try_typo_correction(
                        file_path, expected_prefixes
                    )
                    if corrected_path:
                        # Re-check with corrected filename
                        corrected_filename = Path(corrected_path).name
                        for pattern, file_type in prefix_patterns + suffix_patterns:
                            match = re.match(pattern, corrected_filename, re.IGNORECASE)
                            if match:
                                candidate_files[corrected_path] = file_type
                                break

        return candidate_files

    def _try_typo_correction(
        self, file_path: Path, expected_prefixes: List[str]
    ) -> Optional[str]:
        """Try to correct typos in filename and ask user for confirmation.

        Args:
            file_path: Path to file with potential typo
            expected_prefixes: List of expected prefixes

        Returns:
            Corrected file path if user confirms, None otherwise
        """
        filename = file_path.name

        # Skip job setup files
        job_files = ["job_description.pdf", "ideal_candidate.txt", "warning_flags.txt"]
        if filename in job_files:
            return None

        # Skip files that don't look like candidate files
        filename_lower = filename.lower()
        if not any(
            word in filename_lower
            for word in [
                "resum",
                "cover",
                "coverletter",
                "cover_letter",
                "application",
                "questionnaire",
                "cv",
                "applicat",
            ]
        ):
            # print(f"   DEBUG: Skipping {filename} - doesn't look like candidate file")
            return None

        # print(f"   DEBUG: Processing potential candidate file: {filename}")  # Debug disabled

        # Find best matching prefix
        best_match = None
        best_ratio = 0.0

        for prefix in expected_prefixes:
            # Check similarity with the start of filename
            prefix_len = len(prefix) - 1  # Remove the underscore for comparison
            filename_start = filename.split("_")[
                0
            ].lower()  # Get first part before underscore
            prefix_base = prefix[:-1].lower()  # Remove underscore from prefix

            ratio = difflib.SequenceMatcher(None, prefix_base, filename_start).ratio()

            # print(f"   DEBUG: {prefix_base} vs {filename_start} = {ratio:.2f}")  # Debug disabled

            if ratio > best_ratio and ratio > 0.6:  # 60% similarity threshold
                best_match = prefix
                best_ratio = ratio

        if best_match:
            # Suggest correction
            file_extension = file_path.suffix
            name_part = filename[len(filename.split("_")[0]) + 1 :].replace(
                file_extension, ""
            )
            suggested_name = f"{best_match}{name_part}{file_extension}"

            print(f"\n🤔 Possible typo detected:")
            print(f"   Found: {filename}")
            print(f"   Suggested: {suggested_name}")
            print(f"   Confidence: {best_ratio:.1%}")

            if self.interactive:
                try:
                    confirm = input("   Rename file? (y/N): ").strip().lower()
                    if confirm in ["y", "yes"]:
                        return self._rename_file(file_path, suggested_name)
                    else:
                        print(f"   ❌ Keeping original filename: {filename}")
                        return None
                except KeyboardInterrupt:
                    print(f"\n   ❌ Skipping: {filename}")
                    return None
            else:
                # Non-interactive mode - auto-correct high confidence typos
                if best_ratio > 0.8:  # 80% confidence for auto-correction
                    print(f"   🔧 Auto-correcting: {filename} → {suggested_name}")
                    return self._rename_file(file_path, suggested_name)
                else:
                    print(f"   ⚠️  Possible typo (low confidence): {filename}")
                    return None

        return None

    def _rename_file(self, file_path: Path, suggested_name: str) -> Optional[str]:
        """Rename a file with error handling.

        Args:
            file_path: Original file path
            suggested_name: Suggested new filename

        Returns:
            New file path if successful, None otherwise
        """
        try:
            new_path = file_path.parent / suggested_name

            # Check if target already exists
            if new_path.exists():
                print(f"   ❌ Target file already exists: {suggested_name}")
                return None

            # Rename the file
            file_path.rename(new_path)
            print(f"   ✅ Renamed: {file_path.name} → {suggested_name}")
            return str(new_path)

        except OSError as e:
            print(f"   ❌ Could not rename file: {e}")
            return None

    def _group_files_by_candidate(
        self, candidate_files: Dict[str, str]
    ) -> Dict[str, Dict[str, str]]:
        """Group candidate files by candidate name and merge duplicates.

        - Supports prefix and suffix styles for filenames
        - If multiple files of the same type exist, select the NEWEST by mtime
        - If different uploads contain complementary files (e.g., resume + application), merge them

        Args:
            candidate_files: Dictionary mapping file paths to detected file type

        Returns:
            Dictionary mapping candidate_name -> { file_type: file_path }
        """
        candidates: Dict[str, Dict[str, Tuple[str, float]]] = {}
        duplicates_detected: Dict[str, set] = {}

        for file_path, file_type in candidate_files.items():
            filename = Path(file_path).name
            name_no_ext = filename.rsplit(".", 1)[0]
            parts = name_no_ext.split("_")
            if len(parts) < 2:
                continue

            type_aliases = {
                "resume",
                "coverletter",
                "cover",
                "cover_letter",
                "application",
                "questionnaire",
            }
            if parts[0].lower() in type_aliases:
                # Prefix style: drop type token
                candidate_name = "_".join(parts[1:])
            elif parts[-1].lower() in type_aliases:
                # Suffix style: drop trailing type token
                candidate_name = "_".join(parts[:-1])
            else:
                # Fallback: assume everything after the first token is the name
                candidate_name = "_".join(parts[1:]) if len(parts) > 2 else parts[0]

            # Normalize file_type aliases
            if file_type in ("cover", "coverletter", "cover_letter"):
                norm_type = "coverletter"
            elif file_type in ("application", "questionnaire"):
                norm_type = "application"
            else:
                norm_type = file_type

            if candidate_name not in candidates:
                candidates[candidate_name] = {}
                duplicates_detected[candidate_name] = set()

            mtime = os.path.getmtime(file_path)
            if norm_type not in candidates[candidate_name]:
                candidates[candidate_name][norm_type] = (file_path, mtime)
            else:
                # Duplicate type - keep newest
                existing_path, existing_mtime = candidates[candidate_name][norm_type]
                if mtime >= existing_mtime:
                    candidates[candidate_name][norm_type] = (file_path, mtime)
                # Record that we merged this type
                duplicates_detected[candidate_name].add(norm_type)

        # Convert to simple mapping and print merge notices
        result: Dict[str, Dict[str, str]] = {}
        for candidate_name, types_map in candidates.items():
            result[candidate_name] = {t: p for t, (p, _) in types_map.items()}
            if duplicates_detected.get(candidate_name):
                merged_types = ", ".join(sorted(duplicates_detected[candidate_name]))
                print(
                    f"🔁 Merged duplicates for {candidate_name}: {merged_types} (kept newest by modified time)"
                )

        return result

    def _validate_file_size(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate file size against configured limits.

        Args:
            file_path: Path to file to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            file_size = os.path.getsize(file_path)

            if file_size > self.config.max_file_size_bytes:
                size_mb = file_size / (1024 * 1024)
                return (
                    False,
                    f"File size ({size_mb:.1f}MB) exceeds limit of {self.config.max_file_size_mb}MB",
                )

            return True, None

        except OSError as e:
            return False, f"Cannot access file: {str(e)}"

    def _move_file_to_job_dir(
        self, source_path: str, job_dir: str, base_name: str
    ) -> None:
        """Move file to job directory with standardized name.

        Args:
            source_path: Source file path
            job_dir: Job directory path
            base_name: Base name for the moved file
        """
        source_ext = Path(source_path).suffix
        dest_path = Path(job_dir) / f"{base_name}{source_ext}"

        import shutil

        shutil.move(source_path, dest_path)

    def _move_file_to_candidate_dir(
        self, source_path: str, candidate_dir: str, base_name: str
    ) -> None:
        """Move file to candidate directory with standardized name.

        Args:
            source_path: Source file path
            candidate_dir: Candidate directory path
            base_name: Base name for the moved file
        """
        source_ext = Path(source_path).suffix
        dest_path = Path(candidate_dir) / f"{base_name}{source_ext}"

        import shutil

        shutil.move(source_path, dest_path)

    def _check_unrecognized_files(self) -> List[Tuple[str, Optional[str]]]:
        """Check for unrecognized files in intake directory.

        Returns:
            List of tuples (filename, suggested_name)
        """
        intake_path = Path(self.config.intake_path)
        if not intake_path.exists():
            return []

        unrecognized = []
        job_files = {"job_description.pdf", "ideal_candidate.txt", "warning_flags.txt"}

        # Get list of recognized candidate files
        recognized_files = set(self._find_candidate_files().keys())

        for file_path in intake_path.iterdir():
            if not file_path.is_file():
                continue

            filename = file_path.name

            # Skip job setup files
            if filename in job_files:
                continue

            # Skip already recognized files
            if str(file_path) in recognized_files:
                continue

            # This is an unrecognized file - try to suggest a fix
            suggestion = None
            filename_lower = filename.lower()

            # Check if it looks like a candidate file
            if any(
                word in filename_lower
                for word in ["resum", "cv", "cover", "application", "questionnaire"]
            ):
                # Try to suggest a proper name
                name_base = filename.rsplit(".", 1)[0] if "." in filename else filename
                ext = Path(filename).suffix

                # Clean up the name (remove spaces, standardize)
                clean_name = name_base.replace(" ", "_").strip()

                # Suggest based on content hints
                if "resum" in filename_lower or "cv" in filename_lower:
                    suggestion = f"{clean_name}_resume{ext}"
                elif "cover" in filename_lower:
                    suggestion = f"{clean_name}_cover{ext}"
                elif (
                    "application" in filename_lower or "questionnaire" in filename_lower
                ):
                    suggestion = f"{clean_name}_application{ext}"

            unrecognized.append((filename, suggestion))

        return unrecognized
