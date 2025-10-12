"""Feedback management for AI Job Candidate Reviewer."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ai_client import AIClient
from config import Config
from models import Evaluation, FeedbackRecord, HumanFeedback, JobInsights


class FeedbackManager:
    """Manage human feedback and AI learning system."""

    def __init__(self, config: Config, ai_client: AIClient):
        """Initialize feedback manager.

        Args:
            config: Configuration object
            ai_client: AI client for generating insights
        """
        self.config = config
        self.ai_client = ai_client

    def collect_feedback(
        self, job_name: str, candidate_name: str, feedback: HumanFeedback
    ) -> None:
        """Collect human feedback on an AI evaluation.

        Args:
            job_name: Name of the job
            candidate_name: Name of the candidate
            feedback: Human feedback object
        """
        # Load the original evaluation
        candidate_dir = self.config.get_candidate_path(job_name, candidate_name)
        eval_path = Path(candidate_dir) / "evaluation.json"

        if not eval_path.exists():
            raise ValueError(
                f"No evaluation found for {candidate_name} in job {job_name}"
            )

        with open(eval_path, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
            original_evaluation = Evaluation.from_dict(eval_data)

        # Create feedback record
        feedback_record = FeedbackRecord(
            candidate_name=candidate_name,
            job_name=job_name,
            original_evaluation=original_evaluation,
            human_feedback=feedback,
        )

        # Save feedback to candidate directory
        feedback_path = Path(candidate_dir) / "feedback.json"
        with open(feedback_path, "w", encoding="utf-8") as f:
            json.dump(feedback_record.to_dict(), f, indent=2, ensure_ascii=False)

        # Update job-level feedback summary
        self._update_job_feedback_summary(job_name, feedback_record)

        print(f"✅ Feedback collected for {candidate_name}")
        print(f"   Human recommendation: {feedback.human_recommendation.value}")
        print(f"   AI recommendation: {original_evaluation.recommendation.value}")

        # Generate new insights if we have enough feedback
        self._maybe_generate_insights(job_name)

    def build_insights(self, job_name: str) -> Optional[JobInsights]:
        """Build job-specific insights from feedback patterns.

        Args:
            job_name: Name of the job

        Returns:
            JobInsights object or None if insufficient feedback
        """
        feedback_records = self.get_feedback_history(job_name)

        if len(feedback_records) < 2:
            print(
                f"⚠️  Need at least 2 feedback records to generate insights "
                f"(have {len(feedback_records)})"
            )
            return None

        # Load job context
        job_context = self._load_job_context(job_name)
        if not job_context:
            print(f"❌ Could not load job context for {job_name}")
            return None

        # Prepare feedback patterns for AI analysis
        feedback_patterns = []
        for record in feedback_records:
            pattern = {
                "candidate_name": record.candidate_name,
                "ai_evaluation": {
                    "score": record.original_evaluation.overall_score,
                    "recommendation": record.original_evaluation.recommendation.value,
                    "strengths": record.original_evaluation.strengths,
                    "concerns": record.original_evaluation.concerns,
                    "detailed_notes": record.original_evaluation.detailed_notes,
                },
                "human_feedback": {
                    "recommendation": record.human_feedback.human_recommendation.value,
                    "score": record.human_feedback.human_score,
                    "feedback_notes": record.human_feedback.feedback_notes,
                    "corrections": record.human_feedback.specific_corrections,
                },
            }
            feedback_patterns.append(pattern)

        # Generate insights using AI
        print(f"🤖 Using AI Model: {self.ai_client.model} for insights generation")
        insights_json = self.ai_client.generate_insights(job_context, feedback_patterns)

        try:
            insights_data = json.loads(insights_json)
            insights_text = json.dumps(insights_data, indent=2)
        except json.JSONDecodeError:
            insights_text = insights_json

        # Create JobInsights object
        job_insights = JobInsights(
            job_name=job_name,
            generated_insights=insights_text,
            feedback_count=len(feedback_records),
            effectiveness_metrics=self._calculate_effectiveness_metrics(
                feedback_records
            ),
        )

        # Save insights to job directory
        job_dir = self.config.get_job_path(job_name)
        insights_path = Path(job_dir) / "insights.json"

        with open(insights_path, "w", encoding="utf-8") as f:
            json.dump(job_insights.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"✅ Generated new insights for {job_name}")
        print(f"   Based on {len(feedback_records)} feedback records")

        return job_insights

    def get_feedback_history(self, job_name: str) -> List[FeedbackRecord]:
        """Get all feedback records for a job.

        Args:
            job_name: Name of the job

        Returns:
            List of feedback records
        """
        feedback_records = []
        candidates_path = Path(self.config.candidates_path) / job_name

        if not candidates_path.exists():
            return feedback_records

        for candidate_dir in candidates_path.iterdir():
            if candidate_dir.is_dir():
                feedback_path = candidate_dir / "feedback.json"
                if feedback_path.exists():
                    try:
                        with open(feedback_path, "r", encoding="utf-8") as f:
                            feedback_data = json.load(f)
                            record = FeedbackRecord.from_dict(feedback_data)
                            feedback_records.append(record)
                    except (json.JSONDecodeError, KeyError) as e:
                        print(
                            f"Warning: Could not load feedback for "
                            f"{candidate_dir.name}: {e}"
                        )

        return feedback_records

    def trigger_re_evaluation(
        self, job_name: str, candidate_names: Optional[List[str]] = None
    ) -> None:
        """Re-evaluate candidates with updated insights.

        Args:
            job_name: Name of the job
            candidate_names: Optional list of specific candidates to re-evaluate
        """
        # Load job insights
        job_insights = self._load_job_insights(job_name)
        if not job_insights:
            print(f"⚠️  No insights available for {job_name}. Generate insights first.")
            return

        # Load job context
        job_context = self._load_job_context(job_name)
        if not job_context:
            print(f"❌ Could not load job context for {job_name}")
            return

        candidates_path = Path(self.config.candidates_path) / job_name
        if not candidates_path.exists():
            print(f"❌ No candidates found for job {job_name}")
            return

        re_evaluated = []
        total_candidates = len([d for d in candidates_path.iterdir() if d.is_dir() and (not candidate_names or d.name in candidate_names)])
        current_count = 0

        for candidate_dir in candidates_path.iterdir():
            if candidate_dir.is_dir():
                candidate_name = candidate_dir.name

                # Skip if specific candidates requested and this isn't one
                if candidate_names and candidate_name not in candidate_names:
                    continue

                current_count += 1

                # Load candidate data
                candidate = self._load_candidate_data(candidate_dir)
                if not candidate:
                    continue

                # Re-evaluate with insights
                print(f"🔄 Re-evaluating {candidate_name} ({current_count}/{total_candidates}) with updated insights...")
                evaluation = self.ai_client.evaluate_candidate(
                    job_context, candidate, job_insights.generated_insights
                )

                # Save new evaluation (keep history)
                self._save_evaluation_with_history(candidate_dir, evaluation)
                re_evaluated.append(candidate_name)

                print(
                    f"✅ Re-evaluated {candidate_name} "
                    f"(Score: {evaluation.overall_score}/100)"
                )

        if re_evaluated:
            print(
                f"\n🎉 Re-evaluated {len(re_evaluated)} candidates with updated insights"
            )

            # Generate updated reports
            try:
                # Load all evaluations for the job
                evaluations = []
                for candidate_dir in candidates_path.iterdir():
                    if candidate_dir.is_dir():
                        eval_path = candidate_dir / "evaluation.json"
                        if eval_path.exists():
                            with open(eval_path, "r", encoding="utf-8") as f:
                                eval_data = json.load(f)
                                evaluation = Evaluation.from_dict(eval_data)
                                evaluations.append(evaluation)

                if evaluations:
                    # Import output generator
                    from output_generator import OutputGenerator

                    output_gen = OutputGenerator(self.config)

                    # Generate new reports
                    output_path = self.config.get_output_path(job_name)
                    csv_path = output_gen.generate_csv(
                        evaluations, output_path, job_name
                    )
                    html_path = output_gen.generate_html_report(
                        job_context, evaluations, output_path
                    )

                    print("\n📊 Updated reports generated:")
                    print(f"   📈 CSV: {csv_path}")
                    print(f"   🌐 HTML: {html_path}")

            except Exception as e:
                print(f"   ⚠️  Could not generate updated reports: {e}")
        else:
            print("❌ No candidates were re-evaluated")

    def _update_job_feedback_summary(
        self, job_name: str, feedback_record: FeedbackRecord
    ) -> None:
        """Update job-level feedback summary."""
        output_dir = self.config.get_output_path(job_name)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        summary_path = Path(output_dir) / "feedback_summary.json"

        # Load existing summary or create new
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                summary = json.load(f)
        else:
            summary = {
                "job_name": job_name,
                "total_feedback_count": 0,
                "feedback_records": [],
                "last_updated": None,
            }

        # Add new feedback
        summary["total_feedback_count"] += 1
        summary["feedback_records"].append(
            {
                "candidate_name": feedback_record.candidate_name,
                "timestamp": feedback_record.human_feedback.timestamp.isoformat(),
                "human_recommendation": (
                    feedback_record.human_feedback.human_recommendation.value
                ),
                "ai_recommendation": (
                    feedback_record.original_evaluation.recommendation.value
                ),
            }
        )
        summary["last_updated"] = datetime.now().isoformat()

        # Save updated summary
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    def _maybe_generate_insights(self, job_name: str) -> None:
        """Generate insights if we have enough feedback."""
        feedback_count = len(self.get_feedback_history(job_name))

        # Generate insights after every 2 feedback records
        if feedback_count >= 2 and feedback_count % 2 == 0:
            print(
                f"\n🧠 Generating insights based on {feedback_count} feedback records..."
            )
            self.build_insights(job_name)

    def _load_job_context(self, job_name: str):
        """Load job context from job directory."""
        # This is a simplified version - reuse logic from candidate_reviewer.py
        job_dir = Path(self.config.get_job_path(job_name))

        desc_file = job_dir / "job_description.pdf"
        ideal_file = job_dir / "ideal_candidate.txt"
        warning_file = job_dir / "warning_flags.txt"

        if not desc_file.exists():
            return None

        # For now, we'll need to import file_processor to extract text
        from file_processor import FileProcessor

        processor = FileProcessor(self.config)

        description, _ = processor.extract_text_from_file(str(desc_file))

        ideal_candidate = None
        if ideal_file.exists():
            ideal_candidate, _ = processor.extract_text_from_file(str(ideal_file))

        warning_flags = None
        if warning_file.exists():
            warning_flags, _ = processor.extract_text_from_file(str(warning_file))

        from models import JobContext

        return JobContext(
            name=job_name,
            description=description,
            ideal_candidate=ideal_candidate,
            warning_flags=warning_flags,
        )

    def _load_job_insights(self, job_name: str) -> Optional[JobInsights]:
        """Load job insights from job directory."""
        job_dir = Path(self.config.get_job_path(job_name))
        insights_path = job_dir / "insights.json"

        if not insights_path.exists():
            return None

        try:
            with open(insights_path, "r", encoding="utf-8") as f:
                insights_data = json.load(f)
                return JobInsights.from_dict(insights_data)
        except (json.JSONDecodeError, KeyError):
            return None

    def _load_candidate_data(self, candidate_dir: Path):
        """Load candidate data from directory."""
        # Load candidate files and reconstruct Candidate object
        resume_file = None
        cover_letter_file = None
        application_file = None

        for file_path in candidate_dir.iterdir():
            if file_path.name.startswith("resume"):
                resume_file = file_path
            elif file_path.name.startswith("cover_letter"):
                cover_letter_file = file_path
            elif file_path.name.startswith("application"):
                application_file = file_path

        if not resume_file:
            return None

        from file_processor import FileProcessor

        processor = FileProcessor(self.config)

        resume_text, _ = processor.extract_text_from_file(str(resume_file))

        cover_letter = None
        if cover_letter_file:
            cover_letter, _ = processor.extract_text_from_file(str(cover_letter_file))

        application = None
        if application_file:
            application, _ = processor.extract_text_from_file(str(application_file))

        from models import Candidate

        return Candidate(
            name=candidate_dir.name,
            resume_text=resume_text,
            cover_letter=cover_letter,
            application=application,
        )

    def _save_evaluation_with_history(
        self, candidate_dir: Path, evaluation: Evaluation
    ) -> None:
        """Save evaluation and maintain history."""
        eval_path = candidate_dir / "evaluation.json"
        history_path = candidate_dir / "evaluation_history.json"

        # Load existing history
        history = []
        if history_path.exists():
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                history = []

        # Add current evaluation to history if it exists
        if eval_path.exists():
            try:
                with open(eval_path, "r", encoding="utf-8") as f:
                    current_eval = json.load(f)
                    history.append(current_eval)
            except json.JSONDecodeError:
                pass

        # Save new evaluation
        with open(eval_path, "w", encoding="utf-8") as f:
            json.dump(evaluation.to_dict(), f, indent=2, ensure_ascii=False)

        # Save history
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def _calculate_effectiveness_metrics(
        self, feedback_records: List[FeedbackRecord]
    ) -> Dict[str, float]:
        """Calculate effectiveness metrics from feedback."""
        if not feedback_records:
            return {}

        # Calculate agreement rate
        agreements = 0
        for record in feedback_records:
            ai_rec = record.original_evaluation.recommendation.value
            human_rec = record.human_feedback.human_recommendation.value

            # Simple agreement check (could be more sophisticated)
            if ai_rec == human_rec:
                agreements += 1

        agreement_rate = agreements / len(feedback_records)

        return {
            "agreement_rate": agreement_rate,
            "total_feedback": len(feedback_records),
            "last_calculated": datetime.now().timestamp(),
        }
