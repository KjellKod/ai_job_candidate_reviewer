"""Unit tests for AI client."""

import json
from unittest.mock import Mock, patch

import pytest

from ai_client import AIClient
from models import (
    APIResponse,
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

    @pytest.mark.parametrize(
        "model,expected_param",
        [
            ("gpt-5", "max_completion_tokens"),
            ("gpt-5-turbo", "max_completion_tokens"),
            ("gpt-4o", "max_tokens"),
            ("gpt-4", "max_tokens"),
        ],
    )
    def test_model_parameter_selection(self, model, expected_param):
        """Ensure correct token-limit parameter and value for each model variant."""
        client = AIClient("test_key", model)

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
            messages = [{"role": "user", "content": "test"}]
            client._make_request(messages)

            call_args = mock_create.call_args
            call_kwargs = call_args.kwargs

            # Verify the correct parameter is present with the correct value
            assert expected_param in call_kwargs
            assert call_kwargs[expected_param] == 2000

            # Verify the opposite parameter is not present
            opposite = (
                "max_tokens"
                if expected_param == "max_completion_tokens"
                else "max_completion_tokens"
            )
            assert opposite not in call_kwargs

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

    def test_evaluation_includes_warning_flags_in_openai_prompt(self):
        """Ensure warning flags from JobContext appear in the OpenAI prompt payload."""
        client = AIClient("test_key", "gpt-4o")

        job_context = JobContext(
            name="job",
            description="desc",
            ideal_candidate=None,
            warning_flags="No remote work",
        )

        candidate = Candidate(name="alice", resume_text="resume text")

        captured = {}

        def fake_make_request(messages):
            captured["messages"] = messages
            return APIResponse(
                success=True,
                content=json.dumps(
                    {
                        "overall_score": 75,
                        "recommendation": "YES",
                        "strengths": ["x"],
                        "concerns": ["y"],
                        "interview_priority": "MEDIUM",
                        "detailed_notes": "ok",
                        "insights_applied": None,
                    }
                ),
            )

        with patch.object(client, "_make_request", side_effect=fake_make_request):
            client.evaluate_candidate(job_context, candidate)

        user_content = captured["messages"][1]["content"]
        assert "WARNING FLAGS:" in user_content
        assert "No remote work" in user_content

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
