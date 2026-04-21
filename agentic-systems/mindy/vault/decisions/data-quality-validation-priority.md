# Data Quality Validation Priority

*Decision made: 2026-04-24*

## Context
Team discovered critical data quality issues with over 2 million lead time entries showing zero values, significantly impacting modeling accuracy and analysis capabilities.

## Decision
Prioritize comprehensive data quality validation over new feature development:
- Document all data quality concerns for client escalation
- Investigate VIN assignment date availability in historical tables
- Validate data pipelines to distinguish technical errors from actual data gaps
- Coordinate with Antoine for client communication regarding data integrity
- Focus on production readiness through data validation processes

## Rationale
- Modeling accuracy depends on reliable data inputs
- Zero lead times across millions of records indicate systemic data issues
- Missing VIN assignment dates prevent chassis history tracking
- Production deployment requires validated data quality
- Client communication necessary to resolve upstream data problems

## Implementation
- Alex leading data quality investigation and documentation
- Team shifting focus from feature development to validation activities
- Coordination with Antoine for client escalation processes
- Integration of data quality checks into CI/CD pipeline

## Status
Active implementation

## Backlinks
- [[sprints/2026-21]]
- [[people/alex-maramaldo]]
- [[people/antwoine-flowers]]
- [[projects/order-visibility]]