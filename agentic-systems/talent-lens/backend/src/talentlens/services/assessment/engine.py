"""Assessment engine — core orchestrator for the evaluation pipeline.

Pipeline per interview:
1. Compute talk ratio from diarization
2. Detect individual contributions ("I built" vs "we built")
3. Score against rubric criteria via Claude API
4. Persist Assessment + CriterionScores + Evidence
5. Advance candidate pipeline stage
6. Send Slack notification
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from talentlens.models.database.assessment import Assessment, CriterionScore
from talentlens.models.database.candidate import Candidate, PipelineStage
from talentlens.models.database.capability import (
    Capability,
    RoleCapabilityRequirement,
    RoleTemplate,
    RoleTechnologyRequirement,
)
from talentlens.models.database.evidence import Evidence
from talentlens.models.database.interview import Interview
from talentlens.models.database.rubric import Rubric
from talentlens.services.assessment.contribution import detect_contributions
from talentlens.services.assessment.scoring import score_interview
from talentlens.services.assessment.talk_ratio import compute_talk_ratio
from talentlens.services.notifications.slack import notify_assessment_complete

logger = logging.getLogger(__name__)

# Maps interview type → pipeline stage the candidate should advance to after assessment
STAGE_ADVANCEMENT = {
    "screening": PipelineStage.coderpad,
    "coderpad": PipelineStage.technical_interview,
    "technical": PipelineStage.final_interview,
    "final": PipelineStage.decision,
}


LEVEL_LABELS = {1: "Beginner", 2: "Junior", 3: "Mid-level", 4: "Senior", 5: "Expert"}


async def _build_criteria_from_template(
    role_template_id: uuid.UUID, db: AsyncSession
) -> tuple[list[dict], dict]:
    """Build evaluation criteria from a role template's capability + technology requirements.

    Returns:
        (criteria_list, role_context) where role_context is extra info for the scoring prompt.
    """
    result = await db.execute(
        select(RoleTemplate)
        .where(RoleTemplate.id == role_template_id)
        .options(
            selectinload(RoleTemplate.requirements)
            .selectinload(RoleCapabilityRequirement.capability),
            selectinload(RoleTemplate.technology_requirements)
            .selectinload(RoleTechnologyRequirement.technology),
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        return [], {}

    criteria = []

    # Capability-based criteria — each required capability becomes a scored criterion
    for req in template.requirements:
        cap = req.capability
        if not cap:
            continue
        level_label = LEVEL_LABELS.get(req.required_level, f"Level {req.required_level}")
        criteria.append({
            "name": cap.name,
            "description": (
                f"{cap.description or cap.name} — "
                f"Evaluate at {level_label} level ({req.required_level}/5). "
                f"Look for depth of knowledge, practical experience, and problem-solving "
                f"ability consistent with a {level_label} engineer in this area."
            ),
            "weight": max(1.0, req.required_level / 2),  # higher requirements = heavier weight
            "max_score": 5,
            "capability_id": str(cap.id),
        })

    # Technology-based criteria — group by parent capability for clarity
    tech_by_cap: dict[str, list[tuple[str, int]]] = {}
    for treq in template.technology_requirements:
        tech = treq.technology
        if not tech:
            continue
        # Find parent capability name
        cap_name = None
        for req in template.requirements:
            if req.capability and req.capability.id == tech.capability_id:
                cap_name = req.capability.name
                break
        if not cap_name:
            cap_result = await db.execute(
                select(Capability).where(Capability.id == tech.capability_id)
            )
            parent_cap = cap_result.scalar_one_or_none()
            cap_name = parent_cap.name if parent_cap else "Technical"

        tech_by_cap.setdefault(cap_name, []).append((tech.name, treq.required_level))

    for cap_name, techs in tech_by_cap.items():
        tech_list = ", ".join(
            f"{name} ({LEVEL_LABELS.get(level, 'Level ' + str(level))})"
            for name, level in techs
        )
        avg_level = sum(level for _, level in techs) / len(techs) if techs else 3
        criteria.append({
            "name": f"{cap_name} — Technology Stack",
            "description": (
                f"Evaluate proficiency in the following technologies: {tech_list}. "
                f"Look for hands-on experience, depth of understanding, awareness of "
                f"best practices, and ability to discuss trade-offs for each technology."
            ),
            "weight": max(1.0, avg_level / 2),
            "max_score": 5,
        })

    role_context = {
        "role_name": template.name,
        "role_description": template.description or "",
        "capability_count": len(template.requirements),
        "technology_count": len(template.technology_requirements),
    }

    logger.info(
        "Built %d criteria from role template '%s' (%d capabilities, %d technologies)",
        len(criteria),
        template.name,
        len(template.requirements),
        len(template.technology_requirements),
    )
    return criteria, role_context


async def _find_rubric(candidate: Candidate, db: AsyncSession) -> list[dict]:
    """Find the best matching rubric for a candidate's venture + role."""
    result = await db.execute(
        select(Rubric)
        .where(Rubric.venture_id == candidate.venture_id)
        .options(selectinload(Rubric.criteria))
        .order_by(Rubric.created_at.desc())
    )
    rubrics = result.scalars().all()

    # Try to match by role
    for rubric in rubrics:
        if rubric.role and candidate.role and rubric.role.lower() in candidate.role.lower():
            return [
                {
                    "name": c.name,
                    "description": c.description,
                    "weight": c.weight,
                    "max_score": c.max_score,
                }
                for c in rubric.criteria
            ], rubric.id

    # Fall back to first rubric or default criteria
    if rubrics and rubrics[0].criteria:
        rubric = rubrics[0]
        return [
            {
                "name": c.name,
                "description": c.description,
                "weight": c.weight,
                "max_score": c.max_score,
            }
            for c in rubric.criteria
        ], rubric.id

    # No rubric found — use defaults
    logger.warning("No rubric found for candidate %s, using defaults", candidate.id)
    return [
        {"name": "Technical Skills", "description": "Depth of technical knowledge demonstrated", "weight": 2.0, "max_score": 5},
        {"name": "Communication", "description": "Clarity and structure of responses", "weight": 1.0, "max_score": 5},
        {"name": "Problem Solving", "description": "Approach to breaking down problems", "weight": 1.5, "max_score": 5},
        {"name": "Individual Ownership", "description": "Ability to articulate personal contributions", "weight": 1.0, "max_score": 5},
    ], None


async def run_assessment_pipeline(interview_id: uuid.UUID, db: AsyncSession) -> uuid.UUID:
    """Run the full assessment pipeline for an interview.
    Returns the created Assessment ID."""

    # 1. Load interview
    interview = await db.get(Interview, interview_id)
    if not interview:
        raise ValueError(f"Interview {interview_id} not found")

    if not interview.transcript:
        raise ValueError(f"Interview {interview_id} has no transcript")

    # Load candidate if linked
    candidate = None
    if interview.candidate_id:
        candidate = await db.get(Candidate, interview.candidate_id)

    # 2. Compute talk ratio
    diarization = interview.diarization
    # Handle both raw list and enriched dict format
    if isinstance(diarization, dict):
        segments = diarization.get("segments", [])
    else:
        segments = diarization or []

    candidate_name = candidate.name if candidate else None
    talk_result = compute_talk_ratio(segments, candidate_name)
    interview.talk_ratio = talk_result["candidate_ratio"]

    logger.info(
        "Interview %s: talk ratio %.0f%% (%s)",
        interview_id,
        talk_result["candidate_ratio"] * 100,
        talk_result["candidate_speaker"],
    )

    # 3. Detect contributions
    contributions = detect_contributions(
        interview.transcript,
        candidate_speaker=talk_result["candidate_speaker"],
    )
    logger.info(
        "Interview %s: %d individual, %d collective contributions",
        interview_id,
        contributions["individual_count"],
        contributions["collective_count"],
    )

    # 4. Build criteria: prefer role template → manual rubric → defaults
    rubric_id = None
    role_context = {}

    if candidate and candidate.role_template_id:
        # Use role template requirements as dynamic criteria
        criteria, role_context = await _build_criteria_from_template(
            candidate.role_template_id, db
        )
        if criteria:
            logger.info(
                "Using role template criteria for candidate %s (%d criteria)",
                candidate.name,
                len(criteria),
            )
        else:
            # Template exists but has no requirements — fall back to rubric
            criteria, rubric_id = await _find_rubric(candidate, db)
    elif candidate:
        criteria, rubric_id = await _find_rubric(candidate, db)
    else:
        criteria, rubric_id = [
            {"name": "Technical Skills", "description": "Depth of technical knowledge", "weight": 2.0, "max_score": 5},
            {"name": "Communication", "description": "Clarity of responses", "weight": 1.0, "max_score": 5},
            {"name": "Problem Solving", "description": "Approach to problems", "weight": 1.5, "max_score": 5},
            {"name": "Individual Ownership", "description": "Personal contributions", "weight": 1.0, "max_score": 5},
        ], None

    scoring_result = await score_interview(
        transcript=interview.transcript,
        criteria=criteria,
        talk_ratio=talk_result["candidate_ratio"],
        contributions=contributions,
        interview_type=interview.interview_type.value,
        role_context=role_context,
    )

    # 5. Persist Assessment
    stage = interview.interview_type.value
    assessment = Assessment(
        candidate_id=interview.candidate_id,
        interview_id=interview.id,
        rubric_id=rubric_id,
        stage=stage,
        overall_score=scoring_result.get("overall_score"),
        summary=scoring_result.get("summary"),
        recommendation=scoring_result.get("recommendation"),
        raw_response={"scoring": scoring_result, "talk_ratio": talk_result, "contributions": contributions},
    )
    db.add(assessment)
    await db.flush()

    # Persist criterion scores + evidence
    for cs_data in scoring_result.get("criteria_scores", []):
        criterion_score = CriterionScore(
            assessment_id=assessment.id,
            criterion_name=cs_data.get("criterion_name", ""),
            score=cs_data.get("score", 0),
            max_score=cs_data.get("max_score", 5),
            reasoning=cs_data.get("reasoning"),
        )
        db.add(criterion_score)
        await db.flush()

        for ev_data in cs_data.get("evidence", []):
            evidence = Evidence(
                criterion_score_id=criterion_score.id,
                quote=ev_data.get("quote", ""),
                speaker=ev_data.get("speaker"),
                relevance="supports",
            )
            db.add(evidence)

    # Store analysis in interview diarization
    interview.diarization = {
        "segments": segments,
        "analysis": {
            "talk_ratio": talk_result,
            "contributions": contributions,
        },
    }

    # 6. Advance candidate stage
    if candidate:
        next_stage = STAGE_ADVANCEMENT.get(stage)
        if next_stage and candidate.stage != PipelineStage.rejected:
            candidate.stage = next_stage
            logger.info("Advanced candidate %s to stage %s", candidate.name, next_stage.value)

    await db.commit()

    logger.info(
        "Assessment %s complete: %.1f/5.0 → %s",
        assessment.id,
        scoring_result.get("overall_score", 0),
        scoring_result.get("recommendation", "unknown"),
    )

    # 7. Slack notification (fire-and-forget, don't fail the pipeline)
    try:
        await notify_assessment_complete(
            candidate_name=candidate.name if candidate else "Unknown",
            stage=stage,
            overall_score=scoring_result.get("overall_score", 0),
            recommendation=scoring_result.get("recommendation", "unknown"),
            scorecard_url=f"/assessment/{assessment.id}",
        )
    except Exception as e:
        logger.warning("Slack notification failed (non-critical): %s", e)

    return assessment.id
