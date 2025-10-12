"""Data models for AI Job Candidate Reviewer."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class RecommendationType(Enum):
    """Recommendation types for candidate evaluation."""

    STRONG_YES = "STRONG_YES"
    YES = "YES"
    MAYBE = "MAYBE"
    NO = "NO"
    STRONG_NO = "STRONG_NO"


class InterviewPriority(Enum):
    """Interview priority levels."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class JobContext:
    """Context information for a job position."""

    name: str
    description: str
    ideal_candidate: Optional[str] = None
    warning_flags: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "ideal_candidate": self.ideal_candidate,
            "warning_flags": self.warning_flags,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "JobContext":
        """Create instance from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            ideal_candidate=data.get("ideal_candidate"),
            warning_flags=data.get("warning_flags"),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now().isoformat())
            ),
        )


@dataclass
class Candidate:
    """Candidate information and materials."""

    name: str
    resume_text: str
    cover_letter: Optional[str] = None
    application: Optional[str] = None
    file_paths: Dict[str, str] = field(default_factory=dict)  # file_type -> path
    processed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "resume_text": self.resume_text,
            "cover_letter": self.cover_letter,
            "application": self.application,
            "file_paths": self.file_paths,
            "processed_at": self.processed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Candidate":
        """Create instance from dictionary."""
        return cls(
            name=data["name"],
            resume_text=data["resume_text"],
            cover_letter=data.get("cover_letter"),
            application=data.get("application"),
            file_paths=data.get("file_paths", {}),
            processed_at=datetime.fromisoformat(
                data.get("processed_at", datetime.now().isoformat())
            ),
        )


@dataclass
class Evaluation:
    """AI evaluation of a candidate."""

    candidate_name: str
    job_name: str
    overall_score: int  # 0-100
    recommendation: RecommendationType
    strengths: List[str]
    concerns: List[str]
    interview_priority: InterviewPriority
    detailed_notes: str
    timestamp: datetime = field(default_factory=datetime.now)
    ai_insights_used: Optional[str] = None  # Insights applied during evaluation
    evaluation_id: str = field(
        default_factory=lambda: f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "evaluation_id": self.evaluation_id,
            "candidate_name": self.candidate_name,
            "job_name": self.job_name,
            "overall_score": self.overall_score,
            "recommendation": self.recommendation.value,
            "strengths": self.strengths,
            "concerns": self.concerns,
            "interview_priority": self.interview_priority.value,
            "detailed_notes": self.detailed_notes,
            "timestamp": self.timestamp.isoformat(),
            "ai_insights_used": self.ai_insights_used,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Evaluation":
        """Create instance from dictionary."""
        return cls(
            evaluation_id=data.get(
                "evaluation_id", f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ),
            candidate_name=data["candidate_name"],
            job_name=data["job_name"],
            overall_score=data["overall_score"],
            recommendation=RecommendationType(data["recommendation"]),
            strengths=data["strengths"],
            concerns=data["concerns"],
            interview_priority=InterviewPriority(data["interview_priority"]),
            detailed_notes=data["detailed_notes"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ai_insights_used=data.get("ai_insights_used"),
        )


@dataclass
class HumanFeedback:
    """Human feedback on an AI evaluation."""

    evaluation_id: str
    human_recommendation: RecommendationType
    human_score: Optional[int] = None  # 0-100, optional
    feedback_notes: str = ""
    specific_corrections: Dict[str, str] = field(
        default_factory=dict
    )  # field -> corrected_value
    timestamp: datetime = field(default_factory=datetime.now)
    feedback_id: str = field(
        default_factory=lambda: f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "feedback_id": self.feedback_id,
            "evaluation_id": self.evaluation_id,
            "human_recommendation": self.human_recommendation.value,
            "human_score": self.human_score,
            "feedback_notes": self.feedback_notes,
            "specific_corrections": self.specific_corrections,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "HumanFeedback":
        """Create instance from dictionary."""
        return cls(
            feedback_id=data.get(
                "feedback_id", f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ),
            evaluation_id=data["evaluation_id"],
            human_recommendation=RecommendationType(data["human_recommendation"]),
            human_score=data.get("human_score"),
            feedback_notes=data.get("feedback_notes", ""),
            specific_corrections=data.get("specific_corrections", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class JobInsights:
    """AI-generated insights from feedback patterns for a job."""

    job_name: str
    generated_insights: str  # AI-generated insights from feedback patterns
    feedback_count: int
    last_updated: datetime = field(default_factory=datetime.now)
    effectiveness_metrics: Dict[str, float] = field(
        default_factory=dict
    )  # accuracy improvements, etc.
    insights_id: str = field(
        default_factory=lambda: f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "insights_id": self.insights_id,
            "job_name": self.job_name,
            "generated_insights": self.generated_insights,
            "feedback_count": self.feedback_count,
            "last_updated": self.last_updated.isoformat(),
            "effectiveness_metrics": self.effectiveness_metrics,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "JobInsights":
        """Create instance from dictionary."""
        return cls(
            insights_id=data.get(
                "insights_id", f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ),
            job_name=data["job_name"],
            generated_insights=data["generated_insights"],
            feedback_count=data["feedback_count"],
            last_updated=datetime.fromisoformat(data["last_updated"]),
            effectiveness_metrics=data.get("effectiveness_metrics", {}),
        )


@dataclass
class FeedbackRecord:
    """Complete record of feedback and associated evaluation."""

    candidate_name: str
    job_name: str
    original_evaluation: Evaluation
    human_feedback: HumanFeedback
    insights_generated: Optional[str] = None
    record_id: str = field(
        default_factory=lambda: f"record_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "record_id": self.record_id,
            "candidate_name": self.candidate_name,
            "job_name": self.job_name,
            "original_evaluation": self.original_evaluation.to_dict(),
            "human_feedback": self.human_feedback.to_dict(),
            "insights_generated": self.insights_generated,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "FeedbackRecord":
        """Create instance from dictionary."""
        return cls(
            record_id=data.get(
                "record_id", f"record_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ),
            candidate_name=data["candidate_name"],
            job_name=data["job_name"],
            original_evaluation=Evaluation.from_dict(data["original_evaluation"]),
            human_feedback=HumanFeedback.from_dict(data["human_feedback"]),
            insights_generated=data.get("insights_generated"),
        )


@dataclass
class JobSetupResult:
    """Result of job setup operation."""

    success: bool
    job_name: str
    message: str
    job_context: Optional[JobContext] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class ProcessingResult:
    """Result of candidate processing operation."""

    success: bool
    job_name: str
    processed_candidates: List[str] = field(default_factory=list)
    failed_candidates: List[str] = field(default_factory=list)
    evaluations: List[Evaluation] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class DisplayResult:
    """Result of candidate display operation."""

    success: bool
    job_name: str
    evaluations: List[Evaluation] = field(default_factory=list)
    message: str = ""


@dataclass
class ConnectionResult:
    """Result of API connection test."""

    success: bool
    message: str
    response_time_ms: Optional[float] = None
    model_info: Optional[str] = None


@dataclass
class APIResponse:
    """Response from OpenAI API."""

    success: bool
    content: str
    error_message: Optional[str] = None
    usage_info: Optional[Dict] = None
    response_time_ms: Optional[float] = None


@dataclass
class CandidateFiles:
    """Files associated with a candidate."""

    candidate_name: str
    resume_path: Optional[str] = None
    cover_letter_path: Optional[str] = None
    application_path: Optional[str] = None

    def get_file_paths(self) -> Dict[str, str]:
        """Get non-None file paths as dictionary."""
        paths = {}
        if self.resume_path:
            paths["resume"] = self.resume_path
        if self.cover_letter_path:
            paths["cover_letter"] = self.cover_letter_path
        if self.application_path:
            paths["application"] = self.application_path
        return paths


@dataclass
class JobFiles:
    """Files associated with a job setup."""

    job_name: str
    job_description_path: Optional[str] = None
    ideal_candidate_path: Optional[str] = None
    warning_flags_path: Optional[str] = None
