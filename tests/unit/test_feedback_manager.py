"""Unit tests for feedback manager."""

import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from feedback_manager import FeedbackManager
from config import Config
from ai_client import AIClient
from models import (
    HumanFeedback,
    JobInsights,
    FeedbackRecord,
    Evaluation,
    JobContext,
    Candidate,
    RecommendationType,
    InterviewPriority,
)


class TestFeedbackManager:
    """Test feedback management functionality."""

    def test_initialization(self):
        """Test feedback manager initialization."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            ai_client = Mock(spec=AIClient)
            manager = FeedbackManager(config, ai_client)

            assert manager.config == config
            assert manager.ai_client == ai_client

    def test_collect_feedback_creates_record(self):
        """Test that collecting feedback creates proper records."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup config with temp directory
            with patch.dict(os.environ, {"BASE_DATA_PATH": temp_dir}, clear=True):
                config = Config()
                ai_client = Mock(spec=AIClient)
                manager = FeedbackManager(config, ai_client)

                # Create test job and candidate directories
                job_name = "test_job"
                candidate_name = "john_doe"
                
                candidate_dir = Path(config.get_candidate_path(job_name, candidate_name))
                candidate_dir.mkdir(parents=True, exist_ok=True)

                # Create a test evaluation file
                evaluation = Evaluation(
                    candidate_name=candidate_name,
                    job_name=job_name,
                    overall_score=75,
                    recommendation=RecommendationType.YES,
                    strengths=["Good skills"],
                    concerns=["Some issues"],
                    interview_priority=InterviewPriority.MEDIUM,
                    detailed_notes="Test evaluation",
                )

                eval_path = candidate_dir / "evaluation.json"
                with open(eval_path, "w") as f:
                    json.dump(evaluation.to_dict(), f)

                # Create test feedback
                feedback = HumanFeedback(
                    evaluation_id=evaluation.evaluation_id,
                    human_recommendation=RecommendationType.STRONG_YES,
                    feedback_notes="Actually excellent candidate",
                    human_score=90,
                )

                # Collect feedback
                manager.collect_feedback(job_name, candidate_name, feedback)

                # Verify feedback file was created
                feedback_path = candidate_dir / "feedback.json"
                assert feedback_path.exists()

                # Verify feedback content
                with open(feedback_path, "r") as f:
                    feedback_data = json.load(f)
                    assert feedback_data["candidate_name"] == candidate_name
                    assert feedback_data["human_feedback"]["human_recommendation"] == "STRONG_YES"

    def test_build_insights_insufficient_feedback(self):
        """Test that insights building requires sufficient feedback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"BASE_DATA_PATH": temp_dir}, clear=True):
                config = Config()
                ai_client = Mock(spec=AIClient)
                manager = FeedbackManager(config, ai_client)

                # Test with no feedback
                result = manager.build_insights("test_job")
                assert result is None

    def test_build_insights_with_sufficient_feedback(self):
        """Test insights generation with sufficient feedback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"BASE_DATA_PATH": temp_dir}, clear=True):
                config = Config()
                ai_client = Mock(spec=AIClient)
                ai_client.model = "gpt-4"
                ai_client.generate_insights.return_value = '{"test": "insights"}'
                
                manager = FeedbackManager(config, ai_client)

                job_name = "test_job"
                
                # Create job directory and context files
                job_dir = Path(config.get_job_path(job_name))
                job_dir.mkdir(parents=True, exist_ok=True)
                
                # Create job description file
                desc_file = job_dir / "job_description.pdf"
                desc_file.write_text("Test job description")

                # Create multiple feedback records
                candidates_dir = Path(config.candidates_path) / job_name
                candidates_dir.mkdir(parents=True, exist_ok=True)

                for i, candidate_name in enumerate(["john_doe", "jane_smith"]):
                    candidate_dir = candidates_dir / candidate_name
                    candidate_dir.mkdir(parents=True, exist_ok=True)

                    # Create evaluation
                    evaluation = Evaluation(
                        candidate_name=candidate_name,
                        job_name=job_name,
                        overall_score=70 + i * 10,
                        recommendation=RecommendationType.YES,
                        strengths=["Test strength"],
                        concerns=["Test concern"],
                        interview_priority=InterviewPriority.MEDIUM,
                        detailed_notes="Test notes",
                    )

                    # Create feedback
                    feedback = HumanFeedback(
                        evaluation_id=evaluation.evaluation_id,
                        human_recommendation=RecommendationType.STRONG_YES,
                        feedback_notes=f"Good candidate {i}",
                    )

                    record = FeedbackRecord(
                        candidate_name=candidate_name,
                        job_name=job_name,
                        original_evaluation=evaluation,
                        human_feedback=feedback,
                    )

                    # Save feedback record
                    feedback_path = candidate_dir / "feedback.json"
                    with open(feedback_path, "w") as f:
                        json.dump(record.to_dict(), f)

                # Mock file processor for job context loading
                with patch('feedback_manager.FileProcessor') as mock_processor:
                    mock_processor.return_value.extract_text_from_file.return_value = ("Test description", None)
                    
                    # Build insights
                    insights = manager.build_insights(job_name)

                    assert insights is not None
                    assert insights.job_name == job_name
                    assert insights.feedback_count == 2
                    assert '"test": "insights"' in insights.generated_insights

    def test_effectiveness_metrics_calculation(self):
        """Test calculation of effectiveness metrics."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            ai_client = Mock(spec=AIClient)
            manager = FeedbackManager(config, ai_client)

            # Create test feedback records with different agreement patterns
            records = []
            for i in range(3):
                evaluation = Evaluation(
                    candidate_name=f"candidate_{i}",
                    job_name="test_job",
                    overall_score=75,
                    recommendation=RecommendationType.YES if i < 2 else RecommendationType.NO,
                    strengths=["Test"],
                    concerns=["Test"],
                    interview_priority=InterviewPriority.MEDIUM,
                    detailed_notes="Test",
                )

                feedback = HumanFeedback(
                    evaluation_id=evaluation.evaluation_id,
                    human_recommendation=RecommendationType.YES,  # All human feedback is YES
                    feedback_notes="Test",
                )

                record = FeedbackRecord(
                    candidate_name=f"candidate_{i}",
                    job_name="test_job",
                    original_evaluation=evaluation,
                    human_feedback=feedback,
                )
                records.append(record)

            metrics = manager._calculate_effectiveness_metrics(records)

            # Should have 2/3 agreement (66.7%)
            assert abs(metrics["agreement_rate"] - (2/3)) < 0.01
            assert metrics["total_feedback"] == 3
            assert "last_calculated" in metrics
