#!/usr/bin/env python3
"""Main CLI interface for AI Job Candidate Reviewer."""

import json
import time
import os
import sys
from pathlib import Path
from typing import List, Optional

import click

from config import Config
from models import (
    JobSetupResult,
    ProcessingResult,
    DisplayResult,
    Evaluation,
    JobInsights,
    RecommendationType,
    CandidateFiles,
)
from open_api_test_connection import OpenAIConnectionTester
from ai_client import AIClient
from file_processor import FileProcessor
from output_generator import OutputGenerator
from feedback_manager import FeedbackManager


class CandidateReviewer:
    """Main application class for candidate review system."""

    def __init__(self, config: Config):
        """Initialize candidate reviewer.

        Args:
            config: Configuration object
        """
        self.config = config
        if config.openai_api_key:
            # Test connection and get best model
            connection_tester = OpenAIConnectionTester(
                config.openai_api_key, config.preferred_model
            )
            self.selected_model = connection_tester.model
            self.connection_tester = connection_tester
            # Only initialize AI client if we have an accessible model
            if self.selected_model:
                self.ai_client = AIClient(config.openai_api_key, self.selected_model)
            else:
                self.ai_client = None
        else:
            self.connection_tester = None
            self.ai_client = None
            self.selected_model = None
        self.file_processor = FileProcessor(config)
        self.output_generator = OutputGenerator(config)
        self.feedback_manager = (
            FeedbackManager(config, self.ai_client) if self.ai_client else None
        )

    def _print_model_info(self, operation: str) -> None:
        """Print current model information for an operation.

        Args:
            operation: Description of the operation being performed
        """
        if self.selected_model:
            print(f"🤖 Using AI Model: {self.selected_model} for {operation}")
        else:
            print(f"⚠️  No AI model available for {operation}")

    def _resolve_job_identifier(self, job_identifier: str) -> Optional[str]:
        """Resolve a job identifier that may be a numeric index to a job name.

        If the identifier is a digit, map it to the Nth job in the enumerated jobs list.
        Otherwise, return the identifier as-is.
        """
        if job_identifier and job_identifier.isdigit():
            jobs = self.list_jobs()
            if not jobs:
                print("❌ No jobs found. Use setup-job to create one.")
                return None
            index = int(job_identifier)
            if 1 <= index <= len(jobs):
                resolved = jobs[index - 1]
                print(f"🧩 Selected job #{index}: {resolved}")
                return resolved
            print(f"❌ Invalid job number: {job_identifier}")
            print("📋 Available jobs:")
            for i, name in enumerate(jobs, start=1):
                print(f"   {i}. {name}")
            return None
        return job_identifier

    def setup_job(self, job_name: str, allow_update: bool = False) -> JobSetupResult:
        """Initialize or update job with description files from intake.

        Args:
            job_name: Name of the job to setup

        Returns:
            JobSetupResult with success status and details
        """
        try:
            # Validate job name
            if not job_name or not job_name.strip():
                return JobSetupResult(
                    success=False,
                    job_name=job_name,
                    message="Job name cannot be empty",
                    errors=["Job name is required"],
                )

            job_name = job_name.strip().replace(" ", "_").lower()

            # Check if job already exists
            job_path = Path(self.config.get_job_path(job_name))
            if job_path.exists() and not allow_update:
                return JobSetupResult(
                    success=False,
                    job_name=job_name,
                    message=f"Job '{job_name}' already exists",
                    errors=[f"Job directory already exists: {job_path}"],
                )

            # Process job files from intake
            job_files, file_errors = self.file_processor.process_job_intake(job_name)

            if file_errors:
                return JobSetupResult(
                    success=False,
                    job_name=job_name,
                    message="Failed to process job files",
                    errors=file_errors,
                )

            # Organize files and create job context
            job_context, org_errors = self.file_processor.organize_job_files(job_files)

            if org_errors:
                return JobSetupResult(
                    success=False,
                    job_name=job_name,
                    message="Failed to organize job files",
                    errors=org_errors,
                )

            return JobSetupResult(
                success=True,
                job_name=job_name,
                message=(
                    f"Job '{job_name}' {'updated' if job_path.exists() else 'setup'} "
                    f"successfully"
                ),
                job_context=job_context,
            )

        except Exception as e:
            return JobSetupResult(
                success=False,
                job_name=job_name,
                message=f"Unexpected error during job setup: {str(e)}",
                errors=[str(e)],
            )

    def setup_job_with_paths(
        self,
        job_name: str,
        job_description_path: str = None,
        ideal_candidate_path: str = None,
        warning_flags_path: str = None,
        allow_update: bool = False,
    ) -> JobSetupResult:
        """Setup or update job using direct file paths instead of intake directory.

        Args:
            job_name: Name of the job
            job_description_path: Direct path to job description file
            ideal_candidate_path: Direct path to ideal candidate file (optional)
            warning_flags_path: Direct path to warning flags file (optional)

        Returns:
            JobSetupResult with success status and details
        """
        try:
            # Validate job name
            if not job_name or not job_name.strip():
                return JobSetupResult(
                    success=False,
                    job_name=job_name,
                    message="Job name cannot be empty",
                    errors=["Job name is required"],
                )

            job_name = job_name.strip().replace(" ", "_").lower()

            # Check if job already exists
            job_path = Path(self.config.get_job_path(job_name))
            if job_path.exists() and not allow_update:
                return JobSetupResult(
                    success=False,
                    job_name=job_name,
                    message=f"Job '{job_name}' already exists",
                    errors=[f"Job directory already exists: {job_path}"],
                )

            # Validate required job description
            if not job_description_path:
                return JobSetupResult(
                    success=False,
                    job_name=job_name,
                    message="Job description file is required",
                    errors=[
                        (
                            "Use -j /path/to/job_description.pdf or place "
                            "job_description.pdf in intake/"
                        )
                    ],
                )

            # Validate file exists and size
            if not Path(job_description_path).exists():
                return JobSetupResult(
                    success=False,
                    job_name=job_name,
                    message=f"Job description file not found: {job_description_path}",
                    errors=[f"File does not exist: {job_description_path}"],
                )

            # Create JobFiles object with direct paths
            from models import JobFiles

            job_files = JobFiles(
                job_name=job_name,
                job_description_path=job_description_path,
                ideal_candidate_path=ideal_candidate_path,
                warning_flags_path=warning_flags_path,
            )

            # Organize files and create job context
            job_context, org_errors = self.file_processor.organize_job_files(job_files)

            if org_errors:
                return JobSetupResult(
                    success=False,
                    job_name=job_name,
                    message="Failed to process job files",
                    errors=org_errors,
                )

            return JobSetupResult(
                success=True,
                job_name=job_name,
                message=(
                    f"Job '{job_name}' {'updated' if job_path.exists() else 'setup'} "
                    f"successfully from direct paths"
                ),
                job_context=job_context,
            )

        except Exception as e:
            return JobSetupResult(
                success=False,
                job_name=job_name,
                message=f"Unexpected error during job setup: {str(e)}",
                errors=[str(e)],
            )

    def process_single_candidate(
        self,
        job_name: str,
        candidate_name: str,
        resume_path: str,
        cover_letter_path: str = None,
        application_path: str = None,
    ) -> ProcessingResult:
        """Process a single candidate using direct file paths.

        Args:
            job_name: Name of the job
            candidate_name: Name of the candidate
            resume_path: Path to resume file
            cover_letter_path: Path to cover letter file (optional)
            application_path: Path to application file (optional)

        Returns:
            ProcessingResult with processing status
        """
        try:
            # Print model info and validate API client
            self._print_model_info("single candidate evaluation")

            if not self.ai_client:
                return ProcessingResult(
                    success=False,
                    job_name=job_name,
                    message="OpenAI API key not configured",
                    errors=["Please set OPENAI_API_KEY in your .env file"],
                )

            # Check if job exists
            job_path = Path(self.config.get_job_path(job_name))
            if not job_path.exists():
                return ProcessingResult(
                    success=False,
                    job_name=job_name,
                    message=f"Job '{job_name}' not found",
                    errors=[f"Run setup-job '{job_name}' first"],
                )

            # Load job context
            job_context = self._load_job_context(job_name)
            if not job_context:
                return ProcessingResult(
                    success=False,
                    job_name=job_name,
                    message="Could not load job context",
                    errors=["Job context file missing or corrupted"],
                )

            # Validate resume file exists
            if not Path(resume_path).exists():
                return ProcessingResult(
                    success=False,
                    job_name=job_name,
                    message=f"Resume file not found: {resume_path}",
                    errors=[f"File does not exist: {resume_path}"],
                )

            # Create CandidateFiles object
            from models import CandidateFiles

            candidate_files = CandidateFiles(
                candidate_name=candidate_name,
                resume_path=resume_path,
                cover_letter_path=cover_letter_path,
                application_path=application_path,
            )

            # Process the candidate
            candidate, cand_errors = self.file_processor.organize_candidate_files(
                candidate_files, job_name
            )

            if cand_errors:
                return ProcessingResult(
                    success=False,
                    job_name=job_name,
                    message="Failed to process candidate files",
                    errors=cand_errors,
                )

            # Evaluate candidate with AI
            evaluation = self.ai_client.evaluate_candidate(job_context, candidate)

            # Save evaluation
            candidate_dir = self.config.get_candidate_path(job_name, candidate.name)
            self.output_generator.save_evaluation_json(evaluation, candidate_dir)

            # Generate output files using ALL evaluations on disk
            output_path = self.config.get_output_path(job_name)
            all_evaluations = self.output_generator.load_evaluations_for_job(job_name)
            # Ensure the just-produced evaluation is included
            if evaluation not in all_evaluations:
                all_evaluations.append(evaluation)
            csv_path = self.output_generator.generate_csv(
                all_evaluations, output_path, job_name
            )
            self.output_generator.generate_html_report(
                job_context, all_evaluations, output_path
            )

            print(
                f"✅ Processed: {candidate.name} (Score: {evaluation.overall_score}/100)"
            )

            return ProcessingResult(
                success=True,
                job_name=job_name,
                processed_candidates=[candidate_name],
                failed_candidates=[],
                evaluations=[evaluation],
                errors=[],
                message=f"Processed 1 candidate. Results saved to {csv_path}",
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                job_name=job_name,
                message=f"Unexpected error during processing: {str(e)}",
                errors=[str(e)],
            )

    def process_candidates(self, job_name: str) -> ProcessingResult:
        """Process candidate files for a job.

        Args:
            job_name: Name of the job

        Returns:
            ProcessingResult with processing status and details
        """
        try:
            # Print model info and validate API client
            self._print_model_info("candidate evaluation")

            if not self.ai_client:
                return ProcessingResult(
                    success=False,
                    job_name=job_name,
                    message="OpenAI API key not configured",
                    errors=["Please set OPENAI_API_KEY in your .env file"],
                )

            # Check if job exists
            job_path = Path(self.config.get_job_path(job_name))
            if not job_path.exists():
                return ProcessingResult(
                    success=False,
                    job_name=job_name,
                    message=f"Job '{job_name}' not found",
                    errors=[f"Run --setup-job '{job_name}' first"],
                )

            # Load job context
            job_context = self._load_job_context(job_name)
            if not job_context:
                return ProcessingResult(
                    success=False,
                    job_name=job_name,
                    message="Could not load job context",
                    errors=["Job context file missing or corrupted"],
                )

            # Process candidate files from intake
            candidate_files_list, file_errors = (
                self.file_processor.process_candidate_intake(job_name)
            )

            if not candidate_files_list and not file_errors:
                return ProcessingResult(
                    success=False,
                    job_name=job_name,
                    message="No candidate files found in intake",
                    errors=[
                        (
                            "Place candidate files in intake directory with naming: "
                            "resume_firstname_lastname.pdf"
                        )
                    ],
                )

            processed_candidates = []
            failed_candidates = []
            evaluations = []
            all_errors = file_errors.copy()

            # Process each candidate
            for candidate_files in candidate_files_list:
                try:
                    # Organize candidate files
                    candidate, cand_errors = (
                        self.file_processor.organize_candidate_files(
                            candidate_files, job_name
                        )
                    )

                    if cand_errors:
                        all_errors.extend(cand_errors)
                        failed_candidates.append(candidate_files.candidate_name)
                        # Stop immediately so user can fix or remove candidate
                        return ProcessingResult(
                            success=False,
                            job_name=job_name,
                            processed_candidates=processed_candidates,
                            failed_candidates=failed_candidates,
                            evaluations=evaluations,
                            errors=all_errors,
                            message=(
                                f"Stopped at candidate '{candidate_files.candidate_name}' "
                                f"due to missing/invalid files. "
                                f"Fix the candidate files or remove the candidate, "
                                f"then retry."
                            ),
                        )

                    # Evaluate candidate with AI (retry on transient API errors)
                    max_retries = 3
                    backoff_seconds = 2
                    attempt = 0
                    evaluation = None
                    while attempt < max_retries:
                        evaluation = self.ai_client.evaluate_candidate(
                            job_context, candidate
                        )
                        # Detect retryable API error pattern
                        retryable = False
                        if evaluation and evaluation.overall_score == 0:
                            for c in evaluation.concerns or []:
                                msg = str(c).lower()
                                if (
                                    "api error" in msg
                                    or "connection error" in msg
                                    or "rate limit" in msg
                                ):
                                    retryable = True
                                    break
                        if not retryable:
                            break
                        attempt += 1
                        if attempt < max_retries:
                            wait = backoff_seconds**attempt
                            print(
                                f"⏳ Transient API error for {candidate.name}. "
                                f"Retrying in {wait}s "
                                f"(attempt {attempt}/{max_retries-1})..."
                            )
                            time.sleep(wait)

                    # If still failed due to API error, mark as failed and skip saving
                    if evaluation and evaluation.overall_score == 0:
                        has_api_issue = any(
                            "api error" in str(c).lower()
                            or "connection error" in str(c).lower()
                            for c in (evaluation.concerns or [])
                        )
                    else:
                        has_api_issue = False

                    if has_api_issue:
                        all_errors.append(
                            f"{candidate_files.candidate_name}: "
                            f"Transient API error - not processed. Please retry."
                        )
                        failed_candidates.append(candidate_files.candidate_name)
                        continue

                    # Save evaluation only on success
                    candidate_dir = self.config.get_candidate_path(
                        job_name, candidate.name
                    )
                    self.output_generator.save_evaluation_json(
                        evaluation, candidate_dir
                    )
                    evaluations.append(evaluation)
                    processed_candidates.append(candidate.name)
                    print(
                        f"✅ Processed: {candidate.name} "
                        f"(Score: {evaluation.overall_score}/100)"
                    )

                except Exception as e:
                    all_errors.append(f"{candidate_files.candidate_name}: {str(e)}")
                    failed_candidates.append(candidate_files.candidate_name)

            # Generate output files using ALL evaluations on disk if we processed any
            if evaluations:
                output_path = self.config.get_output_path(job_name)
                all_evaluations = self.output_generator.load_evaluations_for_job(
                    job_name
                )
                # Ensure current batch evaluations are included
                if all_evaluations:
                    existing_names = {e.candidate_name for e in all_evaluations}
                    for ev in evaluations:
                        if ev.candidate_name not in existing_names:
                            all_evaluations.append(ev)
                else:
                    all_evaluations = evaluations
                csv_path = self.output_generator.generate_csv(
                    all_evaluations, output_path, job_name
                )
                self.output_generator.generate_html_report(
                    job_context, all_evaluations, output_path
                )

                success_msg = (
                    f"Processed {len(processed_candidates)} candidates. "
                    f"Results saved to {csv_path}"
                )
            else:
                success_msg = "No candidates were successfully processed"

            return ProcessingResult(
                success=len(processed_candidates) > 0,
                job_name=job_name,
                processed_candidates=processed_candidates,
                failed_candidates=failed_candidates,
                evaluations=evaluations,
                errors=all_errors,
                message=success_msg,
            )

        except Exception as e:
            return ProcessingResult(
                success=False,
                job_name=job_name,
                message=f"Unexpected error during processing: {str(e)}",
                errors=[str(e)],
            )

    def show_candidates(self, job_name: str) -> DisplayResult:
        """Display ranked results for a job.

        Args:
            job_name: Name of the job

        Returns:
            DisplayResult with display status and details
        """
        try:
            # Check if job exists
            job_path = Path(self.config.get_job_path(job_name))
            if not job_path.exists():
                return DisplayResult(
                    success=False,
                    job_name=job_name,
                    message=f"Job '{job_name}' not found",
                )

            # Load evaluations
            evaluations = self.output_generator.load_evaluations_for_job(job_name)

            if not evaluations:
                return DisplayResult(
                    success=False,
                    job_name=job_name,
                    message=f"No evaluations found for job '{job_name}'",
                )

            # Display terminal ranking
            self.output_generator.display_terminal_ranking(evaluations, job_name)

            return DisplayResult(
                success=True,
                job_name=job_name,
                evaluations=evaluations,
                message=f"Displayed {len(evaluations)} candidate evaluations",
            )

        except Exception as e:
            return DisplayResult(
                success=False,
                job_name=job_name,
                message=f"Error displaying candidates: {str(e)}",
            )

    def list_jobs(self) -> List[str]:
        """List all available jobs.

        Returns:
            List of job names
        """
        jobs_path = Path(self.config.jobs_path)

        if not jobs_path.exists():
            return []

        jobs = []
        for job_dir in jobs_path.iterdir():
            if job_dir.is_dir():
                jobs.append(job_dir.name)

        return sorted(jobs)

    def test_connection(self) -> bool:
        """Test OpenAI API connection.

        Returns:
            True if connection successful, False otherwise
        """
        if not self.ai_client:
            print("❌ OpenAI API key not configured")
            print("Please set OPENAI_API_KEY in your .env file")
            return False

        print("🔄 Testing OpenAI API connection...")
        result = self.connection_tester.test_connection()

        if result.success:
            print(f"✅ {result.message}")
            if result.model_info:
                print(f"   {result.model_info}")
            if result.response_time_ms:
                print(f"   Response time: {result.response_time_ms:.0f}ms")
            return True
        else:
            print(f"❌ {result.message}")
            return False

    def list_available_models(self) -> None:
        """List available OpenAI models."""
        if not self.connection_tester:
            print("❌ OpenAI API key not configured")
            return

        print("🔄 Fetching available models...")
        models = self.connection_tester.get_available_models()

        if models:
            print(f"📋 Available GPT models ({len(models)}):")
            for model in sorted(models):
                current = " (CURRENT)" if model == self.selected_model else ""
                print(f"   • {model}{current}")
        else:
            print("❌ Could not fetch available models")

    def provide_feedback(
        self, job_name: str, candidate_name: str, feedback_text: Optional[str] = None
    ) -> None:
        """Provide feedback on a candidate evaluation."""
        if not self.feedback_manager:
            print("❌ Feedback system not available (API key required)")
            return

        # Check if candidate exists
        candidate_dir = Path(self.config.get_candidate_path(job_name, candidate_name))
        if not candidate_dir.exists():
            print(f"❌ Candidate {candidate_name} not found in job {job_name}")
            return

        # Load current evaluation
        eval_path = candidate_dir / "evaluation.json"
        if not eval_path.exists():
            print(f"❌ No evaluation found for {candidate_name}")
            return

        with open(eval_path, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
            evaluation = Evaluation.from_dict(eval_data)

        # Display current evaluation
        print(f"\n📋 Current AI Evaluation for {candidate_name}:")
        print(f"   Score: {evaluation.overall_score}/100")
        print(f"   Recommendation: {evaluation.recommendation.value}")
        print(f"   Priority: {evaluation.interview_priority.value}")
        print(
            f"   Strengths: {', '.join(evaluation.strengths[:2])}{'...' if len(evaluation.strengths) > 2 else ''}"
        )
        print(
            f"   Concerns: {', '.join(evaluation.concerns[:2])}{'...' if len(evaluation.concerns) > 2 else ''}"
        )

        # Handle non-interactive feedback if provided
        if feedback_text:
            print(f"\n🤔 Processing feedback: {feedback_text}")

            # Auto-determine recommendation based on feedback sentiment
            feedback_lower = feedback_text.lower()
            if any(
                word in feedback_lower
                for word in ["poor", "bad", "terrible", "awful", "reject", "no"]
            ):
                human_recommendation = RecommendationType.NO
                human_score = 40  # Low score for negative feedback
            elif any(
                word in feedback_lower
                for word in ["excellent", "great", "perfect", "hire", "strong"]
            ):
                human_recommendation = RecommendationType.YES
                human_score = 90  # High score for positive feedback
            else:
                human_recommendation = RecommendationType.MAYBE
                human_score = 65  # Medium score for neutral feedback

            feedback_notes = feedback_text
            corrections = {}

            # Auto-add corrections for common issues
            if "english" in feedback_lower or "grammar" in feedback_lower:
                corrections["concerns"] = (
                    f"{', '.join(evaluation.concerns)}, "
                    f"Poor written English with grammatical mistakes"
                )
                corrections["overall_score"] = str(human_score)

        else:
            # Interactive feedback collection
            print("\n🤔 Please provide your feedback:")

            # Get human recommendation
            print("\nWhat is your recommendation for this candidate?")
            print("1. STRONG_YES - Definitely hire")
            print("2. YES - Good candidate, should interview")
            print("3. MAYBE - Borderline, needs more evaluation")
            print("4. NO - Not a good fit")
            print("5. STRONG_NO - Definitely reject")

            while True:
                try:
                    choice = input("Enter choice (1-5): ").strip()
                    rec_map = {
                        "1": RecommendationType.STRONG_YES,
                        "2": RecommendationType.YES,
                        "3": RecommendationType.MAYBE,
                        "4": RecommendationType.NO,
                        "5": RecommendationType.STRONG_NO,
                    }
                    if choice in rec_map:
                        human_recommendation = rec_map[choice]
                        break
                    else:
                        print("Please enter 1, 2, 3, 4, or 5")
                except KeyboardInterrupt:
                    print("\n❌ Feedback cancelled")
                    return

            # Get human score (optional)
            human_score = None
            score_input = input(
                "\nOptional: Provide a score 0-100 (or press Enter to skip): "
            ).strip()
            if score_input:
                try:
                    human_score = max(0, min(100, int(score_input)))
                except ValueError:
                    print("Invalid score, skipping...")

            # Get feedback notes
            feedback_notes = input("\nPlease explain your reasoning: ").strip()
            if not feedback_notes:
                feedback_notes = "No additional notes provided"

            # Get specific corrections
            corrections = {}
            print(
                "\nAny specific corrections to the AI evaluation? (press Enter when done)"
            )
            print("Format: field_name: corrected_value")
            print("Example: overall_score: 65")
            print(
                "Available fields: overall_score, strengths, concerns, detailed_notes"
            )

            while True:
                correction = input("Correction (or Enter to finish): ").strip()
                if not correction:
                    break

                if ":" in correction:
                    field, value = correction.split(":", 1)
                    corrections[field.strip()] = value.strip()
                else:
                    print("Format: field_name: corrected_value")

        # Create feedback object
        from models import HumanFeedback

        feedback = HumanFeedback(
            evaluation_id=evaluation.evaluation_id,
            human_recommendation=human_recommendation,
            human_score=human_score,
            feedback_notes=feedback_notes,
            specific_corrections=corrections,
        )

        # Save feedback
        try:
            self.feedback_manager.collect_feedback(job_name, candidate_name, feedback)
            print("\n✅ Feedback saved successfully!")
        except Exception as e:
            print(f"\n❌ Error saving feedback: {e}")

    def show_insights(self, job_name: str) -> None:
        """Display current AI insights for a job."""
        if not self.feedback_manager:
            print("❌ Feedback system not available (API key required)")
            return

        job_dir = Path(self.config.get_job_path(job_name))
        insights_path = job_dir / "insights.json"

        if not insights_path.exists():
            print(f"📋 No insights available for job '{job_name}'")
            print(
                "Insights are generated after collecting feedback on candidate evaluations."
            )
            return

        try:
            with open(insights_path, "r", encoding="utf-8") as f:
                insights_data = json.load(f)
                insights = JobInsights.from_dict(insights_data)

            print(f"\n🧠 AI Insights for Job: {job_name}")
            print("=" * 60)
            print(f"Based on {insights.feedback_count} feedback records")
            print(
                f"Last updated: {insights.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            if insights.effectiveness_metrics:
                agreement_rate = insights.effectiveness_metrics.get("agreement_rate", 0)
                print(f"Agreement rate: {agreement_rate:.1%}")

            print("\n📝 Generated Insights:")

            def _print_value(value, indent_level: int = 2) -> None:
                indent = " " * indent_level
                if isinstance(value, dict):
                    for k, v in value.items():
                        print(f"{indent}- {k.replace('_', ' ').title()}:")
                        _print_value(v, indent_level + 2)
                elif isinstance(value, list):
                    if not value:
                        print(f"{indent}(none)")
                    for item in value:
                        if isinstance(item, (dict, list)):
                            print(f"{indent}-")
                            _print_value(item, indent_level + 2)
                        else:
                            print(f"{indent}- {item}")
                else:
                    # Print multi-line strings nicely
                    text = str(value)
                    lines = text.splitlines() or [text]
                    for line in lines:
                        print(f"{indent}{line}")

            try:
                insights_json = json.loads(insights.generated_insights)
                for key, value in insights_json.items():
                    print(f"\n• {key.replace('_', ' ').title()}:")
                    _print_value(value, 2)
            except json.JSONDecodeError:
                _print_value(insights.generated_insights, 2)

        except Exception as e:
            print(f"❌ Error loading insights: {e}")

    def re_evaluate_candidates(
        self, job_name: str, candidate_names: Optional[List[str]] = None
    ) -> None:
        """Re-evaluate candidates with updated insights."""
        if not self.feedback_manager:
            print("❌ Feedback system not available (API key required)")
            return

        # Print model info for re-evaluation
        self._print_model_info("candidate re-evaluation")

        try:
            self.feedback_manager.trigger_re_evaluation(job_name, candidate_names)

            # Show updated rankings after re-evaluation
            print("\n📊 Updated candidate rankings:")
            self.show_candidates(job_name)

        except Exception as e:
            print(f"❌ Error during re-evaluation: {e}")

    def open_reports(self, job_name: str) -> None:
        """Open the latest HTML report for a job."""
        output_path = Path(self.config.get_output_path(job_name))

        if not output_path.exists():
            print(f"❌ No reports found for job '{job_name}'")
            return

        # Always regenerate HTML from current evaluations before opening
        try:
            job_context = self._load_job_context(job_name)
            evaluations = self.output_generator.load_evaluations_for_job(job_name)
            if job_context and evaluations:
                latest_html_str = self.output_generator.generate_html_report(
                    job_context, evaluations, output_path
                )
                latest_html = Path(latest_html_str)
            else:
                latest_html = None
        except Exception as e:
            print(f"⚠️  Could not regenerate report: {e}")
            latest_html = None

        # Find the latest HTML report
        html_files = list(output_path.glob("detailed_report_*.html"))

        if not html_files and not latest_html:
            print(f"❌ No HTML reports found for job '{job_name}'")
            return

        # Prefer regenerated file; otherwise pick most recent existing file
        if latest_html is None:
            latest_html = max(html_files, key=lambda f: f.stat().st_mtime)

        print(f"📊 Opening HTML report: {latest_html}")

        # Try to open in browser (macOS)
        import subprocess

        try:
            subprocess.run(["open", str(latest_html)], check=True)
            print("✅ Report opened in browser")
        except subprocess.CalledProcessError:
            print(f"❌ Could not open browser. Manual path: {latest_html}")
        except FileNotFoundError:
            print(f"❌ 'open' command not found. Manual path: {latest_html}")

    def list_reports(self, job_name: str) -> None:
        """List all available reports for a job."""
        output_path = Path(self.config.get_output_path(job_name))

        if not output_path.exists():
            print(f"❌ No reports found for job '{job_name}'")
            return

        print("📊 Available reports for '{}':".format(job_name))

        # List CSV files
        csv_files = list(output_path.glob("candidate_scores_*.csv"))
        if csv_files:
            print("\n📈 CSV Reports:")
            for csv_file in sorted(
                csv_files, key=lambda f: f.stat().st_mtime, reverse=True
            ):
                mtime = csv_file.stat().st_mtime
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"   • {csv_file.name} ({date_str})")

        # List HTML files
        html_files = list(output_path.glob("detailed_report_*.html"))
        if html_files:
            print("\n🌐 HTML Reports:")
            for html_file in sorted(
                html_files, key=lambda f: f.stat().st_mtime, reverse=True
            ):
                mtime = html_file.stat().st_mtime
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"   • {html_file.name} ({date_str})")

        # Show feedback summary if exists
        feedback_file = output_path / "feedback_summary.json"
        if feedback_file.exists():
            print("\n💬 Feedback Summary:")
            print("   • feedback_summary.json")

        print(f"\n📂 Full path: {output_path}")

    def _load_job_context(self, job_name: str):
        """Load job context from job directory.

        Args:
            job_name: Name of the job

        Returns:
            JobContext object or None if not found
        """
        # This is a simplified version - in a full implementation,
        # we would save/load JobContext as JSON
        job_dir = Path(self.config.get_job_path(job_name))

        # For now, reconstruct from files
        desc_file = job_dir / "job_description.pdf"
        ideal_file = job_dir / "ideal_candidate.txt"
        warning_file = job_dir / "warning_flags.txt"

        if not desc_file.exists():
            return None

        # Extract text from files
        description, _ = self.file_processor.extract_text_from_file(str(desc_file))

        ideal_candidate = None
        if ideal_file.exists():
            ideal_candidate, _ = self.file_processor.extract_text_from_file(
                str(ideal_file)
            )

        warning_flags = None
        if warning_file.exists():
            warning_flags, _ = self.file_processor.extract_text_from_file(
                str(warning_file)
            )

        from models import JobContext

        return JobContext(
            name=job_name,
            description=description,
            ideal_candidate=ideal_candidate,
            warning_flags=warning_flags,
        )

    def _cleanup_intake_files(self, candidate_files: CandidateFiles) -> None:
        """Clean up intake files after successful processing.

        Args:
            candidate_files: CandidateFiles object with paths to clean up
        """
        try:
            files_to_remove = []

            if candidate_files.resume_path and candidate_files.resume_path.startswith(
                self.config.intake_path
            ):
                files_to_remove.append(candidate_files.resume_path)

            if (
                candidate_files.cover_letter_path
                and candidate_files.cover_letter_path.startswith(
                    self.config.intake_path
                )
            ):
                files_to_remove.append(candidate_files.cover_letter_path)

            if (
                candidate_files.application_path
                and candidate_files.application_path.startswith(self.config.intake_path)
            ):
                files_to_remove.append(candidate_files.application_path)

            for file_path in files_to_remove:
                try:
                    os.remove(file_path)
                    print(f"   🗑️  Cleaned up: {Path(file_path).name}")
                except OSError as e:
                    print(f"   ⚠️  Could not remove {Path(file_path).name}: {e}")

        except Exception as e:
            print(f"   ⚠️  Error during cleanup: {e}")

    def clean_intake(self) -> None:
        """Clean up processed files from intake directory."""
        intake_path = Path(self.config.intake_path)

        if not intake_path.exists():
            print("📁 Intake directory doesn't exist")
            return

        # Find candidate files that have been processed (not job setup files)
        candidate_files = []
        job_files = ["job_description.pdf", "ideal_candidate.txt", "warning_flags.txt"]

        for file_path in intake_path.iterdir():
            if file_path.is_file() and file_path.name not in job_files:
                # Check if it's a candidate file pattern
                if any(
                    file_path.name.startswith(prefix)
                    for prefix in ["resume_", "coverletter_", "application_"]
                ):
                    # Only include if candidate has been processed (exists in candidates directory)
                    candidate_name = self._extract_candidate_name_from_filename(
                        file_path.name
                    )
                    if candidate_name and self._candidate_exists_in_system(
                        candidate_name
                    ):
                        candidate_files.append(file_path)

        if not candidate_files:
            print("📁 No candidate files to clean up in intake")
            return

        print(f"🗑️  Found {len(candidate_files)} candidate files to clean up:")
        for file_path in candidate_files:
            print(f"   • {file_path.name}")

        # Ask for confirmation
        try:
            confirm = input("\nRemove these files? (y/N): ").strip().lower()
            if confirm in ["y", "yes"]:
                removed = 0
                for file_path in candidate_files:
                    try:
                        file_path.unlink()
                        removed += 1
                        print(f"   ✅ Removed: {file_path.name}")
                    except OSError as e:
                        print(f"   ❌ Could not remove {file_path.name}: {e}")

                print(f"\n🎉 Cleaned up {removed}/{len(candidate_files)} files")
            else:
                print("❌ Cleanup cancelled")
        except KeyboardInterrupt:
            print("\n❌ Cleanup cancelled")

    def reset_candidates(self, job_name: str) -> None:
        """Reset all candidates for a job while keeping job setup and insights.

        Args:
            job_name: Name of the job to reset candidates for
        """
        # Check if job exists
        job_path = Path(self.config.get_job_path(job_name))
        if not job_path.exists():
            print(f"❌ Job '{job_name}' not found")
            return

        candidates_path = Path(self.config.candidates_path) / job_name
        output_path = Path(self.config.output_path) / job_name

        items_to_remove = []

        # Find candidate directories
        if candidates_path.exists():
            for candidate_dir in candidates_path.iterdir():
                if candidate_dir.is_dir():
                    items_to_remove.append(("candidate", candidate_dir))

        # Find output files (but keep insights and feedback summary)
        if output_path.exists():
            for item in output_path.iterdir():
                if item.name not in ["feedback_summary.json"]:  # Keep feedback summary
                    items_to_remove.append(("output", item))

        if not items_to_remove:
            print(f"📁 No candidates to reset for job '{job_name}'")
            return

        print(f"🗑️  Found {len(items_to_remove)} items to remove for job '{job_name}':")
        print("\n📋 WILL KEEP (Job Setup & Learning):")
        print("   ✅ Job description, ideal candidate, warning flags")
        print("   ✅ AI insights from feedback (data/jobs/{}/insights.json)".format(job_name))
        print("   ✅ Feedback summary (data/output/{}/feedback_summary.json)".format(job_name))

        print("\n🗑️  WILL DELETE (Candidates & Reports):")
        for item_type, item_path in items_to_remove:
            if item_type == "candidate":
                print(f"   🧑 Candidate: {item_path.name}")
            else:
                print(f"   📊 Report: {item_path.name}")

        try:
            confirm = (
                input(f"\nReset candidates for job '{job_name}'? (y/N): ")
                .strip()
                .lower()
            )
            if confirm in ["y", "yes"]:
                removed = 0
                for item_type, item_path in items_to_remove:
                    try:
                        if item_path.is_dir():
                            import shutil

                            shutil.rmtree(item_path)
                        else:
                            item_path.unlink()
                        removed += 1
                        print(f"   ✅ Removed: {item_path.name}")
                    except OSError as e:
                        print(f"   ❌ Could not remove {item_path.name}: {e}")

                print(
                    f"\n🎉 Reset complete! Removed {removed}/{len(items_to_remove)} items"
                )
                print("✅ Job setup and AI insights preserved")
                print("✅ Ready for new candidates")
            else:
                print("❌ Reset cancelled")
        except KeyboardInterrupt:
            print("\n❌ Reset cancelled")


# CLI Interface
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """AI Job Candidate Reviewer - Automate resume screening with AI assistance."""
    # Show help if no command provided
    if ctx.invoked_subcommand is None:
        click.echo("🤖 AI Job Candidate Reviewer")
        click.echo("=" * 40)
        click.echo("Automate resume screening with AI assistance\n")

        click.echo("📋 Most Common Commands:")
        click.echo("  python3 candidate_reviewer.py test-connection")
        click.echo("  python3 candidate_reviewer.py setup-job 'job_name'")
        click.echo("  python3 candidate_reviewer.py process-candidates 'job_name'")
        click.echo("  python3 candidate_reviewer.py show-candidates 'job_name'")
        click.echo(
            "  python3 candidate_reviewer.py provide-feedback 'job_name' 'candidate_name' 'feedback'"
        )
        click.echo("  python3 candidate_reviewer.py re-evaluate 'job_name'")
        click.echo("\n🔧 Utility Commands:")
        click.echo(
            "  python3 candidate_reviewer.py clean-intake              # Clean up processed files"
        )
        click.echo(
            "  python3 candidate_reviewer.py open-reports 'job_name'   # Open HTML report"
        )
        click.echo(
            "  python3 candidate_reviewer.py list-jobs                 # Show all jobs"
        )
        click.echo("\n💡 Use --help to see all commands and options")
        return

    # Initialize configuration
    config = Config()

    # Validate configuration
    validation = config.validate_required_settings()

    if not validation.is_valid:
        click.echo("❌ Configuration errors:")
        for error in validation.errors:
            click.echo(f"   • {error}")
        sys.exit(1)

    if validation.warnings:
        click.echo("⚠️  Configuration warnings:")
        for warning in validation.warnings:
            click.echo(f"   • {warning}")
        click.echo()

    # Store config in context
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["reviewer"] = CandidateReviewer(config)


@cli.command()
@click.argument("job_name")
@click.option("--job-description", "-j", help="Path to job description file")
@click.option("--ideal-candidate", "-i", help="Path to ideal candidate file")
@click.option("--warning-flags", "-w", help="Path to warning flags file")
@click.option(
    "--update/--no-update", default=False, help="Update an existing job setup"
)
@click.pass_context
def setup_job(
    ctx,
    job_name: str,
    job_description: str = None,
    ideal_candidate: str = None,
    warning_flags: str = None,
    update: bool = False,
):
    """Initialize or update job with description files.

    Can use files from intake directory OR specify file paths directly:
    - From intake: setup-job "job_name" [--update]
    - Direct paths: setup-job "job_name" -j /path/to/job.pdf [--update]
    """
    reviewer = ctx.obj["reviewer"]

    # Allow numeric selection for existing job names when updating
    if (
        update
        and job_name
        and job_name.isdigit()
        and not (job_description or ideal_candidate or warning_flags)
    ):
        resolved = ctx.obj["reviewer"]._resolve_job_identifier(job_name)
        if not resolved:
            sys.exit(1)
        job_name = resolved

    click.echo(f"🔄 Setting up job: {job_name}")

    if job_description or ideal_candidate or warning_flags:
        # Use direct file paths
        result = reviewer.setup_job_with_paths(
            job_name,
            job_description,
            ideal_candidate,
            warning_flags,
            allow_update=update,
        )
    else:
        # Use intake directory
        result = reviewer.setup_job(job_name, allow_update=update)

    if result.success:
        click.echo(f"✅ {result.message}")
        if result.job_context:
            click.echo(
                f"   Job description loaded: {len(result.job_context.description)} characters"
            )
            if result.job_context.ideal_candidate:
                click.echo("   Ideal candidate profile: ✅")
            if result.job_context.warning_flags:
                click.echo("   Warning flags: ✅")
    else:
        click.echo(f"❌ {result.message}")
        for error in result.errors:
            click.echo(f"   • {error}")
        click.echo("\n💡 Usage:")
        click.echo("   From intake: setup-job 'job_name' [--update]")
        click.echo(
            "   Direct paths: setup-job 'job_name' -j /path/to/job.pdf [--update]"
        )
        sys.exit(1)


@cli.command()
@click.argument("job_name")
@click.option("--resume", "-r", help="Path to resume file")
@click.option("--cover-letter", "-c", help="Path to cover letter file")
@click.option("--application", "-a", help="Path to application/questionnaire file")
@click.option(
    "--candidate-name", "-n", help="Candidate name (if not using intake naming)"
)
@click.pass_context
def process_candidates(
    ctx,
    job_name: str,
    resume: str = None,
    cover_letter: str = None,
    application: str = None,
    candidate_name: str = None,
):
    """Process candidate files for evaluation.

    Can use files from intake directory OR specify file paths directly:
    - From intake: process-candidates "job_name"
    - Direct paths: process-candidates "job_name" -r /path/to/resume.pdf -n "John Doe"
    """
    reviewer = ctx.obj["reviewer"]

    # Resolve numeric job selection
    resolved = ctx.obj["reviewer"]._resolve_job_identifier(job_name)
    if not resolved:
        sys.exit(1)
    job_name = resolved

    click.echo(f"🔄 Processing candidates for job: {job_name}")
    ctx.obj["reviewer"]._print_model_info("candidate evaluation")

    if resume:
        # Process single candidate with direct paths
        if not candidate_name:
            click.echo("❌ --candidate-name required when using direct file paths")
            click.echo(
                "💡 Usage: process-candidates 'job_name' -r /path/to/resume.pdf -n 'John Doe'"
            )
            sys.exit(1)

        result = reviewer.process_single_candidate(
            job_name, candidate_name, resume, cover_letter, application
        )
    else:
        # Use intake directory
        result = reviewer.process_candidates(job_name)

    if result.success:
        click.echo(f"✅ {result.message}")
        if result.processed_candidates:
            click.echo(
                f"   Successfully processed: {', '.join(result.processed_candidates)}"
            )
        if result.failed_candidates:
            click.echo(f"   Failed to process: {', '.join(result.failed_candidates)}")
    else:
        click.echo(f"❌ {result.message}")
        for error in result.errors:
            click.echo(f"   • {error}")
        click.echo("\n💡 Usage:")
        click.echo("   From intake: process-candidates 'job_name'")
        click.echo(
            "   Direct paths: process-candidates 'job_name' -r /path/to/resume.pdf -n 'John Doe'"
        )
        sys.exit(1)


@cli.command()
@click.argument("job_name")
@click.pass_context
def show_candidates(ctx, job_name: str):
    """Display ranked candidate results."""
    reviewer = ctx.obj["reviewer"]
    resolved = reviewer._resolve_job_identifier(job_name)
    if not resolved:
        sys.exit(1)
    job_name = resolved
    print(f"📋 Job: {job_name}")
    reviewer._print_model_info("displaying candidates")
    result = reviewer.show_candidates(job_name)

    if not result.success:
        click.echo(f"❌ {result.message}")
        sys.exit(1)


@cli.command()
@click.pass_context
def list_jobs(ctx):
    """Show available jobs."""
    reviewer = ctx.obj["reviewer"]

    jobs = reviewer.list_jobs()

    if jobs:
        click.echo("📋 Available jobs:")
        click.echo("   (Use job number or full name in commands)\n")
        for i, job in enumerate(jobs, start=1):
            click.echo(f"   {i}. {job}")
        click.echo(f"\n💡 Example: process-candidates 1")
        click.echo(f"   Or:       process-candidates {jobs[0]}")
    else:
        click.echo("📋 No jobs found. Use setup-job to create one.")


@cli.command()
@click.pass_context
def test_connection(ctx):
    """Verify OpenAI API connectivity."""
    reviewer = ctx.obj["reviewer"]

    success = reviewer.test_connection()
    if not success:
        sys.exit(1)


@cli.command()
@click.pass_context
def list_models(ctx):
    """List available OpenAI models."""
    reviewer = ctx.obj["reviewer"]
    reviewer.list_available_models()


@cli.command(name="help-all")
@click.pass_context
def help_all(ctx):
    """Show detailed help (including options) for all commands."""
    # Show top-level help
    click.echo(cli.get_help(ctx))
    # Show each subcommand's help
    for name, command in cli.commands.items():
        click.echo("\n" + "=" * 80)
        click.echo(f"{name} - {command.help or ''}")
        # Build a context for the subcommand to format its help text
        with click.Context(command, info_name=name, parent=ctx) as subctx:
            click.echo(command.get_help(subctx))


@cli.command()
@click.argument("job_name")
@click.argument("candidate_name")
@click.argument("feedback_text", required=False)
@click.pass_context
def provide_feedback(
    ctx, job_name: str, candidate_name: str, feedback_text: str = None
):
    """Provide feedback on a candidate evaluation.

    Can be used interactively or with feedback text:
    - Interactive: provide-feedback job_name candidate_name
    - Non-interactive: provide-feedback job_name candidate_name "feedback text"
    """
    reviewer = ctx.obj["reviewer"]
    reviewer.provide_feedback(job_name, candidate_name, feedback_text)


@cli.command()
@click.argument("job_name")
@click.pass_context
def show_insights(ctx, job_name: str):
    """Display current AI insights for a job."""
    reviewer = ctx.obj["reviewer"]
    resolved = reviewer._resolve_job_identifier(job_name)
    if not resolved:
        sys.exit(1)
    job_name = resolved
    print(f"📋 Job: {job_name}")
    reviewer._print_model_info("showing insights")
    reviewer.show_insights(job_name)


@cli.command()
@click.argument("job_name")
@click.option(
    "--candidates", "-c", multiple=True, help="Specific candidates to re-evaluate"
)
@click.pass_context
def re_evaluate(ctx, job_name: str, candidates):
    """Re-evaluate candidates with updated insights."""
    reviewer = ctx.obj["reviewer"]
    resolved = reviewer._resolve_job_identifier(job_name)
    if not resolved:
        sys.exit(1)
    job_name = resolved
    print(f"📋 Job: {job_name}")
    reviewer._print_model_info("re-evaluation")
    candidate_list = list(candidates) if candidates else None
    reviewer.re_evaluate_candidates(job_name, candidate_list)


@cli.command()
@click.argument("job_name")
@click.pass_context
def open_reports(ctx, job_name: str):
    """Open the latest HTML report in browser."""
    reviewer = ctx.obj["reviewer"]
    resolved = reviewer._resolve_job_identifier(job_name)
    if not resolved:
        sys.exit(1)
    job_name = resolved
    print(f"📋 Job: {job_name}")
    reviewer.open_reports(job_name)


@cli.command()
@click.argument("job_name")
@click.pass_context
def list_reports(ctx, job_name: str):
    """List all available reports for a job."""
    reviewer = ctx.obj["reviewer"]
    resolved = reviewer._resolve_job_identifier(job_name)
    if not resolved:
        sys.exit(1)
    job_name = resolved
    print(f"📋 Job: {job_name}")
    reviewer.list_reports(job_name)


@cli.command()
@click.pass_context
def clean_intake(ctx):
    """Clean up processed candidate files from intake directory."""
    reviewer = ctx.obj["reviewer"]
    reviewer.clean_intake()


@cli.command()
@click.argument("job_name")
@click.pass_context
def reset_candidates(ctx, job_name: str):
    """Reset all candidates for a job while keeping job setup and AI insights."""
    reviewer = ctx.obj["reviewer"]
    reviewer.reset_candidates(job_name)


if __name__ == "__main__":
    cli()
