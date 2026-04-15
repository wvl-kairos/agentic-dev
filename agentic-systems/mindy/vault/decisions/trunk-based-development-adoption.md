# Trunk-Based Development Adoption

*Decision made: 2026-04-11*

## Context
Team was using develop branch workflow but needed to streamline releases and reduce merge conflicts for production deployment.

## Decision
Transition to trunk-based development with main branch as the primary integration point:
- Feature branches merge directly to main
- CI/CD pipelines updated accordingly
- Monorepo commits follow this pattern

## Rationale
- Simplifies release process
- Reduces integration complexity
- Aligns with production deployment needs
- Improves team coordination

## Implementation
- Alex updated GitHub Actions
- Tomas confirmed approach for Schedule Manager
- All new work follows feature branch → main pattern

## Status
Implemented and active

## Backlinks
- [[sprints/2026-15]]
- [[people/alex-maramaldo]]
- [[people/rob-patrick]]