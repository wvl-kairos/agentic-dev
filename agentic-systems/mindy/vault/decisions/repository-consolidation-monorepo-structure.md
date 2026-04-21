# Repository Consolidation Monorepo Structure

*Decision made: 2026-04-21*

## Context
Team was managing multiple separate repositories for agentic development, data engineering, constraint optimization, and core application code, creating complexity in CI/CD management, code sharing, and deployment coordination.

## Decision
Implement gradual repository consolidation into centralized monorepo structure:
- Move agentic evaluation projects to standalone repository
- Transition data engineering tasks into main monorepo
- Integrate constraint optimization work into consolidated structure  
- Maintain separate CI/CD rules and environment deployments during transition
- Use slow, step-by-step approach to prevent deployment disruptions

## Rationale
- Simplifies code sharing and cross-project dependencies
- Improves CI/CD coordination and deployment management
- Reduces complexity of managing multiple repository configurations
- Enables better team collaboration and code review processes
- Supports unified development workflow while preserving deployment separation
- Facilitates automated documentation and merge tracking

## Implementation
- Armando leading consolidation effort with dedicated architectural planning
- Testing Git submodules approach for gradual integration
- Alex supporting data engineering repository migration
- Tomas integrating constraint optimization work
- Rob coordinating CI/CD rule adjustments and environment management

## Status
Active implementation

## Backlinks
- [[sprints/2026-24]]
- [[people/armando-lopez]]
- [[people/antwoine-flowers]]
- [[people/alex-maramaldo]]
- [[people/tomas-palomo]]
- [[projects/application-infrastructure]]