# Clerk Authentication with Manual Provisioning

*Decision made: 2026-04-14*

## Context
Team needed secure user onboarding approach for Moreno Valley deployment with proper role and department assignment.

## Decision
Use Clerk authentication with manual user creation:
- Manual user addition with metadata for department and role
- Approver roles stored in private metadata for security
- Support for username/password and future SSO/Google OAuth
- Domain-restricted invites possible

## Rationale
- Precise role and group assignment control
- Enhanced permission management during onboarding
- Security through private metadata storage
- Flexibility for multiple authentication methods

## Implementation
- Evandro implementing user creation flow
- Sunny coordinating user email list
- Password setup options being evaluated
- Production environment integration planned

## Status
In implementation

## Backlinks
- [[sprints/2026-15]]
- [[people/evandro-machado]]
- [[people/sunny-chalam]]