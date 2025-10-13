"""File processing for AI Job Candidate Reviewer."""

import difflib
import json
import logging
import os
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pypdf

# Suppress pypdf warnings about PDF structural issues
logging.getLogger("pypdf").setLevel(logging.ERROR)

from config import Config
from models import Candidate, CandidateFiles, JobContext, JobFiles

# Regex patterns for extracting candidate identifiers
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[ .-]?)?(?:\(?\d{3}\)?|\d{3})[ .-]?\d{3}[ .-]?\d{4}\b"
)
LINKEDIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub|mwlite/in)/([A-Za-z0-9\-_%]+)",
    re.I,
)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9\-]+)", re.I)


def _normalize_profile_url(base: str, handle: str) -> str:
    """Normalize profile URL to a canonical form.

    Args:
        base: Base URL (e.g., 'https://linkedin.com/in')
        handle: User handle from the URL

    Returns:
        Normalized URL in lowercase
    """
    handle = urllib.parse.unquote(handle).strip().strip("/")
    return f"{base}/{handle}".lower()


class FileProcessor:
    """
    Handle file intake, organization, and text extraction.
    Think of this class as the intake clerk + document scanner + file librarian for the AI system.
    """

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
                            (
                                "Processing cancelled by user. "
                                "Please fix unrecognized files."
                            )
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
                (
                    "Expected naming: resume_firstname_lastname.pdf, "
                    "coverletter_firstname_lastname.pdf, "
                    "application_firstname_lastname.txt"
                )
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

        Uses identity-based deduplication to detect and merge duplicate candidates
        based on email, phone, LinkedIn, and GitHub identifiers.

        Args:
            candidate_files: CandidateFiles object with file paths
            job_name: Name of the job

        Returns:
            Tuple of (Candidate, list of error messages)
        """
        errors = []

        # Extract resume text (required) - but don't move file yet
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

        # Extract cover letter (optional) - but don't move file yet
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

        # Extract application (optional) - but don't move file yet
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

        # Extract identifiers from all available text
        combined_text = " ".join(
            t for t in [resume_text, cover_letter or "", application or ""] if t
        )
        identifiers = self._extract_identifiers_from_text(combined_text)

        # Check for existing candidates with overlapping identifiers
        existing_candidates = self._load_all_candidate_metadata(job_name)

        # Determine target directory based on identity matching
        target_dir_path, final_candidate_name = self._determine_target_directory(
            candidate_files.candidate_name, identifiers, existing_candidates, job_name
        )

        # Create target directory
        Path(target_dir_path).mkdir(parents=True, exist_ok=True)

        # Now move files to the determined target directory
        if not resume_error and candidate_files.resume_path:
            self._move_file_to_candidate_dir(
                candidate_files.resume_path, target_dir_path, "resume"
            )

        if cover_letter and candidate_files.cover_letter_path:
            self._move_file_to_candidate_dir(
                candidate_files.cover_letter_path, target_dir_path, "cover_letter"
            )

        if application and candidate_files.application_path:
            self._move_file_to_candidate_dir(
                candidate_files.application_path, target_dir_path, "application"
            )

        # Save candidate metadata for future deduplication
        self._save_candidate_metadata(target_dir_path, identifiers)

        candidate = Candidate(
            name=final_candidate_name,
            resume_text=resume_text,
            cover_letter=cover_letter,
            application=application,
            file_paths=candidate_files.get_file_paths(),
        )

        return candidate, errors

    def _extract_identifiers_from_text(self, text: str) -> Dict[str, set]:
        """Extract candidate identifiers from text.

        Args:
            text: Text to extract identifiers from (resume, cover letter, etc.)

        Returns:
            Dictionary with sets of emails, phones, linkedin, and github URLs
        """
        if not text:
            return {
                "emails": set(),
                "phones": set(),
                "linkedin": set(),
                "github": set(),
            }

        # Extract emails (lowercase for comparison)
        emails = set(m.group(0).lower() for m in EMAIL_RE.finditer(text))

        # Extract phones (digits only for comparison)
        phones = set(re.sub(r"\D", "", m.group(0)) for m in PHONE_RE.finditer(text))

        # Extract LinkedIn profiles (normalized URLs)
        linkedin = set()
        for match in LINKEDIN_RE.finditer(text):
            handle = match.group(1)
            # Skip if handle is empty or too generic
            if handle and len(handle) > 1:
                linkedin.add(_normalize_profile_url("https://linkedin.com/in", handle))

        # Extract GitHub profiles (normalized URLs)
        github = set()
        for match in GITHUB_RE.finditer(text):
            handle = match.group(1)
            # Skip if handle is empty or too generic
            if handle and len(handle) > 1:
                github.add(_normalize_profile_url("https://github.com", handle))

        return {
            "emails": emails,
            "phones": phones,
            "linkedin": linkedin,
            "github": github,
        }

    def _save_candidate_metadata(
        self, candidate_dir: str, identifiers: Dict[str, set]
    ) -> None:
        """Save candidate identifiers to metadata file.

        Args:
            candidate_dir: Path to candidate directory
            identifiers: Dictionary of identifier sets
        """
        meta_path = Path(candidate_dir) / "candidate_meta.json"
        # Convert sets to sorted lists for JSON serialization
        serializable = {k: sorted(list(v)) for k, v in identifiers.items()}
        meta_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")

    def _load_all_candidate_metadata(self, job_name: str) -> List[Dict]:
        """Load metadata for all existing candidates in a job.

        Args:
            job_name: Name of the job

        Returns:
            List of dictionaries with candidate name, dir, and identifier sets
        """
        job_candidates_dir = Path(self.config.candidates_path) / job_name
        records = []

        if not job_candidates_dir.exists():
            return records

        for cand_dir in job_candidates_dir.iterdir():
            if not cand_dir.is_dir():
                continue

            meta_path = cand_dir / "candidate_meta.json"
            if meta_path.exists():
                try:
                    data = json.loads(meta_path.read_text(encoding="utf-8"))
                    # Convert lists back to sets
                    record = {
                        "name": cand_dir.name,
                        "dir": str(cand_dir),
                        "emails": set(data.get("emails", [])),
                        "phones": set(data.get("phones", [])),
                        "linkedin": set(data.get("linkedin", [])),
                        "github": set(data.get("github", [])),
                    }
                    records.append(record)
                except (json.JSONDecodeError, OSError):
                    continue

        return records

    def _identifiers_overlap(self, a: Dict[str, set], b: Dict[str, set]) -> bool:
        """Check if two identifier sets have any overlap.

        Args:
            a: First identifier dictionary
            b: Second identifier dictionary

        Returns:
            True if any non-empty identifiers overlap, False otherwise
        """
        # Only count non-empty intersections; empty/empty does not match
        for key in ["emails", "phones", "linkedin", "github"]:
            a_set = a.get(key, set())
            b_set = b.get(key, set())
            if a_set and b_set and (a_set & b_set):
                return True
        return False

    def _has_any_identifiers(self, identifiers: Dict[str, set]) -> bool:
        """Check if identifier dictionary has at least one non-empty identifier.

        Args:
            identifiers: Dictionary of identifier sets

        Returns:
            True if any identifier set is non-empty
        """
        return any(
            identifiers.get(key) for key in ["emails", "phones", "linkedin", "github"]
        )

    def _determine_target_directory(
        self,
        candidate_name: str,
        identifiers: Dict[str, set],
        existing_candidates: List[Dict],
        job_name: str,
    ) -> Tuple[str, str]:
        """Determine the target directory for a candidate based on identity matching.

        Args:
            candidate_name: Name extracted from filename
            identifiers: Extracted identifiers for this candidate
            existing_candidates: List of existing candidate metadata
            job_name: Name of the job

        Returns:
            Tuple of (target_directory_path, final_candidate_name)
        """
        # Check for candidates with overlapping identifiers
        matching = [
            rec
            for rec in existing_candidates
            if self._identifiers_overlap(identifiers, rec)
        ]

        if matching:
            # Found at least one match with overlapping identifiers
            first_match = matching[0]

            if first_match["name"] != candidate_name:
                # Different name but same identifiers - potential fake/duplicate
                print(
                    f"\n⚠️  DUPLICATE IDENTIFIERS DETECTED: Candidate '{candidate_name}' shares "
                    f"identifiers with existing candidate '{first_match['name']}'"
                )

                # Show which identifiers overlap
                overlaps = []
                for key in ["emails", "phones", "linkedin", "github"]:
                    overlap = identifiers.get(key, set()) & first_match.get(key, set())
                    if overlap:
                        overlaps.append(f"{key}: {', '.join(sorted(overlap))}")
                overlap_text = (
                    "; ".join(overlaps) if overlaps else "(details unavailable)"
                )

                print("   Creating separate directory (marked for review)...")

                # Create a new directory with a duplicate check suffix
                base_name = candidate_name
                suffix = 2
                new_name = f"{base_name}__DUPLICATE_CHECK"
                new_path = self.config.get_candidate_path(job_name, new_name)
                # Ensure uniqueness in case of multiple
                while Path(new_path).exists():
                    new_name = f"{base_name}__DUPLICATE_CHECK_{suffix}"
                    new_path = self.config.get_candidate_path(job_name, new_name)
                    suffix += 1

                # Write duplicate warnings in BOTH directories for visibility
                try:
                    Path(new_path).mkdir(parents=True, exist_ok=True)
                except OSError:
                    pass
                self._write_duplicate_warning(
                    new_path,
                    first_match["name"],
                    overlap_text,
                )
                self._write_duplicate_warning(
                    first_match["dir"],
                    candidate_name,
                    overlap_text,
                )

                return new_path, new_name
            else:
                # Same name and overlapping identifiers - legitimate duplicate
                print(
                    f"\n🔁 Merging duplicate files for '{candidate_name}' "
                    f"(matching identifiers found)"
                )

            return first_match["dir"], first_match["name"]

        # No identifier overlap found - check if name collision exists
        same_name_candidates = [
            rec for rec in existing_candidates if rec["name"] == candidate_name
        ]

        if same_name_candidates:
            # Same name but no identifier overlap
            existing = same_name_candidates[0]
            has_new_ids = self._has_any_identifiers(identifiers)
            has_existing_ids = self._has_any_identifiers(existing)

            if has_new_ids and has_existing_ids:
                # Both have identifiers but they don't overlap - likely different people
                print(
                    f"\n⚠️  NAME COLLISION: Found existing candidate '{candidate_name}' "
                    f"with different identifiers"
                )
                print("   Creating new directory with suffix...")

                # Find next available suffix
                base_name = candidate_name
                suffix = 2
                while True:
                    new_name = f"{base_name}__{suffix}"
                    new_path = self.config.get_candidate_path(job_name, new_name)
                    if not Path(new_path).exists():
                        print(f"   New candidate directory: {new_name}")
                        return new_path, new_name
                    suffix += 1
            else:
                # At least one side has no identifiers - can't determine, use original
                print(
                    f"\n⚠️  NAME COLLISION: Candidate '{candidate_name}' already exists "
                    f"but insufficient identifiers to determine if duplicate"
                )
                print("   Using original directory (files may be merged)...")
                return existing["dir"], existing["name"]

        # No match found - use original name
        original_path = self.config.get_candidate_path(job_name, candidate_name)
        return original_path, candidate_name

    def _write_duplicate_warning(
        self, candidate_dir: str, other_name: str, overlap_text: str
    ) -> None:
        """Write a prominent duplicate warning file into a candidate directory.

        Args:
            candidate_dir: Path to candidate directory
            other_name: The other candidate name that shares identifiers
            overlap_text: Human-readable list of overlapping identifiers
        """
        try:
            warning_path = Path(candidate_dir) / "DUPLICATE_WARNING.txt"
            content = (
                "🚨 DUPLICATE IDENTIFIERS DETECTED\n"
                f"This profile shares identifiers with: {other_name}\n"
                f"Overlapping: {overlap_text}\n\n"
                "Action: Review both profiles carefully. These candidates were processed separately "
                "to avoid data loss, but may represent the same person or a fake/alias.\n"
            )
            warning_path.write_text(content, encoding="utf-8")
        except OSError:
            pass

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
            filename_start = filename.split("_")[
                0
            ].lower()  # Get first part before underscore
            prefix_base = prefix[:-1].lower()  # Remove underscore from prefix

            ratio = difflib.SequenceMatcher(None, prefix_base, filename_start).ratio()

            # print("   DEBUG: {} vs {} = {:.2f}".format(prefix_base, filename_start, ratio))  # Debug disabled

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

            print("\n🤔 Possible typo detected:")
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
        - If different uploads contain complementary files
          (e.g., resume + application), merge them

        Args:
            candidate_files: Dictionary mapping file paths to detected file type

        Returns:
            Dictionary mapping candidate_name -> { file_type: file_path }
        """
        candidates: Dict[str, Dict[str, Tuple[str, float]]] = {}
        duplicates_detected: Dict[str, set] = {}

        for file_path, file_type in candidate_files.items():
            candidate_name = self.extract_candidate_name_from_filename(file_path)
            if not candidate_name:
                continue

            candidate_name = self._normalize_candidate_name(candidate_name, file_path)
            norm_type = self._normalize_file_type(file_type)

            self._handle_duplicate_files(
                candidates, duplicates_detected, candidate_name, norm_type, file_path
            )

        return self._format_grouping_results(candidates, duplicates_detected)

    def extract_candidate_name_from_filename(self, file_path: str) -> Optional[str]:
        """Extract candidate name from filename using various naming patterns.

        This is a public API method that can be used by other components
        to extract candidate names from file paths or filenames.

        Args:
            file_path: Path to the candidate file or just the filename

        Returns:
            Extracted candidate name or None if extraction fails
        """
        filename = Path(file_path).name
        name_no_ext = filename.rsplit(".", 1)[0]
        parts = name_no_ext.split("_")

        if len(parts) < 2:
            return None

        type_aliases = self._get_file_type_aliases()

        # Try different naming patterns
        if parts[0].lower() in type_aliases:
            # Prefix style: resume_firstname_lastname.pdf
            return "_".join(parts[1:])
        elif parts[-1].lower() in type_aliases:
            # Suffix style: firstname_lastname_resume.pdf
            return "_".join(parts[:-1])
        else:
            # Check if any part is a type (handles middle positions)
            type_indices = [
                i for i, part in enumerate(parts) if part.lower() in type_aliases
            ]
            if type_indices:
                # Remove all type tokens and join the rest
                name_parts = [
                    part for i, part in enumerate(parts) if i not in type_indices
                ]
                return "_".join(name_parts) if name_parts else parts[0]
            else:
                # No type found - assume everything after first token is name
                return "_".join(parts[1:]) if len(parts) > 2 else parts[0]

    def _normalize_candidate_name(self, candidate_name: str, file_path: str) -> str:
        """Normalize and clean up candidate name.

        Args:
            candidate_name: Raw extracted candidate name
            file_path: Original file path for fallback

        Returns:
            Normalized candidate name
        """
        if not candidate_name:
            return Path(file_path).name.rsplit(".", 1)[0]

        # Remove trailing/leading underscores
        candidate_name = candidate_name.strip("_")

        # Handle cases where type suffix wasn't caught
        type_aliases = self._get_file_type_aliases()
        for alias in type_aliases:
            if candidate_name.lower().endswith(f"_{alias}"):
                candidate_name = candidate_name[: -len(f"_{alias}")]
                break

        # Ensure we have a valid name
        if not candidate_name or candidate_name.lower() in type_aliases:
            candidate_name = Path(file_path).name.rsplit(".", 1)[0]

        return candidate_name

    def _normalize_file_type(self, file_type: str) -> str:
        """Normalize file type aliases to standard names.

        Args:
            file_type: Raw file type

        Returns:
            Normalized file type
        """
        if file_type in ("cover", "coverletter", "cover_letter"):
            return "coverletter"
        elif file_type in ("application", "questionnaire"):
            return "application"
        else:
            return file_type

    def _handle_duplicate_files(
        self,
        candidates: Dict[str, Dict[str, Tuple[str, float]]],
        duplicates_detected: Dict[str, set],
        candidate_name: str,
        norm_type: str,
        file_path: str,
    ) -> None:
        """Handle duplicate files by keeping the newest version.

        Args:
            candidates: Main candidates dictionary
            duplicates_detected: Tracking dictionary for duplicates
            candidate_name: Name of the candidate
            norm_type: Normalized file type
            file_path: Path to the current file
        """
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

    def _format_grouping_results(
        self,
        candidates: Dict[str, Dict[str, Tuple[str, float]]],
        duplicates_detected: Dict[str, set],
    ) -> Dict[str, Dict[str, str]]:
        """Format the final results and report any duplicates found.

        Args:
            candidates: Dictionary with file paths and timestamps
            duplicates_detected: Dictionary tracking which types had duplicates

        Returns:
            Clean dictionary mapping candidate_name -> { file_type: file_path }
        """
        result: Dict[str, Dict[str, str]] = {}

        for candidate_name, types_map in candidates.items():
            result[candidate_name] = {t: p for t, (p, _) in types_map.items()}

            if duplicates_detected.get(candidate_name):
                merged_types = ", ".join(sorted(duplicates_detected[candidate_name]))
                print(
                    f"🔁 Merged duplicates for {candidate_name}: {merged_types} "
                    f"(kept newest by modified time)"
                )

        return result

    def _get_file_type_aliases(self) -> set:
        """Get the set of recognized file type aliases.

        Returns:
            Set of file type aliases
        """
        return {
            "resume",
            "coverletter",
            "cover",
            "cover_letter",
            "application",
            "questionnaire",
        }

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
