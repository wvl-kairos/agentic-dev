# Flexible Data Architecture for Scalable Customer Strategy

*Decision made: 2026-04-28*

## Context
Team was initially designing data models specifically for Wabash's one-to-one order-to-chassis relationship but recognized need to support multiple customers with varying business models and operational requirements.

## Decision
Implement flexible, generic data model supporting scalable customer architecture beyond single implementation:
- Move from Wabash-specific one-to-one model to generic one-to-many relationships supporting diverse business models
- Design order-to-box/chassis model accommodating various customer needs and manufacturing processes
- Create normalized transactional database schema based on ISA 95 standard for enterprise compatibility
- Support multi-tenancy and source-agnostic data structures for scalable platform development
- Enable unified analytics across multiple customer implementations with consistent data architecture
- Implement tenant-aware data isolation while maintaining unified analytics capabilities

## Rationale
- Supports business expansion beyond single customer implementation with scalable architecture foundation
- Reduces technical debt from customer-specific architecture decisions and implementation constraints
- Enables scalable platform development for multiple manufacturing environments and business models
- Provides foundation for unified analytics and cross-customer insights while maintaining data isolation
- Aligns with enterprise software development best practices and ISA 95 manufacturing standards
- Facilitates easier onboarding of future customers with different business models and requirements

## Implementation
- Alex leading normalized transactional table schema design based on ISA 95 standard
- Evandro implementing flexible frontend components supporting various data relationships
- Database architecture supporting tenant-aware, source-agnostic structures with unified analytics
- Backend service development using centralized reference schema for consistent data access
- Integration testing across multiple customer data scenarios and business model validation

## Status
Active implementation with schema development and frontend adaptation

## Backlinks
- [[sprints/2026-20]]
- [[people/alex-maramaldo]]
- [[people/evandro-machado]]
- [[projects/order-visibility]]