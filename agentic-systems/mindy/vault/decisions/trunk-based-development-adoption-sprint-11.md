# Trunk-Based Development Adoption (Sprint 11)

*Decision made: 2026-04-21*

## Context
Team was using develop branch workflow but needed to streamline releases and reduce merge conflicts for production deployment and customer onboarding preparation.

## Decision
Transition to trunk-based development with main branch as the primary integration point:
- Feature branches merge directly to main
- Develop branch deprecated and removed
- CI/CD pipelines updated accordingly
- All active PRs retargeted to main
- Squash-only merge strategy enforced
- Force push and direct commits to main blocked

## Rationale
- Simplifies release process and reduces integration complexity
- Reduces merge conflicts and coordination overhead
- Aligns with production deployment needs and customer demo stability
- Improves team coordination and workflow consistency
- Supports faster iteration and deployment cycles

## Implementation
- Alex updated GitHub Actions and branch protection rules
- Luis coordinated team transition and communication
- All team members updated local development workflows
- Graphite configuration updated for main branch targeting
- Documentation updated with new workflow procedures

## Status
Implemented and active

## Backlinks
- [[sprints/2026-17]]
- [[people/alex-maramaldo]]
- [[people/luis-suarez]]
- [[projects/application-infrastructure]]