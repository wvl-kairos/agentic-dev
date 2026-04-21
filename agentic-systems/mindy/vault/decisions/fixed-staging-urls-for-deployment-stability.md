# Fixed Staging URLs for Deployment Stability

*Decision made: 2026-04-19*

## Context
Team was experiencing issues with dynamic Vercel URLs for staging environment, creating communication challenges and deployment instability during customer onboarding.

## Decision
Transition to fixed staging URLs for better stability and communication:
- Staging: https://kairos-stg.vercel.app (fixed)
- Preview: https://kairos-preview-pr-<PR_NUMBER>.vercel.app (per PR)
- Production: https://kairos-prod.vercel.app (fixed)
- Implement URL redirects to avoid user disruption
- Freeze staging environment during customer testing while continuing development in preview

## Rationale
- Eliminates confusion with dynamic staging URLs
- Improves customer experience during onboarding
- Enables better communication of environment URLs to users
- Supports stable testing environment for customer validation
- Maintains development velocity through preview environments

## Implementation
- Luis updated Vercel deployment workflows with fixed aliases
- Team coordination on URL communication to Wabash users
- Staging environment frozen for customer testing
- Preview environments continue to support development

## Status
Implemented and active

## Backlinks
- [[sprints/2026-20]]
- [[people/luis-suarez]]
- [[people/evandro-machado]]
- [[projects/application-infrastructure]]