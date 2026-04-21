# Graphite Stacked PR Workflow

*Decision made: 2026-04-30*

## Context
Team experienced challenges with large single PRs causing conflicts and review bottlenecks, needing improved development workflow for better coordination and reduced integration issues.

## Decision
Implement Graphite for stacked PR workflow:
- Transition from large single PRs to smaller stacked pull requests
- Use Graphite's automated PR stacking and review capabilities
- Configure automatic merge queue for issues tagged with `merge-queue`
- Enable GT commands for streamlined PR submission process
- Reduce conflicts and improve task management efficiency

## Rationale
- Reduces merge conflicts and integration complexity
- Improves code review quality through smaller, focused changes
- Streamlines development workflow and reduces bottlenecks
- Supports faster iteration and feedback cycles
- Aligns with weekly incremental shipping approach
- Enhances collaboration through better change management

## Implementation
- Rob configured Graphite with merge queue automation
- Evandro setting up Graphite for stacked PR usage
- Team adopting GT commands for PR submissions
- Integration with existing CI/CD pipeline workflows
- Training and adoption across engineering team

## Status
Active implementation

## Backlinks
- [[sprints/2026-23]]
- [[people/evandro-machado]]
- [[people/rob-patrick]]
- [[projects/application-infrastructure]]