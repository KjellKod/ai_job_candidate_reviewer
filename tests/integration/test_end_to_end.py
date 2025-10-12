"""Integration tests for end-to-end pipeline functionality."""

import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from candidate_reviewer import CandidateReviewer
from config import Config
from models import (
    JobSetupResult,
    ProcessingResult,
    RecommendationType,
    InterviewPriority,
)


class TestEndToEndPipeline:
    """Test complete pipeline functionality."""

    def test_complete_job_setup_and_processing_pipeline(self):
        """Test the complete pipeline from job setup to candidate processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup config with temp directory
            with patch.dict(os.environ, {
                "BASE_DATA_PATH": temp_dir,
                "OPENAI_API_KEY": "sk-test123"
            }, clear=True):
                config = Config()
                
                # Mock the AI client to avoid real API calls
                with patch('candidate_reviewer.AIClient') as mock_ai_client_class:
                    mock_ai_client = Mock()
                    mock_ai_client.evaluate_candidate.return_value = Mock(
                        candidate_name="john_doe",
                        job_name="test_job",
                        overall_score=85,
                        recommendation=RecommendationType.YES,
                        strengths=["Strong technical skills", "Good communication"],
                        concerns=["Limited leadership experience"],
                        interview_priority=InterviewPriority.HIGH,
                        detailed_notes="Solid candidate with good potential",
                        timestamp=Mock(),
                        ai_insights_used=None,
                        evaluation_id="test_eval_123"
                    )
                    mock_ai_client_class.return_value = mock_ai_client

                    # Mock connection tester
                    with patch('candidate_reviewer.OpenAIConnectionTester') as mock_tester:
                        mock_tester.return_value.model = "gpt-4"
                        
                        reviewer = CandidateReviewer(config)

                        # Step 1: Setup job with direct paths
                        job_name = "software_engineer"
                        
                        # Create test job description file
                        job_desc_file = Path(temp_dir) / "job_description.pdf"
                        job_desc_file.write_text("Software Engineer Position\\nPython development role")
                        
                        # Create ideal candidate file
                        ideal_file = Path(temp_dir) / "ideal_candidate.txt"
                        ideal_file.write_text("5+ years Python experience\\nStrong problem-solving skills")

                        # Setup job using direct paths
                        setup_result = reviewer.setup_job_with_paths(
                            job_name=job_name,
                            job_description_path=str(job_desc_file),
                            ideal_candidate_path=str(ideal_file),
                        )

                        assert setup_result.success
                        assert setup_result.job_context is not None
                        assert setup_result.job_context.name == job_name

                        # Verify job files were organized
                        job_dir = Path(config.get_job_path(job_name))
                        assert job_dir.exists()
                        assert (job_dir / "job_description.pdf").exists()
                        assert (job_dir / "ideal_candidate.txt").exists()

                        # Step 2: Process a single candidate
                        candidate_name = "john_doe"
                        
                        # Create test resume file
                        resume_file = Path(temp_dir) / "john_doe_resume.pdf"
                        resume_file.write_text("John Doe Resume\\nSoftware Engineer\\n5 years Python experience")
                        
                        # Create test cover letter
                        cover_file = Path(temp_dir) / "john_doe_cover.pdf" 
                        cover_file.write_text("Dear Hiring Manager\\nI am interested in the position...")

                        # Process single candidate
                        process_result = reviewer.process_single_candidate(
                            job_name=job_name,
                            candidate_name=candidate_name,
                            resume_path=str(resume_file),
                            cover_letter_path=str(cover_file),
                        )

                        assert process_result.success
                        assert len(process_result.processed_candidates) == 1
                        assert candidate_name in process_result.processed_candidates
                        assert len(process_result.evaluations) == 1

                        # Verify candidate files were organized
                        candidate_dir = Path(config.get_candidate_path(job_name, candidate_name))
                        assert candidate_dir.exists()
                        assert (candidate_dir / "resume.pdf").exists()
                        assert (candidate_dir / "cover_letter.pdf").exists()
                        assert (candidate_dir / "evaluation.json").exists()

                        # Step 3: Display candidates
                        display_result = reviewer.show_candidates(job_name)
                        
                        assert display_result.success
                        assert len(display_result.evaluations) == 1
                        assert display_result.evaluations[0].candidate_name == candidate_name

                        # Verify output files were generated
                        output_dir = Path(config.get_output_path(job_name))
                        assert output_dir.exists()
                        
                        # Should have CSV and HTML files
                        csv_files = list(output_dir.glob("candidate_scores_*.csv"))
                        html_files = list(output_dir.glob("detailed_report_*.html"))
                        
                        assert len(csv_files) > 0
                        assert len(html_files) > 0

    def test_job_setup_from_intake_directory(self):
        """Test job setup using intake directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {
                "BASE_DATA_PATH": temp_dir,
                "OPENAI_API_KEY": "sk-test123"
            }, clear=True):
                config = Config()
                
                with patch('candidate_reviewer.OpenAIConnectionTester') as mock_tester:
                    mock_tester.return_value.model = "gpt-4"
                    
                    reviewer = CandidateReviewer(config)

                    # Create intake directory with job files
                    intake_dir = Path(config.intake_path)
                    intake_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create job files in intake
                    (intake_dir / "job_description.pdf").write_text("Test job description")
                    (intake_dir / "ideal_candidate.txt").write_text("Test ideal candidate")
                    (intake_dir / "warning_flags.txt").write_text("Test warning flags")

                    # Setup job from intake
                    job_name = "test_job_intake"
                    setup_result = reviewer.setup_job(job_name)

                    assert setup_result.success
                    assert setup_result.job_context.ideal_candidate is not None
                    assert setup_result.job_context.warning_flags is not None

    def test_candidate_processing_from_intake_directory(self):
        """Test candidate processing using intake directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {
                "BASE_DATA_PATH": temp_dir,
                "OPENAI_API_KEY": "sk-test123"
            }, clear=True):
                config = Config()
                
                # Mock AI client
                with patch('candidate_reviewer.AIClient') as mock_ai_client_class:
                    mock_ai_client = Mock()
                    mock_ai_client.evaluate_candidate.return_value = Mock(
                        candidate_name="jane_smith",
                        job_name="test_job",
                        overall_score=75,
                        recommendation=RecommendationType.MAYBE,
                        strengths=["Good skills"],
                        concerns=["Needs experience"],
                        interview_priority=InterviewPriority.MEDIUM,
                        detailed_notes="Decent candidate",
                        timestamp=Mock(),
                        ai_insights_used=None,
                        evaluation_id="test_eval_456"
                    )
                    mock_ai_client_class.return_value = mock_ai_client

                    with patch('candidate_reviewer.OpenAIConnectionTester') as mock_tester:
                        mock_tester.return_value.model = "gpt-4"
                        
                        reviewer = CandidateReviewer(config)

                        # First setup a job
                        job_name = "test_job_candidates"
                        job_desc_file = Path(temp_dir) / "job_description.pdf"
                        job_desc_file.write_text("Test job")
                        
                        setup_result = reviewer.setup_job_with_paths(
                            job_name=job_name,
                            job_description_path=str(job_desc_file),
                        )
                        assert setup_result.success

                        # Create candidate files in intake
                        intake_dir = Path(config.intake_path)
                        intake_dir.mkdir(parents=True, exist_ok=True)
                        
                        (intake_dir / "resume_jane_smith.pdf").write_text("Jane Smith Resume")
                        (intake_dir / "coverletter_jane_smith.pdf").write_text("Jane Cover Letter")
                        (intake_dir / "application_jane_smith.txt").write_text("Jane Application")

                        # Mock file processor to avoid actual file operations
                        with patch.object(reviewer.file_processor, 'process_candidate_intake') as mock_process:
                            from models import CandidateFiles
                            mock_process.return_value = ([
                                CandidateFiles(
                                    candidate_name="jane_smith",
                                    resume_path=str(intake_dir / "resume_jane_smith.pdf"),
                                    cover_letter_path=str(intake_dir / "coverletter_jane_smith.pdf"),
                                    application_path=str(intake_dir / "application_jane_smith.txt"),
                                )
                            ], [])

                            with patch.object(reviewer.file_processor, 'organize_candidate_files') as mock_organize:
                                from models import Candidate
                                mock_organize.return_value = (
                                    Candidate(
                                        name="jane_smith",
                                        resume_text="Jane Smith Resume",
                                        cover_letter="Jane Cover Letter",
                                        application="Jane Application",
                                    ),
                                    []
                                )

                                # Process candidates from intake
                                process_result = reviewer.process_candidates(job_name)

                                assert process_result.success
                                assert len(process_result.processed_candidates) == 1
                                assert "jane_smith" in process_result.processed_candidates

    def test_error_handling_missing_job(self):
        """Test error handling when job doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {
                "BASE_DATA_PATH": temp_dir,
                "OPENAI_API_KEY": "sk-test123"
            }, clear=True):
                config = Config()
                
                with patch('candidate_reviewer.OpenAIConnectionTester') as mock_tester:
                    mock_tester.return_value.model = "gpt-4"
                    
                    reviewer = CandidateReviewer(config)

                    # Try to process candidates for non-existent job
                    result = reviewer.process_candidates("nonexistent_job")
                    
                    assert not result.success
                    assert "not found" in result.message.lower()

    def test_error_handling_missing_api_key(self):
        """Test error handling when API key is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {
                "BASE_DATA_PATH": temp_dir,
                # No OPENAI_API_KEY
            }, clear=True):
                config = Config()
                reviewer = CandidateReviewer(config)

                # Try to process candidates without API key
                result = reviewer.process_candidates("test_job")
                
                assert not result.success
                assert "api key" in result.message.lower()

    def test_list_jobs_functionality(self):
        """Test listing jobs functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {
                "BASE_DATA_PATH": temp_dir,
                "OPENAI_API_KEY": "sk-test123"
            }, clear=True):
                config = Config()
                
                with patch('candidate_reviewer.OpenAIConnectionTester') as mock_tester:
                    mock_tester.return_value.model = "gpt-4"
                    
                    reviewer = CandidateReviewer(config)

                    # Initially no jobs
                    jobs = reviewer.list_jobs()
                    assert len(jobs) == 0

                    # Create some job directories manually
                    jobs_dir = Path(config.jobs_path)
                    jobs_dir.mkdir(parents=True, exist_ok=True)
                    
                    (jobs_dir / "job1").mkdir()
                    (jobs_dir / "job2").mkdir()
                    (jobs_dir / "job3").mkdir()

                    # List jobs
                    jobs = reviewer.list_jobs()
                    assert len(jobs) == 3
                    assert "job1" in jobs
                    assert "job2" in jobs
                    assert "job3" in jobs
                    assert jobs == sorted(jobs)  # Should be sorted
