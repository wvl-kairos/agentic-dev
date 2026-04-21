# Flexible Data Architecture Strategy

*Decision made: 2026-04-20*

## Context
Team was initially designing data models specifically for Wabash's one-to-one order-to-chassis relationship but recognized need to support multiple customers with varying business models and requirements.

## Decision
Implement flexible, generic data model supporting scalable customer architecture:
- Move from Wabash-specific one-to-one model to generic one-to-many relationships
- Design order-to-box/chassis model accommodating diverse customer needs
- Create normalized transactional database schema based on ISA 95 standard
- Support multi-tenancy and source-agnostic data structures
- Enable unified analytics across multiple customer implementations

## Rationale
- Supports business expansion beyond single customer implementation
- Reduces technical debt from customer-specific architecture decisions
- Enables scalable platform development for multiple manufacturing environments
- Provides foundation for unified analytics and cross-customer insights
- Aligns with enterprise software development best practices
- Facilitates easier onboarding of future customers with different business models

## Implementation
- Alex leading normalized transactional table schema design based on ISA 95
- Evandro implementing flexible frontend components supporting various data relationships
- Database architecture supporting tenant-aware, source-agnostic structures
- Backend service development using centralized reference schema
- Integration testing across multiple customer data scenarios

## Status
Active implementation

## Backlinks
- [[sprints/2026-17]]
- [[people/alex-maramaldo]]
- [[people/evandro-machado]]
- [[projects/order-visibility]]