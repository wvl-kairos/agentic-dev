# AS400 Boomi API Integration Coordination

*Decision made: 2026-01-26*

## Context
Team required coordination on AS400 field specifications for Boomi API writeback integration to enable schedule change updates from Kairos application to legacy AS400 systems.

## Decision
Implement comprehensive AS400 Boomi API integration coordination:
- Define specific fields required for writeback including delivery dates and schedule changes
- Coordinate field specification requirements with Wabash stakeholders
- Focus initial writeback on schedule change fields to reduce customer notification redundancy
- Request API documentation such as Swagger for integration clarity and development ease
- Establish collaborative approach between Rob, Sunny, Antoine, and Luis for specification definition
- Start integration from data analysis to define update fields before engineering implementation

## Rationale
- Enables automated schedule change updates from Kairos to legacy AS400 systems
- Reduces manual coordination overhead and customer notification redundancy
- Provides foundation for comprehensive ERP integration and data synchronization
- Supports customer experience improvements through streamlined schedule change processes
- Ensures proper stakeholder alignment and specification accuracy before development
- Leverages existing Boomi infrastructure for enterprise integration capabilities

## Implementation
- Luis leading change control process coordination with Wabash stakeholders
- Rob coordinating stakeholder alignment and field specification requirements
- Sunny providing customer coordination and use case validation
- Alex supporting field identification and data integration requirements
- API documentation acquisition and integration specification development

## Status
Active coordination and specification development

## Backlinks
- [[sprints/2026-17]]
- [[people/luis-suarez]]
- [[people/rob-patrick]]
- [[projects/schedule-change-request]]