# ⚖️ Design Decisions — Public Transport Reliability

## Overview

This document explains the main architectural and technical decisions made while building the Public Transport Reliability pipeline. The goal is to keep the solution simple, reproducible, testable, and aligned with the assessment requirement to use Python and SQL.

## 1. Python + SQL Responsibility Separation

**Decision:** Use Python for ingestion, validation, orchestration, and AI integration, while PostgreSQL and SQL handle storage and reliability calculations.

**Rationale:**
- Python and Pandas provide convenient CSV processing and data validation.
- PostgreSQL provides relational integrity and persistent storage.
- SQL makes route-level calculations deterministic and auditable.
- Separating responsibilities makes individual components easier to test and maintain.

**Trade-off:** Some transformations require coordination between Python and SQL, but this separation keeps the pipeline understandable.

## 2. PostgreSQL as the Database

**Decision:** Use PostgreSQL with four main tables: `routes`, `vehicles`, `trips`, and `pipeline_state`.

**Rationale:**
- Routes and vehicles are reference entities.
- Trips contain the operational records used in analytics.
- Pipeline state tracks incremental processing progress.
- Primary keys, foreign keys, and constraints help protect data integrity.

**Trade-off:** PostgreSQL must be installed and configured before the application can run.

## 3. Daily CSV Batch Processing

**Decision:** Use date-specific CSV files as the source data instead of connecting to a live transport API.

**Rationale:**
- CSV files are easy to inspect and reproduce.
- Daily files demonstrate batch ingestion clearly.
- Synthetic data allows delays, cancellations, duplicates, and invalid records to be controlled for testing.

**Trade-off:** The dataset does not represent live transport conditions, and the pipeline does not currently ingest real-time events.

## 4. Validation Before Database Loading

**Decision:** Validate trip records before inserting them into the PostgreSQL `trips` table.

**Rationale:**
- Required fields, route and vehicle references, numeric values, and timestamps are checked.
- Invalid records are written to quarantine with a `validation_error` reason.
- Valid records are staged separately for database loading.
- Original raw files remain unchanged for traceability.

**Trade-off:** Quarantined records require correction or an explicit reprocessing procedure before they can be loaded.

## 5. Incremental Loading and Duplicate Protection

**Decision:** Use `pipeline_state` to track the latest processed service date and `trip_id` as the primary key of the `trips` table.

**Rationale:**
- Previously processed daily files can be skipped.
- `ON CONFLICT (trip_id) DO NOTHING` prevents duplicate trip insertion.
- The state update and database loading use a transaction so a failed transaction does not leave partially committed changes.

**Trade-off:** The current date watermark assumes files arrive in chronological order. A correction or late-arriving file for an older date requires a deliberate backfill or reprocessing strategy.

## 6. SQL-Based Reliability Metrics

**Decision:** Calculate route reliability in the PostgreSQL `route_reliability` view rather than asking Python or AI to recalculate the metrics.

**Rationale:**
- SQL provides a consistent source of truth.
- Metrics can be independently inspected and queried.
- The view can be reused by Python and other reporting tools.

The project defines an on-time trip as a completed trip with a delay of five minutes or less. The reliability score is:

\[
\text{Reliability Score}
= 0.60 \times \text{On-Time Rate}
+ 0.40 \times (100 - \text{Cancellation Rate})
\]

The score ranges from 0 to 100, with higher values indicating better reliability. The 60/40 weighting is a project-specific design choice, not an established industry standard.

**Trade-off:** A composite score simplifies route comparisons, but the result depends on the chosen weights and business definitions.

## 7. AI as an Explanation Layer

**Decision:** Use Google Gemini through a dedicated `src/ai/summarizer.py` interface.

**Rationale:**
- SQL identifies the worst-performing route and calculates its metrics.
- Python passes structured evidence to the AI module.
- The AI explains the supplied evidence in natural language rather than calculating metrics itself.
- Isolating the AI integration makes the provider easier to replace or test independently.

**Trade-off:** AI-generated wording can still be inaccurate or omit context. The SQL results remain authoritative, and generated explanations should be checked against the evidence.

## 8. Configuration and Credential Security

**Decision:** Store local database credentials and AI API keys in `.env`, use `.env.example` as a placeholder template, and exclude `.env` from Git.

**Rationale:**
- Secrets are kept out of application source files.
- Other developers can configure their own environments.
- The repository can be shared without publishing private credentials.

**Trade-off:** Each environment must be configured before database access or AI summarization can run.

## 9. Automated Testing

**Decision:** Use Pytest to verify validation behavior and selected edge cases.

**Rationale:**
- Tests cover valid data, duplicate trip IDs, invalid numeric values, missing route identifiers, and other selected failures.
- Automated assertions help detect regressions when validation rules change.
- Test fixtures provide repeatable examples of invalid input.

**Trade-off:** Passing tests demonstrate only the behaviors they exercise. Database integration, incremental loading, and AI calls should also be verified during end-to-end testing.

## Conclusion

These decisions prioritize a clear Python + SQL architecture, reliable data handling, deterministic analytics, and explainable AI output. The design avoids unnecessary infrastructure while demonstrating the key data-engineering requirements of the assessment.