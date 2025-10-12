"""Unit tests for output generator."""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch
import pytest

from output_generator import OutputGenerator
from config import Config
from models import (
    Evaluation,
    JobContext,
    RecommendationType,
    InterviewPriority,
)


class TestOutputGenerator:
    """Test output generation functionality."""

    def test_initialization(self):
        """Test output generator initialization."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            generator = OutputGenerator(config)

            assert generator.config == config

    def test_csv_generation(self):
        """Test CSV file generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"BASE_DATA_PATH": temp_dir}, clear=True):
                config = Config()
                generator = OutputGenerator(config)

                # Create test evaluations
                evaluations = [
                    Evaluation(
                        candidate_name="john_doe",
                        job_name="test_job",
                        overall_score=85,
                        recommendation=RecommendationType.YES,
                        strengths=["Strong Python skills", "Good communication"],
                        concerns=["Limited leadership experience"],
                        interview_priority=InterviewPriority.HIGH,
                        detailed_notes="Solid candidate",
                    ),
                    Evaluation(
                        candidate_name="jane_smith",
                        job_name="test_job",
                        overall_score=75,
                        recommendation=RecommendationType.MAYBE,
                        strengths=["Good technical skills"],
                        concerns=["Needs more experience"],
                        interview_priority=InterviewPriority.MEDIUM,
                        detailed_notes="Decent candidate",
                    ),
                ]

                # Generate CSV
                csv_path = generator.generate_csv(evaluations, temp_dir, "test_job")

                # Verify file was created
                assert os.path.exists(csv_path)
                assert csv_path.endswith(".csv")

                # Verify CSV content
                with open(csv_path, "r") as f:
                    content = f.read()
                    assert "john_doe" in content
                    assert "jane_smith" in content
                    assert "85" in content
                    assert "75" in content
                    assert "YES" in content
                    assert "MAYBE" in content

    def test_html_report_generation(self):
        """Test HTML report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"BASE_DATA_PATH": temp_dir}, clear=True):
                config = Config()
                generator = OutputGenerator(config)

                job_context = JobContext(
                    name="test_job",
                    description="Test job description",
                    ideal_candidate="Test ideal candidate",
                )

                evaluations = [
                    Evaluation(
                        candidate_name="john_doe",
                        job_name="test_job",
                        overall_score=90,
                        recommendation=RecommendationType.STRONG_YES,
                        strengths=["Excellent skills"],
                        concerns=[],
                        interview_priority=InterviewPriority.HIGH,
                        detailed_notes="Top candidate",
                    )
                ]

                # Generate HTML report
                html_path = generator.generate_html_report(job_context, evaluations, temp_dir)

                # Verify file was created
                assert os.path.exists(html_path)
                assert html_path.endswith(".html")

                # Verify HTML content
                with open(html_path, "r") as f:
                    content = f.read()
                    assert "<!DOCTYPE html>" in content
                    assert "test_job" in content
                    assert "john_doe" in content
                    assert "90/100" in content
                    assert "STRONG_YES" in content

    def test_evaluation_json_saving(self):
        """Test saving individual evaluation as JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"BASE_DATA_PATH": temp_dir}, clear=True):
                config = Config()
                generator = OutputGenerator(config)

                evaluation = Evaluation(
                    candidate_name="test_candidate",
                    job_name="test_job",
                    overall_score=80,
                    recommendation=RecommendationType.YES,
                    strengths=["Good skills"],
                    concerns=["Minor issues"],
                    interview_priority=InterviewPriority.MEDIUM,
                    detailed_notes="Good candidate",
                )

                # Save evaluation
                json_path = generator.save_evaluation_json(evaluation, temp_dir)

                # Verify file was created
                assert os.path.exists(json_path)
                assert json_path.endswith("evaluation.json")

                # Verify JSON content
                import json
                with open(json_path, "r") as f:
                    data = json.load(f)
                    assert data["candidate_name"] == "test_candidate"
                    assert data["overall_score"] == 80
                    assert data["recommendation"] == "YES"

    def test_summary_statistics_generation(self):
        """Test generation of summary statistics."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            generator = OutputGenerator(config)

            evaluations = [
                Evaluation(
                    candidate_name="candidate_1",
                    job_name="test_job",
                    overall_score=90,
                    recommendation=RecommendationType.STRONG_YES,
                    strengths=["Test"],
                    concerns=[],
                    interview_priority=InterviewPriority.HIGH,
                    detailed_notes="Test",
                ),
                Evaluation(
                    candidate_name="candidate_2",
                    job_name="test_job",
                    overall_score=70,
                    recommendation=RecommendationType.MAYBE,
                    strengths=["Test"],
                    concerns=["Test"],
                    interview_priority=InterviewPriority.MEDIUM,
                    detailed_notes="Test",
                ),
                Evaluation(
                    candidate_name="candidate_3",
                    job_name="test_job",
                    overall_score=50,
                    recommendation=RecommendationType.NO,
                    strengths=[],
                    concerns=["Test"],
                    interview_priority=InterviewPriority.LOW,
                    detailed_notes="Test",
                ),
            ]

            stats = generator.generate_summary_stats(evaluations)

            assert stats["total_candidates"] == 3
            assert stats["average_score"] == 70.0  # (90 + 70 + 50) / 3
            assert stats["highest_score"] == 90
            assert stats["lowest_score"] == 50
            assert stats["strong_candidates"] == 1  # Only STRONG_YES
            assert stats["high_priority_interviews"] == 1  # Only HIGH priority

    def test_load_evaluations_for_job(self):
        """Test loading evaluations for a job."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"BASE_DATA_PATH": temp_dir}, clear=True):
                config = Config()
                generator = OutputGenerator(config)

                job_name = "test_job"
                
                # Create candidate directories with evaluations
                candidates_dir = Path(config.candidates_path) / job_name
                candidates_dir.mkdir(parents=True, exist_ok=True)

                # Create test evaluations
                test_evaluations = []
                for i, candidate_name in enumerate(["john_doe", "jane_smith"]):
                    candidate_dir = candidates_dir / candidate_name
                    candidate_dir.mkdir(parents=True, exist_ok=True)

                    evaluation = Evaluation(
                        candidate_name=candidate_name,
                        job_name=job_name,
                        overall_score=80 + i * 5,
                        recommendation=RecommendationType.YES,
                        strengths=["Test strength"],
                        concerns=["Test concern"],
                        interview_priority=InterviewPriority.MEDIUM,
                        detailed_notes="Test notes",
                    )
                    test_evaluations.append(evaluation)

                    # Save evaluation
                    eval_path = candidate_dir / "evaluation.json"
                    import json
                    with open(eval_path, "w") as f:
                        json.dump(evaluation.to_dict(), f)

                # Load evaluations
                loaded_evaluations = generator.load_evaluations_for_job(job_name)

                assert len(loaded_evaluations) == 2
                loaded_names = {e.candidate_name for e in loaded_evaluations}
                assert "john_doe" in loaded_names
                assert "jane_smith" in loaded_names

    def test_terminal_ranking_display(self):
        """Test terminal ranking display."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            generator = OutputGenerator(config)

            evaluations = [
                Evaluation(
                    candidate_name="top_candidate",
                    job_name="test_job",
                    overall_score=95,
                    recommendation=RecommendationType.STRONG_YES,
                    strengths=["Excellent"],
                    concerns=[],
                    interview_priority=InterviewPriority.HIGH,
                    detailed_notes="Outstanding",
                ),
                Evaluation(
                    candidate_name="average_candidate",
                    job_name="test_job",
                    overall_score=70,
                    recommendation=RecommendationType.MAYBE,
                    strengths=["OK"],
                    concerns=["Some issues"],
                    interview_priority=InterviewPriority.MEDIUM,
                    detailed_notes="Average",
                ),
            ]

            # Test that display doesn't crash (we can't easily test output)
            try:
                generator.display_terminal_ranking(evaluations, "test_job")
                success = True
            except Exception:
                success = False

            assert success
