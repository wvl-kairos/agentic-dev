# Fixed Staging URLs for Deployment Stability

*Decision made: 2026-04-21*

## Context
Team was experiencing challenges with dynamic Vercel URLs for staging environment, creating communication difficulties and deployment instability during customer onboarding and pilot preparation.

## Decision
Implement fixed staging URLs for enhanced stability and customer communication:
- Staging: https://kairos-stg.vercel.app (fixed alias)
- Preview: https://kairos-preview-pr-<PR_NUMBER>.vercel.app (per PR)
- Production: https://kairos-prod.vercel.app (fixed alias)
- Implement URL alias system to maintain both old and new URLs during transition
- Freeze staging environment during customer testing while continuing development in preview
- Enhanced deployment workflows with manual trigger capabilities

## Rationale
- Eliminates confusion with dynamic staging URLs during customer onboarding
- Improves customer experience and communication of environment URLs
- Enables stable testing environment for customer validation and pilot launch
- Supports continued development velocity through preview environments
- Reduces coordination overhead for customer communication
- Provides foundation for production environment with consistent URL strategy

## Implementation
- Luis implemented fixed Vercel deployment aliases with fallback support
- Team coordination on URL communication to Wabash users
- Staging environment stability prioritized for customer testing
- Preview environments maintain development workflow support
- Manual deployment triggers added for enhanced control

## Status
Implemented and active

## Backlinks
- [[sprints/2026-17]]
- [[people/luis-suarez]]
- [[people/evandro-machado]]
- [[projects/application-infrastructure]]