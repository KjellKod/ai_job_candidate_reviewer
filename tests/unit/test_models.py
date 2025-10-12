"""Unit tests for data models."""

from datetime import datetime
import pytest

from models import (
    JobContext,
    Candidate,
    Evaluation,
    HumanFeedback,
    JobInsights,
    RecommendationType,
    InterviewPriority,
)


class TestJobContext:
    """Test JobContext model."""

    def test_creation_with_required_fields(self):
        """Test creating JobContext with required fields."""
        job = JobContext(
            name="software_engineer", description="Python developer position"
        )

        assert job.name == "software_engineer"
        assert job.description == "Python developer position"
        assert job.ideal_candidate is None
        assert job.warning_flags is None
        assert isinstance(job.created_at, datetime)

    def test_creation_with_all_fields(self):
        """Test creating JobContext with all fields."""
        job = JobContext(
            name="software_engineer",
            description="Python developer position",
            ideal_candidate="5+ years Python experience",
            warning_flags="No remote work experience",
        )

        assert job.ideal_candidate == "5+ years Python experience"
        assert job.warning_flags == "No remote work experience"

    def test_to_dict_conversion(self):
        """Test converting JobContext to dictionary."""
        job = JobContext(name="test_job", description="Test description")

        data = job.to_dict()

        assert data["name"] == "test_job"
        assert data["description"] == "Test description"
        assert "created_at" in data

    def test_from_dict_conversion(self):
        """Test creating JobContext from dictionary."""
        data = {
            "name": "test_job",
            "description": "Test description",
            "ideal_candidate": "Test ideal",
            "warning_flags": "Test warnings",
            "created_at": "2024-01-01T12:00:00",
        }

        job = JobContext.from_dict(data)

        assert job.name == "test_job"
        assert job.description == "Test description"
        assert job.ideal_candidate == "Test ideal"
        assert job.warning_flags == "Test warnings"


class TestCandidate:
    """Test Candidate model."""

    def test_creation_with_required_fields(self):
        """Test creating Candidate with required fields."""
        candidate = Candidate(
            name="john_doe", resume_text="Software engineer with 5 years experience"
        )

        assert candidate.name == "john_doe"
        assert candidate.resume_text == "Software engineer with 5 years experience"
        assert candidate.cover_letter is None
        assert candidate.application is None
        assert isinstance(candidate.processed_at, datetime)

    def test_to_dict_conversion(self):
        """Test converting Candidate to dictionary."""
        candidate = Candidate(name="john_doe", resume_text="Test resume")

        data = candidate.to_dict()

        assert data["name"] == "john_doe"
        assert data["resume_text"] == "Test resume"
        assert "processed_at" in data


class TestEvaluation:
    """Test Evaluation model."""

    def test_creation_with_required_fields(self):
        """Test creating Evaluation with required fields."""
        evaluation = Evaluation(
            candidate_name="john_doe",
            job_name="software_engineer",
            overall_score=85,
            recommendation=RecommendationType.YES,
            strengths=["Strong Python skills", "Good communication"],
            concerns=["Limited leadership experience"],
            interview_priority=InterviewPriority.HIGH,
            detailed_notes="Solid candidate with good technical skills",
        )

        assert evaluation.candidate_name == "john_doe"
        assert evaluation.job_name == "software_engineer"
        assert evaluation.overall_score == 85
        assert evaluation.recommendation == RecommendationType.YES
        assert len(evaluation.strengths) == 2
        assert len(evaluation.concerns) == 1
        assert evaluation.interview_priority == InterviewPriority.HIGH
        assert isinstance(evaluation.timestamp, datetime)
        assert evaluation.evaluation_id.startswith("eval_")

    def test_to_dict_conversion(self):
        """Test converting Evaluation to dictionary."""
        evaluation = Evaluation(
            candidate_name="john_doe",
            job_name="test_job",
            overall_score=75,
            recommendation=RecommendationType.MAYBE,
            strengths=["Test strength"],
            concerns=["Test concern"],
            interview_priority=InterviewPriority.MEDIUM,
            detailed_notes="Test notes",
        )

        data = evaluation.to_dict()

        assert data["candidate_name"] == "john_doe"
        assert data["overall_score"] == 75
        assert data["recommendation"] == "MAYBE"
        assert data["interview_priority"] == "MEDIUM"
        assert "timestamp" in data
        assert "evaluation_id" in data

    def test_from_dict_conversion(self):
        """Test creating Evaluation from dictionary."""
        data = {
            "candidate_name": "john_doe",
            "job_name": "test_job",
            "overall_score": 80,
            "recommendation": "YES",
            "strengths": ["Skill 1", "Skill 2"],
            "concerns": ["Concern 1"],
            "interview_priority": "HIGH",
            "detailed_notes": "Good candidate",
            "timestamp": "2024-01-01T12:00:00",
        }

        evaluation = Evaluation.from_dict(data)

        assert evaluation.candidate_name == "john_doe"
        assert evaluation.overall_score == 80
        assert evaluation.recommendation == RecommendationType.YES
        assert evaluation.interview_priority == InterviewPriority.HIGH


class TestHumanFeedback:
    """Test HumanFeedback model."""

    def test_creation_with_required_fields(self):
        """Test creating HumanFeedback with required fields."""
        feedback = HumanFeedback(
            evaluation_id="eval_123",
            human_recommendation=RecommendationType.STRONG_YES,
            feedback_notes="Excellent candidate, hire immediately",
        )

        assert feedback.evaluation_id == "eval_123"
        assert feedback.human_recommendation == RecommendationType.STRONG_YES
        assert feedback.feedback_notes == "Excellent candidate, hire immediately"
        assert feedback.human_score is None
        assert isinstance(feedback.timestamp, datetime)
        assert feedback.feedback_id.startswith("feedback_")

    def test_to_dict_conversion(self):
        """Test converting HumanFeedback to dictionary."""
        feedback = HumanFeedback(
            evaluation_id="eval_123",
            human_recommendation=RecommendationType.NO,
            human_score=30,
            feedback_notes="Not a good fit",
        )

        data = feedback.to_dict()

        assert data["evaluation_id"] == "eval_123"
        assert data["human_recommendation"] == "NO"
        assert data["human_score"] == 30
        assert "timestamp" in data
        assert "feedback_id" in data
