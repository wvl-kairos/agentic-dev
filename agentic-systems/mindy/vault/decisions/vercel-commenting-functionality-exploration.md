# Vercel Commenting Functionality Exploration

*Decision made: 2026-05-09*

## Context
Team needed improved feedback and review processes for preview deployments, with existing tools like Agentation creating integration challenges and workflow inefficiencies.

## Decision
Explore and implement Vercel commenting functionality for enhanced feedback processes:
- Investigate Vercel's native commenting features for preview environment feedback
- Test integration with existing CI/CD pipeline and Linear issue tracking
- Evaluate feasibility of automated comment posting from GitHub pipeline
- Assess structured comment formats for engineering clarity and visual context
- Determine access configuration for team members including Sunny and Amanda
- Link preview URLs to Linear tickets for comprehensive feedback tracking

## Rationale
- Provides integrated feedback mechanism directly within preview environments
- Eliminates need for separate annotation tools with complex integration requirements
- Supports visual context linking and descriptive notes for improved feedback quality
- Enables better collaboration between design, product, and engineering teams
- Streamlines feedback collection and issue triage processes
- Aligns with existing Vercel deployment infrastructure for seamless workflow

## Implementation
- Evandro Machado investigating Vercel commenting feature capabilities and limitations
- Rob Patrick coordinating access configuration for Amanda and Sunny
- Team testing comment posting automation and Linear integration
- Amanda experimenting with structured comment formats for design feedback
- Weekly Linear issue creation for consolidating demo feedback and UI fixes

## Status
Active exploration and testing

## Backlinks
- [[sprints/2026-20]]
- [[people/evandro-machado]]
- [[people/amanda-cunha]]
- [[people/rob-patrick]]
- [[projects/application-infrastructure]]