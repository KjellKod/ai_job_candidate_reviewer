"""AI client for candidate evaluation and insights generation."""

import json
import time
from typing import Dict, List, Optional

import openai
from openai import OpenAI

from models import (
    APIResponse,
    Candidate,
    Evaluation,
    InterviewPriority,
    JobContext,
    RecommendationType,
)


class AIClient:
    """AI client for candidate evaluation and insights generation."""

    def __init__(self, api_key: str, model: str):
        """Initialize AI client.

        Args:
            api_key: OpenAI API key
            model: Model name to use
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def evaluate_candidate(
        self,
        job_context: JobContext,
        candidate: Candidate,
        job_insights: Optional[str] = None,
        screening_filters: Optional[Dict] = None,
        verbose: bool = False,
    ) -> Evaluation:
        """Evaluate a candidate using AI.

        Args:
            job_context: Job context and requirements
            candidate: Candidate information and materials
            job_insights: Optional AI insights from previous feedback

        Returns:
            Evaluation object with AI assessment
        """
        prompt = self._build_evaluation_prompt(
            job_context, candidate, job_insights, screening_filters
        )

        if verbose:
            print("\n" + "=" * 80)
            print("🔍 VERBOSE: Full AI Prompt")
            print("=" * 80)
            print(prompt)
            print("=" * 80 + "\n")

        try:
            response = self._make_request(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert HR professional evaluating job "
                            "candidates. Provide thorough, fair, and structured "
                            "evaluations."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            if not response.success:
                # Return a default evaluation with error information
                return Evaluation(
                    candidate_name=candidate.name,
                    job_name=job_context.name,
                    overall_score=0,
                    recommendation=RecommendationType.NO,
                    strengths=[],
                    concerns=[f"API Error: {response.error_message}"],
                    interview_priority=InterviewPriority.LOW,
                    detailed_notes=(
                        f"Evaluation failed due to API error: "
                        f"{response.error_message}"
                    ),
                    ai_insights_used=job_insights,
                )

            # Parse the JSON response
            evaluation_data = self._parse_evaluation_response(response.content)

            # Deterministic enforcement of screening filters (post-processing)
            if screening_filters:
                try:
                    applied_filters: list[str] = []
                    # Prefer explicit rules_applied from the model
                    if isinstance(evaluation_data.get("rules_applied"), list):
                        applied_filters = [str(fid) for fid in evaluation_data.get("rules_applied")]
                    else:
                        # Fallback: parse from detailed_notes prefix "Failed filters: id1, id2"
                        notes = str(evaluation_data.get("detailed_notes", ""))
                        marker = "Failed filters:"
                        if marker in notes:
                            # take the first line after marker
                            first_line = notes.split("\n", 1)[0]
                            ids_part = first_line.split(marker, 1)[-1].strip().strip(". ")
                            # split by comma or space
                            applied_filters = [p.strip() for p in ids_part.split(",") if p.strip()]

                    if applied_filters:
                        # Build action map from screening_filters
                        items = screening_filters.get("filters", []) if isinstance(screening_filters, dict) else []
                        id_to_action = {str(f.get("id")): f.get("action", {}) for f in items}

                        forced_recommendation = None
                        cap_recommendation = None
                        total_deduction = 0

                        for fid in applied_filters:
                            action = id_to_action.get(fid, {})
                            if not isinstance(action, dict):
                                continue
                            if action.get("set_recommendation"):
                                forced_recommendation = action.get("set_recommendation")
                            if action.get("cap_recommendation"):
                                cap_recommendation = action.get("cap_recommendation")
                            if action.get("deduct_points") is not None:
                                try:
                                    total_deduction += int(action.get("deduct_points"))
                                except Exception:
                                    pass

                        # Apply score deduction
                        if isinstance(evaluation_data.get("overall_score"), (int, float)) and total_deduction > 0:
                            new_score = max(0, int(evaluation_data.get("overall_score")) - total_deduction)
                            evaluation_data["overall_score"] = new_score

                        # Apply recommendation overrides/caps
                        rec = str(evaluation_data.get("recommendation", "NO"))
                        order = ["STRONG_NO", "NO", "MAYBE", "YES", "STRONG_YES"]
                        if forced_recommendation:
                            evaluation_data["recommendation"] = forced_recommendation
                        elif cap_recommendation and rec in order:
                            # Cap if current is greater than cap
                            if cap_recommendation in order and order.index(rec) > order.index(cap_recommendation):
                                evaluation_data["recommendation"] = cap_recommendation

                        if verbose and (applied_filters or total_deduction > 0 or forced_recommendation or cap_recommendation):
                            print("\n" + "-"*80)
                            print("🔧 VERBOSE: Post-processing enforcement applied")
                            print(f"   Applied filter IDs: {applied_filters if applied_filters else '[]'}")
                            print(f"   Score deduction: {total_deduction}")
                            print(f"   Forced recommendation: {forced_recommendation}")
                            print(f"   Cap recommendation: {cap_recommendation}")
                            print(f"   Final score: {evaluation_data.get('overall_score')}")
                            print(f"   Final recommendation: {evaluation_data.get('recommendation')}")
                            print("-"*80 + "\n")
                except Exception:
                    # Do not fail evaluation on enforcement issues
                    pass

            if verbose:
                print("\n" + "=" * 80)
                print("🔍 VERBOSE: AI Response (Raw JSON)")
                print("=" * 80)
                print(response.content)
                print("=" * 80)
                print(
                    f"\nParsed rules_applied: {evaluation_data.get('rules_applied', 'NOT_PROVIDED')}"
                )
                print(f"Parsed overall_score: {evaluation_data.get('overall_score')}")
                print(f"Parsed recommendation: {evaluation_data.get('recommendation')}")
                print("=" * 80 + "\n")

            return Evaluation(
                candidate_name=candidate.name,
                job_name=job_context.name,
                overall_score=evaluation_data.get("overall_score", 0),
                recommendation=RecommendationType(
                    # standard Python dictionary pattern for safe retrieval with a default of "no"
                    evaluation_data.get("recommendation", "NO")
                ),
                strengths=evaluation_data.get("strengths", []),
                concerns=evaluation_data.get("concerns", []),
                interview_priority=InterviewPriority(
                    evaluation_data.get("interview_priority", "LOW")
                ),
                detailed_notes=evaluation_data.get("detailed_notes", ""),
                ai_insights_used=evaluation_data.get("insights_applied", job_insights),
            )

        except Exception as e:
            # Return error evaluation
            return Evaluation(
                candidate_name=candidate.name,
                job_name=job_context.name,
                overall_score=0,
                recommendation=RecommendationType.NO,
                strengths=[],
                concerns=[f"Evaluation Error: {str(e)}"],
                interview_priority=InterviewPriority.LOW,
                detailed_notes=f"Evaluation failed: {str(e)}",
                ai_insights_used=job_insights,
            )

    def generate_insights(
        self, job_context: JobContext, feedback_patterns: List[Dict]
    ) -> str:
        """Generate job-specific insights from feedback patterns.

        Args:
            job_context: Job context and requirements
            feedback_patterns: Aggregated feedback data

        Returns:
            Generated insights as JSON string
        """
        prompt = self._build_insights_prompt(job_context, feedback_patterns)

        try:
            response = self._make_request(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are an AI learning system that generates insights "
                            "from human feedback to improve candidate evaluations."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            if response.success:
                return response.content
            else:
                return json.dumps(
                    {
                        "evaluation_criteria_refinements": (
                            "Unable to generate insights due to API error"
                        ),
                        "strength_identification_patterns": "Error occurred",
                        "concern_identification_patterns": "Error occurred",
                        "scoring_calibration": "Error occurred",
                        "recommendation_logic": "Error occurred",
                    }
                )

        except Exception as e:
            return json.dumps(
                {
                    "evaluation_criteria_refinements": (
                        f"Error generating insights: {str(e)}"
                    ),
                    "strength_identification_patterns": "Error occurred",
                    "concern_identification_patterns": "Error occurred",
                    "scoring_calibration": "Error occurred",
                    "recommendation_logic": "Error occurred",
                }
            )

    def _make_request(self, messages: List[Dict]) -> APIResponse:
        """Make a request to OpenAI API with error handling.

        Args:
            messages: List of message dictionaries for the API

        Returns:
            APIResponse with result and metadata
        """
        start_time = time.time()

        try:
            # Handle different API parameters for different models
            request_params = {
                "model": self.model,
                "messages": messages,
                # this is "stable" setting when you need dynamic output without sacrificing coherence.
                # https://platform.openai.com/docs/api-reference/chat/create#chat-create-temperature
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            }

            # GPT-5 models use max_completion_tokens instead of max_tokens
            if self.model.startswith("gpt-5"):
                request_params["max_completion_tokens"] = 2000
            else:
                request_params["max_tokens"] = 2000

            response = self.client.chat.completions.create(**request_params)

            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            if response.choices and response.choices[0].message.content:
                return APIResponse(
                    success=True,
                    content=response.choices[0].message.content,
                    usage_info=response.usage.model_dump() if response.usage else None,
                    response_time_ms=response_time_ms,
                )
            else:
                return APIResponse(
                    success=False, content="", error_message="Empty response from API"
                )

        except openai.AuthenticationError as e:
            return APIResponse(
                success=False,
                content="",
                error_message=f"Authentication failed: {str(e)}",
            )
        except openai.RateLimitError as e:
            return APIResponse(
                success=False,
                content="",
                error_message=f"Rate limit exceeded: {str(e)}",
            )
        except openai.APIConnectionError as e:
            return APIResponse(
                success=False, content="", error_message=f"Connection error: {str(e)}"
            )
        except Exception as e:
            return APIResponse(
                success=False, content="", error_message=f"Unexpected error: {str(e)}"
            )

    def _build_evaluation_prompt(
        self,
        job_context: JobContext,
        candidate: Candidate,
        job_insights: Optional[str] = None,
        screening_filters: Optional[Dict] = None,
    ) -> str:
        """Build the evaluation prompt for a candidate.

        Args:
            job_context: Job context and requirements
            candidate: Candidate information
            job_insights: Optional AI insights from feedback

        Returns:
            Formatted prompt string
        """
        insights_section = ""
        if job_insights:
            insights_section = f"""
AI INSIGHTS FROM PREVIOUS FEEDBACK:
{job_insights}
Note: These insights were generated from human feedback on previous
evaluations for this role.
"""

        filters_section = ""
        if screening_filters and isinstance(screening_filters, dict):
            items = screening_filters.get("filters", [])
            if items:
                lines = [
                    "DECISION FILTERS (must enforce):",
                ]
                for f in items:
                    if not f.get("enabled", True):
                        continue
                    fid = f.get("id", "unknown")
                    when = f.get("when", "")
                    action = f.get("action", {})
                    actions = []
                    if action.get("set_recommendation"):
                        actions.append(
                            f"set_recommendation={action.get('set_recommendation')}"
                        )
                    if action.get("cap_recommendation"):
                        actions.append(
                            f"cap_recommendation={action.get('cap_recommendation')}"
                        )
                    if action.get("deduct_points") is not None:
                        actions.append(f"deduct_points={action.get('deduct_points')}")
                    lines.append(
                        f"- id: {fid}\n  when: {when}\n  action: {', '.join(actions) if actions else 'none'}"
                    )
                lines.append(
                    "You must apply these filters. If a filter condition is met: (1) apply the specified penalties, (2) set/cap the recommendation as specified, (3) list 'Failed filters: <ids>' at the top of detailed_notes, and (4) include 'rules_applied' in the JSON response."
                )
                filters_section = "\n" + "\n".join(lines) + "\n"

        # Global evaluation approach (applies to all jobs)
        evaluation_approach_section = """
EVALUATION APPROACH:
1. Resume is ground truth for experience verification
2. Application answers are self-reported claims - verify against resume
3. If application claims X years of experience/responsibility but resume doesn't show it, flag as "unverified claim"
4. For filters: only count verified evidence from resume, not self-reported application answers
"""

        return f"""You are evaluating job candidates. Analyze the following:

JOB DESCRIPTION:
{job_context.description}

IDEAL CANDIDATE PROFILE:
{job_context.ideal_candidate or "Not specified"}

WARNING FLAGS:
{job_context.warning_flags or "Not specified"}
{insights_section}
{filters_section}
{evaluation_approach_section}
CANDIDATE MATERIALS:
Resume: {candidate.resume_text}
Cover Letter: {candidate.cover_letter or "Not provided"}
Application: {candidate.application or "Not provided"}

Provide evaluation in this exact JSON format:
{{
  "overall_score": 0-100,
  "recommendation": "STRONG_YES|YES|MAYBE|NO|STRONG_NO",
  "strengths": ["strength1", "strength2"],
  "concerns": ["concern1", "concern2"],
  "interview_priority": "HIGH|MEDIUM|LOW",
  "detailed_notes": "comprehensive evaluation; include 'Failed filters: ...' if any",
  "insights_applied": "which specific insights influenced this evaluation "
                      "(or null if none)"
  ,"rules_applied": ["filter_id_1", "filter_id_2"]
}}"""

    def _build_insights_prompt(
        self, job_context: JobContext, feedback_patterns: List[Dict]
    ) -> str:
        """Build the insights generation prompt.

        Args:
            job_context: Job context and requirements
            feedback_patterns: Aggregated feedback data

        Returns:
            Formatted prompt string
        """
        feedback_data = json.dumps(feedback_patterns, indent=2)

        return f"""Based on the following human feedback patterns for the job "{job_context.name}", generate specific insights that will improve future candidate evaluations:

JOB CONTEXT:
- Description: {job_context.description}
- Ideal Candidate: {job_context.ideal_candidate or "Not specified"}
- Warning Flags: {job_context.warning_flags or "Not specified"}

FEEDBACK PATTERNS:
{feedback_data}

Generate insights in this JSON format:
{{
  "evaluation_criteria_refinements": "specific adjustments to scoring criteria",
  "strength_identification_patterns": "what human reviewers consistently value",
  "concern_identification_patterns": "what human reviewers consistently flag",
  "scoring_calibration": "adjustments to overall scoring approach",
  "recommendation_logic": "refined logic for recommendation categories"
}}"""

    def _parse_evaluation_response(self, response_content: str) -> Dict:
        """Parse and validate evaluation response from API.

        Args:
            response_content: JSON response from API

        Returns:
            Parsed evaluation data dictionary
        """
        try:
            data = json.loads(response_content)

            # Validate required fields and provide defaults
            validated_data = {
                "overall_score": max(0, min(100, data.get("overall_score", 0))),
                "recommendation": data.get("recommendation", "NO"),
                "strengths": data.get("strengths", []),
                "concerns": data.get("concerns", []),
                "interview_priority": data.get("interview_priority", "LOW"),
                "detailed_notes": data.get("detailed_notes", ""),
                "insights_applied": data.get("insights_applied"),
                "rules_applied": data.get("rules_applied"),
            }

            # Validate enum values
            if validated_data["recommendation"] not in [
                r.value for r in RecommendationType
            ]:
                validated_data["recommendation"] = "NO"

            if validated_data["interview_priority"] not in [
                p.value for p in InterviewPriority
            ]:
                validated_data["interview_priority"] = "LOW"

            return validated_data

        except json.JSONDecodeError:
            # Return default evaluation if JSON parsing fails
            return {
                "overall_score": 0,
                "recommendation": "NO",
                "strengths": [],
                "concerns": ["Failed to parse AI evaluation response"],
                "interview_priority": "LOW",
                "detailed_notes": "Evaluation parsing failed",
                "insights_applied": None,
            }
