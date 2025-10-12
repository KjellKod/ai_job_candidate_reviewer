"""Unit tests for AI client."""

import json
from unittest.mock import Mock, patch

import pytest

from ai_client import AIClient
from models import (
    Candidate,
    Evaluation,
    InterviewPriority,
    JobContext,
    RecommendationType,
)


class TestAIClient:
    """Test AI client functionality."""

    def test_initialization(self):
        """Test AI client initialization."""
        client = AIClient("test_key", "gpt-4o")

        assert client.api_key == "test_key"
        assert client.model == "gpt-4o"
        assert client.client is not None

    def test_gpt5_parameter_handling(self):
        """Test that GPT-5 models use correct parameters."""
        client = AIClient("test_key", "gpt-5")

        # Mock the OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            '{"overall_score": 75, "recommendation": "YES", "strengths": ["test"], "concerns": ["test"], "interview_priority": "MEDIUM", "detailed_notes": "test"}'
        )
        mock_response.usage = None

        with patch.object(
            client.client.chat.completions, "create", return_value=mock_response
        ) as mock_create:
            # Test that GPT-5 uses max_completion_tokens
            messages = [{"role": "user", "content": "test"}]
            client._make_request(messages)

            # Verify the correct parameter was used
            call_args = mock_create.call_args
            assert "max_completion_tokens" in call_args.kwargs
            assert "max_tokens" not in call_args.kwargs

    def test_gpt4_parameter_handling(self):
        """Test that GPT-4 models use correct parameters."""
        client = AIClient("test_key", "gpt-4o")

        # Mock the OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            '{"overall_score": 75, "recommendation": "YES", "strengths": ["test"], "concerns": ["test"], "interview_priority": "MEDIUM", "detailed_notes": "test"}'
        )
        mock_response.usage = None

        with patch.object(
            client.client.chat.completions, "create", return_value=mock_response
        ) as mock_create:
            # Test that GPT-4 uses max_tokens
            messages = [{"role": "user", "content": "test"}]
            client._make_request(messages)

            # Verify the correct parameter was used
            call_args = mock_create.call_args
            assert "max_tokens" in call_args.kwargs
            assert "max_completion_tokens" not in call_args.kwargs

    def test_evaluation_prompt_building(self):
        """Test evaluation prompt construction."""
        client = AIClient("test_key", "gpt-4o")

        job_context = JobContext(
            name="test_job",
            description="Test job description",
            ideal_candidate="Test ideal candidate",
            warning_flags="Test warning flags",
        )

        candidate = Candidate(
            name="test_candidate",
            resume_text="Test resume",
            cover_letter="Test cover letter",
            application="Test application",
        )

        insights = "Test insights"

        prompt = client._build_evaluation_prompt(job_context, candidate, insights)

        assert "Test job description" in prompt
        assert "Test ideal candidate" in prompt
        assert "Test warning flags" in prompt
        assert "Test resume" in prompt
        assert "Test cover letter" in prompt
        assert "Test application" in prompt
        assert "Test insights" in prompt
        assert "JSON format" in prompt

    def test_evaluation_response_parsing(self):
        """Test parsing of evaluation responses."""
        client = AIClient("test_key", "gpt-4o")

        # Test valid JSON response
        valid_response = json.dumps(
            {
                "overall_score": 85,
                "recommendation": "YES",
                "strengths": ["Strong skills", "Good experience"],
                "concerns": ["Minor issue"],
                "interview_priority": "HIGH",
                "detailed_notes": "Good candidate",
                "insights_applied": "Applied insights",
            }
        )

        parsed = client._parse_evaluation_response(valid_response)

        assert parsed["overall_score"] == 85
        assert parsed["recommendation"] == "YES"
        assert len(parsed["strengths"]) == 2
        assert len(parsed["concerns"]) == 1
        assert parsed["interview_priority"] == "HIGH"

    def test_evaluation_response_parsing_invalid_json(self):
        """Test parsing of invalid JSON responses."""
        client = AIClient("test_key", "gpt-4o")

        # Test invalid JSON
        invalid_response = "This is not JSON"

        parsed = client._parse_evaluation_response(invalid_response)

        assert parsed["overall_score"] == 0
        assert parsed["recommendation"] == "NO"
        assert "Failed to parse" in parsed["concerns"][0]

    def test_evaluation_response_validation(self):
        """Test validation of evaluation response values."""
        client = AIClient("test_key", "gpt-4o")

        # Test with invalid enum values
        invalid_response = json.dumps(
            {
                "overall_score": 150,  # Too high
                "recommendation": "INVALID_REC",  # Invalid enum
                "strengths": ["test"],
                "concerns": ["test"],
                "interview_priority": "INVALID_PRIORITY",  # Invalid enum
                "detailed_notes": "test",
            }
        )

        parsed = client._parse_evaluation_response(invalid_response)

        assert parsed["overall_score"] == 100  # Clamped to max
        assert parsed["recommendation"] == "NO"  # Default for invalid
        assert parsed["interview_priority"] == "LOW"  # Default for invalid
