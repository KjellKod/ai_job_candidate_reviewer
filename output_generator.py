"""Output generation for AI Job Candidate Reviewer."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from config import Config
from models import Evaluation, InterviewPriority, JobContext, RecommendationType


class OutputGenerator:
    """Generate CSV reports and terminal displays for candidate evaluations."""

    def __init__(self, config: Config):
        """Initialize output generator.

        Args:
            config: Configuration object
        """
        self.config = config

    def generate_csv(
        self, evaluations: List[Evaluation], output_path: str, job_name: str
    ) -> str:
        """Generate CSV file with candidate evaluations.

        Args:
            evaluations: List of candidate evaluations
            output_path: Directory path for output
            job_name: Name of the job

        Returns:
            Path to generated CSV file
        """
        # Create output directory
        Path(output_path).mkdir(parents=True, exist_ok=True)

        # Generate CSV filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"candidate_scores_{timestamp}.csv"
        csv_path = Path(output_path) / csv_filename

        # Sort evaluations by score (descending)
        sorted_evaluations = sorted(
            evaluations, key=lambda e: e.overall_score, reverse=True
        )

        # Prepare duplicate flags
        duplicate_flags = self._load_duplicate_warnings(job_name)

        # Prepare CSV data
        csv_data = []
        for rank, evaluation in enumerate(sorted_evaluations, 1):
            flags = []
            if evaluation.candidate_name in duplicate_flags:
                flags.append("DUPLICATE_IDENTIFIERS")

            # Check rejection status
            is_rejected = self._is_candidate_rejected(
                job_name, evaluation.candidate_name
            )
            status = "Rejected" if is_rejected else "Active"

            csv_data.append(
                {
                    "Rank": rank,
                    "Status": status,
                    "Candidate Name": evaluation.candidate_name,
                    "Overall Score": evaluation.overall_score,
                    "Recommendation": evaluation.recommendation.value,
                    "Interview Priority": evaluation.interview_priority.value,
                    "Strengths": "; ".join(evaluation.strengths),
                    "Concerns": "; ".join(evaluation.concerns),
                    "Detailed Notes": evaluation.detailed_notes,
                    "Evaluation Date": evaluation.timestamp.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "AI Insights Used": evaluation.ai_insights_used or "None",
                    "Flags": ", ".join(flags) if flags else "",
                }
            )

        # Write CSV file
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            if csv_data:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)

        return str(csv_path)

    def display_terminal_ranking(
        self, evaluations: List[Evaluation], job_name: str
    ) -> None:
        """Display candidate rankings in terminal.

        Args:
            evaluations: List of candidate evaluations
            job_name: Name of the job
        """
        if not evaluations:
            print(f"\n📋 No candidates found for job: {job_name}")
            return

        # Separate rejected and active candidates
        active_evaluations = []
        rejected_evaluations = []

        for evaluation in evaluations:
            if self._is_candidate_rejected(job_name, evaluation.candidate_name):
                rejected_evaluations.append(evaluation)
            else:
                active_evaluations.append(evaluation)

        # Sort evaluations by score (descending)
        sorted_active = sorted(
            active_evaluations, key=lambda e: e.overall_score, reverse=True
        )
        sorted_rejected = sorted(
            rejected_evaluations, key=lambda e: e.overall_score, reverse=True
        )

        # Load duplicate flags
        duplicate_flags = self._load_duplicate_warnings(job_name)

        print(f"\n🎯 Candidate Rankings for: {job_name}")
        print("=" * 80)

        # Add explanatory header
        print("\n📊 How to Read the Results:")
        print("   Score: [0-100] | [RECOMMENDATION] | [🔥📋📝] [INTERVIEW PRIORITY]")
        print("")
        print(
            "   \033[92mSTRONG_YES\033[0m = Great catch         🔥 HIGH = Interview ASAP"
        )
        print(
            "   \033[94mYES\033[0m = Consider hiring            📋 MEDIUM = Not sure. Review again before deciding"
        )
        print(
            "   \033[93mMAYBE\033[0m = Consider carefully       📝 LOW = Likely not worth interviewing. Too many red flags"
        )
        print("   \033[91mNO\033[0m/\033[95mSTRONG_NO\033[0m = Don't recommend")
        print("=" * 80)

        # Display active candidates
        for rank, evaluation in enumerate(sorted_active, 1):
            # Color coding for recommendations
            rec_color = self._get_recommendation_color(evaluation.recommendation)
            priority_icon = self._get_priority_icon(evaluation.interview_priority)

            dup_tag = (
                " \U0001f6a8 DUPLICATE"
                if evaluation.candidate_name in duplicate_flags
                else ""
            )
            print(f"\n{rank}. {evaluation.candidate_name}{dup_tag}")
            print(
                f"   Score: {evaluation.overall_score}/100 | {rec_color}{evaluation.recommendation.value}\033[0m | {priority_icon} {evaluation.interview_priority.value}"
            )

            if evaluation.strengths:
                print(
                    f"   ✅ Strengths: {', '.join(evaluation.strengths[:3])}{'...' if len(evaluation.strengths) > 3 else ''}"
                )

            if evaluation.concerns:
                print(
                    f"   ⚠️  Concerns: {', '.join(evaluation.concerns[:2])}{'...' if len(evaluation.concerns) > 2 else ''}"
                )

            # If duplicate, print prominent warning with brief details
            if evaluation.candidate_name in duplicate_flags:
                snippet = duplicate_flags[evaluation.candidate_name]
                if snippet:
                    print(f"   🚨 Duplicate identifiers detected: {snippet}")

        print("\n" + "=" * 80)

        # Summary statistics for active candidates
        self._display_summary_stats(sorted_active)

        # Display rejected candidates section if there are any
        if sorted_rejected:
            print("\n" + "─" * 80)
            print(f"🚫 REJECTED CANDIDATES ({len(sorted_rejected)})")
            print("─" * 80)

            for evaluation in sorted_rejected:
                rec_color = self._get_recommendation_color(evaluation.recommendation)

                # Get rejection info
                rejection_info = self._get_rejection_info(
                    job_name, evaluation.candidate_name
                )
                reason = (
                    rejection_info.get("reason", "No reason provided")
                    if rejection_info
                    else "No reason provided"
                )

                print(
                    f"\n    [{evaluation.overall_score}] {rec_color}{evaluation.recommendation.value}\033[0m {evaluation.candidate_name}"
                )
                print(f"         Reason: {reason}")

            print("\n" + "=" * 80)

    def generate_html_report(
        self, job_context: JobContext, evaluations: List[Evaluation], output_path: str
    ) -> str:
        """Generate detailed HTML report.

        Args:
            job_context: Job context information
            evaluations: List of candidate evaluations
            output_path: Directory path for output

        Returns:
            Path to generated HTML file
        """
        # Create output directory
        Path(output_path).mkdir(parents=True, exist_ok=True)

        # Generate HTML filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"detailed_report_{timestamp}.html"
        html_path = Path(output_path) / html_filename

        # Sort evaluations by score (descending)
        sorted_evaluations = sorted(
            evaluations, key=lambda e: e.overall_score, reverse=True
        )

        # Generate HTML content
        html_content = self._build_html_content(job_context, sorted_evaluations)

        # Write HTML file
        with open(html_path, "w", encoding="utf-8") as htmlfile:
            htmlfile.write(html_content)

        return str(html_path)

    def save_evaluation_json(self, evaluation: Evaluation, candidate_dir: str) -> str:
        """Save individual evaluation as JSON.

        Args:
            evaluation: Candidate evaluation
            candidate_dir: Directory path for candidate

        Returns:
            Path to saved JSON file
        """
        # Create candidate directory
        Path(candidate_dir).mkdir(parents=True, exist_ok=True)

        json_path = Path(candidate_dir) / "evaluation.json"

        # Save evaluation
        with open(json_path, "w", encoding="utf-8") as jsonfile:
            json.dump(evaluation.to_dict(), jsonfile, indent=2, ensure_ascii=False)

        return str(json_path)

    def load_evaluations_for_job(
        self, job_name: str, silent: bool = False
    ) -> List[Evaluation]:
        """Load all evaluations for a job.

        Args:
            job_name: Name of the job
            silent: If True, suppress deduplication messages

        Returns:
            List of evaluations (deduplicated by candidate name, keeping most recent)
        """
        evaluations = []
        candidates_path = Path(self.config.candidates_path) / job_name

        if not candidates_path.exists():
            return evaluations

        # Load evaluations from each candidate directory
        for candidate_dir in candidates_path.iterdir():
            if candidate_dir.is_dir():
                eval_path = candidate_dir / "evaluation.json"
                if eval_path.exists():
                    try:
                        with open(eval_path, "r", encoding="utf-8") as jsonfile:
                            eval_data = json.load(jsonfile)
                            evaluation = Evaluation.from_dict(eval_data)
                            evaluations.append(evaluation)
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        print(
                            f"Warning: Could not load evaluation for {candidate_dir.name}: {e}"
                        )

        # Deduplicate by candidate name, keeping the most recent evaluation
        return self._deduplicate_evaluations(evaluations, silent=silent)

    def _deduplicate_evaluations(
        self, evaluations: List[Evaluation], silent: bool = False
    ) -> List[Evaluation]:
        """Deduplicate evaluations by candidate name, keeping most recent.

        Args:
            evaluations: List of evaluations that may contain duplicates
            silent: If True, suppress deduplication messages

        Returns:
            List of evaluations with duplicates removed
        """
        if not evaluations:
            return evaluations

        # Use more sophisticated matching instead of simple key-based grouping
        unique_evaluations = []

        for evaluation in evaluations:
            # Check if this candidate already exists in our unique list
            existing_index = None

            for i, existing_eval in enumerate(unique_evaluations):
                if self._are_same_candidate(
                    evaluation.candidate_name, existing_eval.candidate_name
                ):
                    existing_index = i
                    break

            if existing_index is not None:
                # Found a duplicate - keep the better one (prefer full names and more recent)
                existing_eval = unique_evaluations[existing_index]

                # Prefer full names over partial names (more parts = more specific)
                existing_parts = len(existing_eval.candidate_name.split("_"))
                new_parts = len(evaluation.candidate_name.split("_"))

                should_replace = False

                if new_parts > existing_parts:
                    # New name has more parts (more specific) - prefer it
                    should_replace = True
                    reason = f"more specific name ({evaluation.candidate_name} vs {existing_eval.candidate_name})"
                elif existing_parts > new_parts:
                    # Existing name has more parts - keep it
                    should_replace = False
                    reason = f"keeping more specific name ({existing_eval.candidate_name} vs {evaluation.candidate_name})"
                else:
                    # Same number of parts - use timestamp
                    if evaluation.timestamp > existing_eval.timestamp:
                        should_replace = True
                        reason = f"newer timestamp"
                    else:
                        should_replace = False
                        reason = f"older timestamp"

                if should_replace:
                    unique_evaluations[existing_index] = evaluation
                    if not silent:
                        print(
                            f"📋 Deduplicated: Replaced {existing_eval.candidate_name} with {evaluation.candidate_name} ({reason})"
                        )
                else:
                    if not silent:
                        print(
                            f"📋 Deduplicated: Kept {existing_eval.candidate_name}, skipped {evaluation.candidate_name} ({reason})"
                        )
            else:
                # No duplicate found, add to unique list
                unique_evaluations.append(evaluation)

        return unique_evaluations

    def _normalize_candidate_name(self, name: str) -> str:
        """Normalize candidate name for deduplication.

        Args:
            name: Original candidate name

        Returns:
            Normalized name for comparison
        """
        # Convert to lowercase for comparison
        normalized = name.lower()

        # Remove common suffixes that indicate file types
        type_suffixes = ["_resume", "_application", "_cover", "_coverletter"]
        for suffix in type_suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[: -len(suffix)]
                break

        # Split into parts for more sophisticated matching
        parts = normalized.split("_")
        parts = [part for part in parts if part]  # Remove empty parts

        if not parts:
            return normalized

        # For single part names, check if it could be a last name
        if len(parts) == 1:
            single_part = parts[0]
            # This will be used to match against multi-part names containing this part
            return single_part

        # For multi-part names, create multiple possible matches
        # This handles firstname_lastname, lastname_firstname, etc.
        if len(parts) >= 2:
            # Primary key: sort all parts for consistent ordering
            primary_key = "_".join(sorted(parts))
            return primary_key

        return normalized

    def _are_same_candidate(self, name1: str, name2: str) -> bool:
        """Check if two candidate names refer to the same person.

        Args:
            name1: First candidate name
            name2: Second candidate name

        Returns:
            True if they likely refer to the same person
        """
        norm1 = self._normalize_candidate_name(name1)
        norm2 = self._normalize_candidate_name(name2)

        # Direct match
        if norm1 == norm2:
            return True

        # Check if one name is contained in the other (handles firstname_lastname vs lastname cases)
        parts1 = set(norm1.split("_"))
        parts2 = set(norm2.split("_"))

        # If one is a subset of the other with significant overlap
        if parts1 and parts2:
            intersection = parts1.intersection(parts2)
            # If there's at least one common part and one name is a subset of the other
            if intersection and (parts1.issubset(parts2) or parts2.issubset(parts1)):
                return True

        return False

    def generate_summary_stats(self, evaluations: List[Evaluation]) -> Dict:
        """Generate summary statistics for evaluations.

        Args:
            evaluations: List of evaluations

        Returns:
            Dictionary with summary statistics
        """
        if not evaluations:
            return {}

        scores = [e.overall_score for e in evaluations]
        recommendations = [e.recommendation.value for e in evaluations]
        priorities = [e.interview_priority.value for e in evaluations]

        # Count recommendations
        rec_counts = {}
        for rec in RecommendationType:
            rec_counts[rec.value] = recommendations.count(rec.value)

        # Count priorities
        priority_counts = {}
        for priority in InterviewPriority:
            priority_counts[priority.value] = priorities.count(priority.value)

        return {
            "total_candidates": len(evaluations),
            "average_score": sum(scores) / len(scores),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "recommendation_counts": rec_counts,
            "priority_counts": priority_counts,
            "strong_candidates": len(
                [
                    e
                    for e in evaluations
                    if e.recommendation
                    in [RecommendationType.STRONG_YES, RecommendationType.YES]
                ]
            ),
            "high_priority_interviews": len(
                [
                    e
                    for e in evaluations
                    if e.interview_priority == InterviewPriority.HIGH
                ]
            ),
        }

    def _get_recommendation_color(self, recommendation: RecommendationType) -> str:
        """Get ANSI color code for recommendation.

        Args:
            recommendation: Recommendation type

        Returns:
            ANSI color code
        """
        colors = {
            RecommendationType.STRONG_YES: "\033[92m",  # Green
            RecommendationType.YES: "\033[94m",  # Blue
            RecommendationType.MAYBE: "\033[93m",  # Yellow
            RecommendationType.NO: "\033[91m",  # Red
            RecommendationType.STRONG_NO: "\033[95m",  # Magenta
        }
        return colors.get(recommendation, "\033[0m")

    def _get_priority_icon(self, priority: InterviewPriority) -> str:
        """Get icon for interview priority.

        Args:
            priority: Interview priority

        Returns:
            Priority icon
        """
        icons = {
            InterviewPriority.HIGH: "🔥",
            InterviewPriority.MEDIUM: "📋",
            InterviewPriority.LOW: "📝",
        }
        return icons.get(priority, "📝")

    def _display_summary_stats(self, evaluations: List[Evaluation]) -> None:
        """Display summary statistics in terminal.

        Args:
            evaluations: List of evaluations
        """
        stats = self.generate_summary_stats(evaluations)

        if not stats:
            return

        print(f"📊 Summary Statistics:")
        print(f"   Total Candidates: {stats['total_candidates']}")
        print(f"   Average Score: {stats['average_score']:.1f}")
        print(f"   Score Range: {stats['lowest_score']} - {stats['highest_score']}")
        print(f"   Strong Candidates (YES/STRONG_YES): {stats['strong_candidates']}")
        print(f"   High Priority Interviews: {stats['high_priority_interviews']}")

    def _build_html_content(
        self, job_context: JobContext, evaluations: List[Evaluation]
    ) -> str:
        """Build HTML content for detailed report.

        Args:
            job_context: Job context information
            evaluations: List of evaluations

        Returns:
            HTML content string
        """
        # Split into active and rejected for clearer presentation
        active_evaluations: List[Evaluation] = []
        rejected_evaluations: List[Evaluation] = []
        for ev in evaluations:
            if self._is_candidate_rejected(job_context.name, ev.candidate_name):
                rejected_evaluations.append(ev)
            else:
                active_evaluations.append(ev)

        # Stats only for active candidates
        stats = self.generate_summary_stats(active_evaluations)

        # Load duplicate flags (by job name)
        duplicate_flags = self._load_duplicate_warnings(job_context.name)

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Candidate Evaluation Report - {job_context.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .stats {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .candidate {{ border: 1px solid #ddd; margin-bottom: 20px; padding: 15px; border-radius: 5px; }}
        .candidate h3 {{ margin-top: 0; color: #333; }}
        .score {{ font-size: 1.2em; font-weight: bold; }}
        .recommendation {{ padding: 5px 10px; border-radius: 3px; color: white; }}
        .strong-yes {{ background-color: #28a745; }}
        .yes {{ background-color: #007bff; }}
        .maybe {{ background-color: #ffc107; color: black; }}
        .no {{ background-color: #dc3545; }}
        .strong-no {{ background-color: #6f42c1; }}
        .strengths {{ color: #28a745; }}
        .concerns {{ color: #dc3545; }}
        ul {{ margin: 5px 0; }}
        .duplicate-banner {{ background-color: #ffe3e3; color: #b00020; padding: 8px 12px; border-radius: 4px; margin: 8px 0; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Candidate Evaluation Report</h1>
        <h2>{job_context.name}</h2>
        <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
"""

        if stats:
            html += f"""
    <div class="stats">
        <h3>Summary Statistics</h3>
        <p><strong>Total Candidates:</strong> {stats['total_candidates']}</p>
        <p><strong>Average Score:</strong> {stats['average_score']:.1f}</p>
        <p><strong>Score Range:</strong> {stats['lowest_score']} - {stats['highest_score']}</p>
        <p><strong>Strong Candidates:</strong> {stats['strong_candidates']}</p>
        <p><strong>High Priority Interviews:</strong> {stats['high_priority_interviews']}</p>
    </div>
"""

        html += "<h3>Candidate Evaluations</h3>"

        for rank, evaluation in enumerate(active_evaluations, 1):
            rec_class = evaluation.recommendation.value.lower().replace("_", "-")

            html += f"""
    <div class="candidate">
        <h3>{rank}. {evaluation.candidate_name}{' 🚨 DUPLICATE' if evaluation.candidate_name in duplicate_flags else ''}</h3>
        <p>
            <span class="score">Score: {evaluation.overall_score}/100</span> |
            <span class="recommendation {rec_class}">{evaluation.recommendation.value}</span> |
            <strong>Priority:</strong> {evaluation.interview_priority.value}
        </p>
"""

            # Add duplicate banner if applicable
            if evaluation.candidate_name in duplicate_flags:
                banner = duplicate_flags[evaluation.candidate_name]
                html += f"""
        <div class="duplicate-banner">
            🚨 Duplicate identifiers detected. {banner}
        </div>
"""

            if evaluation.strengths:
                html += f"""
        <div class="strengths">
            <strong>Strengths:</strong>
            <ul>
                {''.join(f'<li>{strength}</li>' for strength in evaluation.strengths)}
            </ul>
        </div>
"""

            if evaluation.concerns:
                html += f"""
        <div class="concerns">
            <strong>Concerns:</strong>
            <ul>
                {''.join(f'<li>{concern}</li>' for concern in evaluation.concerns)}
            </ul>
        </div>
"""

            html += f"""
        <p><strong>Detailed Notes:</strong> {evaluation.detailed_notes}</p>
        <p><small><strong>Evaluated:</strong> {evaluation.timestamp.strftime("%Y-%m-%d %H:%M:%S")}</small></p>
    </div>
"""

        # Rejected section
        if rejected_evaluations:
            html += """
    <hr/>
    <h3>🚫 Rejected Candidates</h3>
    <p>The following candidates have been rejected and are excluded from evaluation rankings.</p>
"""
            # Sort rejected by score descending for consistency
            rejected_sorted = sorted(
                rejected_evaluations, key=lambda e: e.overall_score, reverse=True
            )
            for evaluation in rejected_sorted:
                info = self._get_rejection_info(
                    job_context.name, evaluation.candidate_name
                )
                reason = (
                    info.get("reason", "No reason provided")
                    if info
                    else "No reason provided"
                )
                html += f"""
    <div class="candidate">
        <h3>{evaluation.candidate_name}</h3>
        <p>
            <span class=\"score\">Score: {evaluation.overall_score}/100</span> |
            <span class=\"recommendation {evaluation.recommendation.value.lower().replace('_','-')}\">{evaluation.recommendation.value}</span>
        </p>
        <p><strong>Reason:</strong> {reason}</p>
        <p><small><strong>Evaluated:</strong> {evaluation.timestamp.strftime("%Y-%m-%d %H:%M:%S")}</small></p>
    </div>
"""

        html += """
</body>
</html>
"""

        return html

    def _is_candidate_rejected(self, job_name: str, candidate_name: str) -> bool:
        """Check if a candidate is marked as rejected.

        Args:
            job_name: Name of the job
            candidate_name: Name of the candidate

        Returns:
            True if candidate is rejected, False otherwise
        """
        candidate_dir = Path(self.config.get_candidate_path(job_name, candidate_name))
        meta_path = candidate_dir / "candidate_meta.json"

        if not meta_path.exists():
            return False

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                return meta.get("rejected", False)
        except (json.JSONDecodeError, KeyError):
            return False

    def _get_rejection_info(self, job_name: str, candidate_name: str) -> Optional[dict]:
        """Get rejection information for a candidate.

        Args:
            job_name: Name of the job
            candidate_name: Name of the candidate

        Returns:
            Dict with rejection info or None if not rejected
        """
        candidate_dir = Path(self.config.get_candidate_path(job_name, candidate_name))
        meta_path = candidate_dir / "candidate_meta.json"

        if not meta_path.exists():
            return None

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                if meta.get("rejected", False):
                    return {
                        "reason": meta.get("rejection_reason", "No reason provided"),
                        "timestamp": meta.get("rejection_timestamp", "Unknown"),
                    }
        except (json.JSONDecodeError, KeyError):
            pass

        return None

    def _load_duplicate_warnings(self, job_name: str) -> Dict[str, str]:
        """Load duplicate warning snippets for all candidates in a job.

        Returns a mapping: candidate_name -> short snippet from warning file.
        """
        flags: Dict[str, str] = {}
        candidates_path = Path(self.config.candidates_path) / job_name
        if not candidates_path.exists():
            return flags
        for candidate_dir in candidates_path.iterdir():
            if not candidate_dir.is_dir():
                continue
            warning_path = candidate_dir / "DUPLICATE_WARNING.txt"
            if warning_path.exists():
                try:
                    text = warning_path.read_text(encoding="utf-8").strip()
                    # Try to extract one-line summary
                    lines = [l.strip() for l in text.splitlines() if l.strip()]
                    summary = (
                        " ".join(lines[1:3])
                        if len(lines) > 1
                        else lines[0] if lines else ""
                    )
                    flags[candidate_dir.name] = summary
                except OSError:
                    flags[candidate_dir.name] = ""
        return flags
