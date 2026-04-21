# Manual Preview Deployment for Resource Optimization

*Decision made: 2026-04-21*

## Context
Team was experiencing resource conflicts and deployment inefficiencies with automatic Vercel deployments triggering alongside GitHub Actions CI/CD pipeline.

## Decision
Implement manual preview deployment process using GitHub Actions:
- Label-based deployment triggering to reduce resource usage
- Disable automatic Vercel deployments to prevent conflicts
- Manual control over preview environment creation and resource allocation
- Per pull request Azure environment deployment with automated teardown
- Optimize resource usage while maintaining development velocity

## Rationale
- Reduces resource conflicts between Vercel and GitHub Actions deployments
- Provides manual control over preview environment resource allocation
- Optimizes development workflow efficiency and reduces deployment overhead
- Maintains development velocity while improving resource management
- Enables better coordination between multiple deployment systems
- Supports cost optimization and infrastructure resource planning

## Implementation
- Alex implemented GitHub Actions labeling system for manual deployment triggering
- Automatic Vercel deployments disabled to prevent deployment conflicts
- Azure environment deployment per pull request with automated resource management
- Team adoption of manual deployment workflow with label-based triggering

## Status
Implemented and active

## Backlinks
- [[sprints/2026-17]]
- [[people/alex-maramaldo]]
- [[people/evandro-machado]]
- [[projects/application-infrastructure]]