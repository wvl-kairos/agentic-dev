# Repository Consolidation into Agentic-Dev Structure

*Decision made: 2026-04-22*

## Context
Team was managing multiple separate repositories for agentic development, plugins, and various AI tooling projects, creating complexity in code sharing, dependency management, and workflow coordination.

## Decision
Consolidate all agentic development work into unified agentic-dev repository structure:
- Create single repository for all agentic plugins and development tools
- Implement plugin-per-subfolder organization while maintaining unified structure
- Deploy automated documentation system for merge tracking with Notion integration
- Establish consistent installation and configuration processes across tools
- Enable enhanced collaboration through centralized development approach

## Rationale
- Simplifies plugin management and reduces repository sprawl across multiple projects
- Improves code sharing and dependency coordination for agentic development efforts
- Enables automated documentation and merge tracking through GitHub Actions integration
- Facilitates better testing and quality assurance workflows for AI tooling
- Supports unified approach to agentic development while maintaining project separation
- Reduces complexity for team access and usage of various AI development tools

## Implementation
- Armando leading consolidation effort with agentic-dev repository creation and organization
- Individual plugins and tools moved to dedicated subfolders within unified structure
- Automated merge documentation system deployed with Notion database integration
- Team adoption of consolidated repository for all agentic development work
- Plugin cleanup with obsolete repository removal and single-plugin approach

## Status
Implemented and active with automated documentation system deployed

## Backlinks
- [[sprints/2026-19]]
- [[people/armando-lopez]]
- [[projects/investigating-gen-ai-tooling]]
- [[projects/application-infrastructure]]