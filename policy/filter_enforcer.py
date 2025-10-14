"""Policy layer: deterministic enforcement of screening filters on evaluations.

This module applies per-job screening filters after the AI evaluation, ensuring
that penalties and recommendation rules are enforced consistently regardless of
LLM variability.
"""

from typing import Dict, List, Optional

from models import Evaluation, RecommendationType


def _parse_applied_filters_from_notes(detailed_notes: str) -> List[str]:
    """Extract applied filter IDs from the 'Failed filters:' prefix in notes.

    Expected pattern at the start of the notes (first line):
        "Failed filters: id1, id2"
    """
    if not detailed_notes:
        return []
    marker = "Failed filters:"
    first_line = detailed_notes.split("\n", 1)[0]
    if marker in first_line:
        ids_part = first_line.split(marker, 1)[-1].strip().strip(". ")
        parsed = [p.strip() for p in ids_part.split(",") if p.strip()]
        if parsed:
            return parsed

    # Fallback: look for a line starting with the marker anywhere
    for line in detailed_notes.splitlines():
        if line.strip().startswith(marker):
            ids_part = line.split(marker, 1)[-1].strip().strip(". ")
            parsed = [p.strip() for p in ids_part.split(",") if p.strip()]
            if parsed:
                return parsed
    return []


def enforce_filters_on_evaluation(
    evaluation: Evaluation,
    screening_filters: Optional[Dict],
    verbose: bool = False,
) -> Evaluation:
    """Apply deterministic enforcement rules to an Evaluation in-place.

    - Deduct points as specified by filters
    - Force or cap recommendation according to actions

    Returns the same Evaluation instance for convenience.
    """
    if not screening_filters or not isinstance(screening_filters, dict):
        return evaluation

    items = screening_filters.get("filters", [])
    if not items:
        return evaluation

    id_to_action: Dict[str, Dict] = {
        str(f.get("id")): (f.get("action", {}) if isinstance(f, dict) else {})
        for f in items
        if f and f.get("enabled", True)
    }

    applied_filters = _parse_applied_filters_from_notes(evaluation.detailed_notes)
    if not applied_filters:
        return evaluation

    forced_recommendation = None
    cap_recommendation = None
    total_deduction = 0

    for fid in applied_filters:
        action = id_to_action.get(fid)
        if action is None:
            if verbose:
                print(
                    f"   ⚠️  Filter '{fid}' was applied by AI but not found in "
                    f"screening_filters.json"
                )
            continue
        if not isinstance(action, dict):
            if verbose:
                print(f"   ⚠️  Filter '{fid}' has invalid action (not a dict)")
            continue
        if action.get("set_recommendation"):
            forced_recommendation = action.get("set_recommendation")
        if action.get("cap_recommendation"):
            cap_recommendation = action.get("cap_recommendation")
        if action.get("deduct_points") is not None:
            try:
                points = int(action.get("deduct_points"))
                total_deduction += points
            except (ValueError, TypeError) as e:
                if verbose:
                    print(
                        f"   ⚠️  Filter '{fid}' has invalid deduct_points: "
                        f"{action.get('deduct_points')} ({e})"
                    )

    # Apply score deduction
    if total_deduction > 0:
        try:
            original_score = int(evaluation.overall_score)
            evaluation.overall_score = max(0, original_score - total_deduction)
        except (ValueError, TypeError) as e:
            print(
                f"⚠️  Could not apply score deduction: "
                f"evaluation.overall_score is invalid ({evaluation.overall_score}): {e}"
            )

    # Apply recommendation overrides/caps
    rec_order = [
        RecommendationType.STRONG_NO.value,
        RecommendationType.NO.value,
        RecommendationType.MAYBE.value,
        RecommendationType.YES.value,
        RecommendationType.STRONG_YES.value,
    ]

    try:
        current_rec = evaluation.recommendation.value
        if forced_recommendation and forced_recommendation in rec_order:
            evaluation.recommendation = RecommendationType(forced_recommendation)
        elif (
            cap_recommendation
            and current_rec in rec_order
            and cap_recommendation in rec_order
        ):
            if rec_order.index(current_rec) > rec_order.index(cap_recommendation):
                evaluation.recommendation = RecommendationType(cap_recommendation)
    except (ValueError, AttributeError) as e:
        print(
            f"⚠️  Could not apply recommendation override: "
            f"Invalid recommendation value ({e})"
        )

    if verbose:
        print("\n" + "-" * 80)
        print("🔧 VERBOSE: Policy enforcement applied (filter_enforcer)")
        print(f"   Applied filter IDs: {applied_filters if applied_filters else '[]'}")
        print(f"   Score deduction: {total_deduction}")
        print(f"   Final score: {evaluation.overall_score}")
        print(f"   Final recommendation: {evaluation.recommendation.value}")
        print("-" * 80 + "\n")

    return evaluation
