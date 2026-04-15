# Data QA as Shared Responsibility

*Decision made: 2026-04-11*

## Context
Team needed to establish clear data quality validation process for production deployment with accountability across development stages.

## Decision
Implement data QA as shared responsibility across team:
- Agent workflows integrate QA early to catch issues sooner
- Engineer sign-off required before moving tickets to "Ready for QA"
- Team walkthrough and validation sessions
- Customer validation through spot QA at plant locations
- CICD integration of data checks across development, staging, and production

## Rationale
- Distributes quality responsibility to prevent single points of failure
- Catches data issues earlier in development cycle
- Ensures production readiness through multiple validation layers
- Maintains accountability while sharing workload
- Aligns with production deployment timeline requirements

## Implementation
- Luis creating data QA tickets with clear ownership assignment
- Alex and Antwoine defining QA process across environments
- Sunny coordinating plant operator validation sessions
- Integration with existing CI/CD pipeline workflows

## Status
Implemented and active

## Backlinks
- [[sprints/2026-16]]
- [[people/luis-suarez]]
- [[people/antwoine-flowers]]
- [[people/alex-maramaldo]]
- [[people/sunny-chalam]]