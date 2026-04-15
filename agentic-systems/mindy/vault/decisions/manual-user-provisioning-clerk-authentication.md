# Manual User Provisioning with Clerk Authentication

*Decision made: 2026-04-15*

## Context
Team required secure user onboarding for Moreno Valley production deployment with precise role and department assignment control.

## Decision
Implement manual user provisioning through Clerk authentication:
- Manual user creation with metadata for department and role assignment
- Approver roles stored in private metadata for enhanced security
- Support for username/password and future SSO/Google OAuth integration
- Domain-restricted invites capability
- Initial password setup or invite email process options

## Rationale
- Provides precise control over role and group assignment during onboarding
- Enhanced permission management through private metadata storage
- Security through controlled access and authentication
- Flexibility for multiple authentication methods as system scales
- Reduces risk during initial production rollout

## Implementation
- Evandro implementing user creation flow and metadata management
- Sunny coordinating user email lists and provisioning requirements
- Password setup options being evaluated for user experience
- Production environment integration planned for Moreno Valley visit

## Status
In implementation

## Backlinks
- [[sprints/2026-16]]
- [[people/evandro-machado]]
- [[people/sunny-chalam]]
- [[people/rob-patrick]]