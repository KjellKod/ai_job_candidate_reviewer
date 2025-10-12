"""Output generation for AI Job Candidate Reviewer."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

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

        # Prepare CSV data
        csv_data = []
        for rank, evaluation in enumerate(sorted_evaluations, 1):
            csv_data.append(
                {
                    "Rank": rank,
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

        # Sort evaluations by score (descending)
        sorted_evaluations = sorted(
            evaluations, key=lambda e: e.overall_score, reverse=True
        )

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

        for rank, evaluation in enumerate(sorted_evaluations, 1):
            # Color coding for recommendations
            rec_color = self._get_recommendation_color(evaluation.recommendation)
            priority_icon = self._get_priority_icon(evaluation.interview_priority)

            print(f"\n{rank}. {evaluation.candidate_name}")
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

        print("\n" + "=" * 80)

        # Summary statistics
        self._display_summary_stats(sorted_evaluations)

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

    def load_evaluations_for_job(self, job_name: str) -> List[Evaluation]:
        """Load all evaluations for a job.

        Args:
            job_name: Name of the job

        Returns:
            List of evaluations
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

        return evaluations

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
        stats = self.generate_summary_stats(evaluations)

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

        for rank, evaluation in enumerate(evaluations, 1):
            rec_class = evaluation.recommendation.value.lower().replace("_", "-")

            html += f"""
    <div class="candidate">
        <h3>{rank}. {evaluation.candidate_name}</h3>
        <p>
            <span class="score">Score: {evaluation.overall_score}/100</span> | 
            <span class="recommendation {rec_class}">{evaluation.recommendation.value}</span> | 
            <strong>Priority:</strong> {evaluation.interview_priority.value}
        </p>
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

        html += """
</body>
</html>
"""

        return html
