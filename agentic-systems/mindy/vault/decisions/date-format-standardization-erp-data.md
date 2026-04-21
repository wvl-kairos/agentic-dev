# Date Format Standardization for ERP Data

*Decision made: 2026-04-28*

## Context
Alex identified critical date parsing issues in Frontier ERP data where MMDD formats are inconsistently stored - some as MMDD (1011) and others as MDD (401 = April 1st), causing data pipeline failures and modeling accuracy issues.

## Decision
Implement comprehensive date format standardization across ERP data ingestion:
- Create unified date parsing logic to handle both MMDD and MDD formats
- Validate and normalize date formats during bronze layer ingestion
- Document format variations and create robust transformation rules
- Add data quality checks to catch future format inconsistencies

## Rationale
- Ensures reliable data pipeline processing
- Prevents downstream modeling errors from inconsistent date formats
- Supports accurate historical analysis and forecasting
- Reduces manual intervention required for data quality issues

## Implementation
- Alex leading date parsing logic improvements
- Integration with existing data quality validation processes
- Linear issue to be created for tracking implementation progress

## Status
In planning

## Backlinks
- [[sprints/2026-22]]
- [[people/alex-maramaldo]]
- [[projects/order-visibility]]