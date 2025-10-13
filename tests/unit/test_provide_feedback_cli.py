import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from candidate_reviewer import cli


def _setup_minimal_job(tmp_path: Path):
    # Create minimal data structure
    base = tmp_path / "data"
    (base / "jobs" / "j1").mkdir(parents=True, exist_ok=True)
    (base / "candidates" / "j1" / "john_doe").mkdir(parents=True, exist_ok=True)
    (base / "output" / "j1").mkdir(parents=True, exist_ok=True)

    # Minimal job_description
    (base / "jobs" / "j1" / "job_description.txt").write_text("desc")

    # Minimal evaluation required by provide_feedback
    eval_path = base / "candidates" / "j1" / "john_doe" / "evaluation.json"
    from datetime import datetime

    evaluation = {
        "evaluation_id": "eval-1",
        "candidate_name": "john_doe",
        "job_name": "j1",
        "overall_score": 60,
        "recommendation": "MAYBE",
        "interview_priority": "LOW",
        "strengths": ["s1", "s2"],
        "concerns": ["c1", "c2"],
        "detailed_notes": "notes",
        "timestamp": datetime.now().isoformat(),
    }
    eval_path.write_text(json.dumps(evaluation))

    return base


@pytest.fixture(autouse=True)
def _chdir_tmp(monkeypatch, tmp_path):
    # Ensure CLI uses the tmp data dir
    monkeypatch.chdir(tmp_path)
    # Minimal env to satisfy config validation
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
    monkeypatch.setenv("BASE_DATA_PATH", str(tmp_path / "data"))
    return tmp_path


def test_provide_feedback_resolves_numeric_job_and_interactive(monkeypatch, tmp_path):
    base = _setup_minimal_job(tmp_path)

    # Verify the job directory structure was created
    assert (base / "jobs" / "j1").exists(), "Job directory should exist"
    assert (
        base / "jobs" / "j1" / "job_description.txt"
    ).exists(), "Job description should exist"

    runner = CliRunner()

    # list-jobs depends on actual jobs dir; we won't call it directly here
    # but numeric resolution expects jobs to be under data/jobs sorted order
    # and our single job is 'j1', so selecting 1 should resolve to j1

    result = runner.invoke(
        cli,
        [
            "provide-feedback",
            "1",  # numeric job id -> j1
            "john_doe",
            "Prefilled feedback",
        ],
        input="y\n3\n\n",  # confirm candidate, select MAYBE (3), keep prefilled notes (Enter)
        env={"BASE_DATA_PATH": str(base), "OPENAI_API_KEY": "sk-test-123"},
    )

    assert result.exit_code == 0, result.output
    # Should run to completion with interactive prompts


def test_provide_feedback_accepts_accented_name_and_confirms(monkeypatch, tmp_path):
    base = _setup_minimal_job(tmp_path)

    # Verify the job directory structure was created
    assert (base / "jobs" / "j1").exists(), "Job directory should exist"

    runner = CliRunner()

    # Use human-readable name with spaces/accents that maps to john_doe
    # We simulate confirmation by sending 'y' to stdin
    result = runner.invoke(
        cli,
        [
            "provide-feedback",
            "1",
            "Jõhn Dóe",
            "Notes",
        ],
        input="y\n2\n\n",  # confirm candidate match, select YES (2), keep notes (Enter)
        env={"BASE_DATA_PATH": str(base), "OPENAI_API_KEY": "sk-test-123"},
    )

    # Should succeed with interactive prompts
    assert result.exit_code == 0, result.output
