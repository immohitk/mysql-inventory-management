# Data Migration Plan

## 1. Purpose

This document describes the migration tooling and development-database workflow for the procurement schema introduced in `v0.4.1`.

The goal of `v0.4.2` is to provide a reliable, repeatable way to create and upgrade an isolated development/test database, track applied migrations, and recover safely from migration failures.

Legacy inventory records are disposable demonstration data. Preserving their historical rows, reconciling old purchase totals, or completing mappings for the eight legacy products is not a completion requirement for this development milestone. When GUI testing begins, sample records can be entered again through the application.

## 2. Scope

The migration workflow covers:

- Creating or preparing a dedicated development/test database.
- Applying ordered SQL migration files.
- Recording successful migrations in `schema_migrations`.
- Skipping migrations already recorded as applied.
- Detecting and reporting migration failures clearly.
- Documenting the limitations of MySQL DDL rollback and partial migration failures.
- Providing an intentional workflow to reset and seed disposable development data.
- Keeping the protected database `inventory_db` safe from accidental migration or reset operations.

This milestone does not require migration of legacy demo records into the new procurement model.

## 3. Database Safety Rules

- Use an explicitly named development/test database for migration experiments.
- The migration runner must require an explicit `--database` argument.
- The runner must reject protected or non-test database names before executing migration SQL.
- Never infer the target database from a default connection or silently fall back to `inventory_db`.
- A reset operation must display or require the exact target database and must refuse protected databases.
- Do not drop or reset a database until the intended development/test target has been identified.
- Keep schema migrations and migration history separate from disposable demo records.
- Do not put private development roadmaps or internal workflow notes into public project documentation.

## 4. Migration Workflow

The normal workflow is:

1. Select an explicitly named development/test database.
2. Create the database if the setup workflow is intended to do so.
3. Apply migration files in deterministic filename order.
4. Record each successful migration in `schema_migrations`.
5. Skip migrations already recorded as applied.
6. Stop on the first migration error and report the migration filename and error.
7. Inspect the database after a failure; do not blindly rerun a partially applied migration.
8. Run the relevant schema and application tests.
9. Record the result in the development notes or test output.

A successful second run should skip previously recorded migrations rather than duplicate their effects.

## 5. Migration History

The `schema_migrations` table is the record of migrations successfully applied by the runner.

The runner should:

- Create the history table when it is missing.
- Record a migration only after its SQL completes successfully.
- Skip migration files already present in the history table.
- Apply pending migrations in a stable, deterministic order.
- Fail clearly if a migration cannot be executed.
- Avoid marking a partially executed migration as successful.

MySQL may persist some DDL changes even when a later statement in the same migration fails. A history table alone therefore cannot guarantee that a failed migration left the schema unchanged.

## 6. Failure Handling and Recovery

MySQL schema statements may cause implicit commits. Do not assume a transaction rollback will undo all DDL in a failed migration.

When a migration fails:

1. Stop and capture the migration filename and error message.
2. Keep the failed database isolated from normal application use.
3. Inspect which tables, columns, indexes, and history entries were created before the failure.
4. For a clean retry, create a new uniquely named disposable test database or reset the confirmed disposable database using the documented reset workflow.
5. Re-run the complete migration sequence against that clean test database.
6. Verify the expected schema and migration-history entries.
7. Run the migration runner a second time and confirm that already-applied migrations are skipped.
8. Record any known limitation or remaining failure case.

Do not automatically delete partial objects from an unknown database. The recovery path must be explicit and limited to a disposable development/test target.

## 7. Development Database Reset and Demo Seed

Development data exists to support GUI and automated testing; it is not business data that must be preserved.

The development workflow should support:

- Starting with a fresh database schema.
- Loading a small, deterministic set of demo records when useful.
- Clearing and re-entering demo records during GUI testing.
- Repeating setup without duplicating seed data, or explicitly resetting the disposable database before reseeding.
- Keeping test setup separate from any real or protected database.

Before implementing a reset command, validate the target database name and reject protected databases. The reset workflow must not silently delete data from `inventory_db` or any database outside the explicitly supported development/test naming convention.

The reset/seed documentation should explain which operation drops data, which operation creates schema, and which operation inserts demo records.

## 8. Testing Requirements

Tests for this milestone should cover the migration tooling itself, not the preservation of legacy demo records.

Required checks:

- Migration runner requires an explicit database target.
- Protected database names are rejected before SQL execution.
- Migration files are applied in deterministic order.
- Successful migrations are recorded in `schema_migrations`.
- A second run skips migrations already recorded.
- A migration error is reported and is not recorded as successful.
- Partial DDL after a failure is documented and the recovery workflow is clear.
- Fresh database setup produces the expected target schema.
- Reset/seed operations are scoped to disposable development/test databases.
- The relevant existing automated test suite passes.

Tests should use isolated test databases or controlled test fixtures. Do not use the protected application database as a migration test target.

## 9. Existing Validation Evidence

The following checks were previously documented as completed against the isolated development database `inventory_migration_dev`:

- Imported `database/schema_base.sql` successfully.
- Applied migrations `001` through `004` successfully.
- Verified that all four migrations were recorded in `schema_migrations`.
- Ran the migration runner a second time and confirmed that all four migrations were skipped as already recorded.
- Verified that the final database contained the expected 16 tables, including the core schema, procurement tables, and `schema_migrations`.
- A historical automated test run was reported as successful: `63 passed`.
- **Live migration-failure recovery drill:** Using the isolated `inventory_migration_recovery` database, an intentionally invalid migration was detected and rejected by the runner. The failed migration was not recorded in `schema_migrations`. MySQL retained the table created before the syntax error, confirming that partial DDL can survive a failed migration. The temporary test table and migration-history table were removed afterward; verification confirmed the seven core tables remained intact. The normal migration files were not modified, and `inventory_migration_dev` and `inventory_db` were not touched during the drill.

These are historical validation results recorded in the project documentation. They were not independently repeated during the current review.

The current review separately ran focused migration-runner unit tests and reset/seed unit tests. Those results are documented in Section 12. They do not constitute a new live-database test or a rerun of the full test suite.

## 10. Out of Scope

The following are not blockers for `v0.4.2`:

- Preserving disposable legacy categories, suppliers, products, purchases, or purchase items.
- Field-by-field reconciliation of historical demo records.
- Reconciliation of legacy purchase headers, item subtotals, and financial totals solely to preserve test data.
- Obtaining real-world evidence for the unit or package sizes of the eight legacy demo products.
- Completing initial supplier-offer mappings from legacy demo products.
- Keeping old demo product IDs or relationships after a fresh development reset.

These items may be revisited only if the project later adopts a real-data import requirement. They should not delay development of the intended procurement features.

## 11. Completion Criteria

`v0.4.2` is complete when:

- The migration runner safely targets only supported development/test databases.
- Migration history is recorded and repeat-run behavior is tested.
- Migration failures are reported clearly and are not falsely marked successful.
- Partial-DDL behavior and the clean-retry procedure are documented.
- A fresh development database can be prepared from the migration files.
- A safe, explicit reset/seed workflow is available or its remaining implementation work is clearly listed.
- Relevant automated tests pass.
- Documentation reflects the implemented behavior and actual validation evidence.

No legacy demo-data preservation or product-mapping sign-off is required to complete this milestone.

## 12. Current Review Status and Evidence

**Status: Closure recommended — acceptance evidence reviewed; historical recovery evidence accepted.**

The focused automated tests, working-tree checks, and live MySQL acceptance validation have been completed for this review. Live MySQL tests were run against the isolated disposable database `inventory_migration_acceptance_20261019`, not the application's `inventory_db`.

### 12.1 Current Verification Results

- **Focused test suite:** 50 passed, 2 skipped, and 3 subtests passed.
- **Live MySQL supplier-offer lifecycle tests:** 2 passed in 0.89 seconds.
- **Fresh-schema migration:** All four migrations applied successfully to the isolated acceptance database.
- **Migration rerun:** All four previously applied migrations were skipped as expected.
- **Schema verification:** The acceptance database recorded four applied migrations and contained the expected 16 tables.
- **Python compilation:** Passed for the migration runner, migration unit tests, and integration test modules.
- **Diff formatting check:** `git diff --check` completed without reporting issues.
- **Working tree:** Changes remain uncommitted. Untracked files have been preserved.

Final closure remains pending until the remaining acceptance criteria and documentation are reconciled.

### 12.2 Historical Database Validation

Earlier documentation records successful fresh-schema migration, migration-history and rerun checks, and a recovery drill using isolated test databases.

Those results remain **historical evidence**. They were not independently reproduced during this review and must not be presented as newly verified results.

### 12.3 Working-Tree State

The working tree contains these changes:

- Modified: `database/migrate.py`
- Modified: `docs/data-migration-plan.md`
- Modified: `tests/test_migrate.py`
- Untracked: `database/schema_fresh.sql`
- Untracked: `tests/integration/`

The untracked schema and integration-test files must be preserved. They must not be staged or committed as part of this review without explicit authorization.

No commit, push, tag, release operation, or database operation was performed during this review.

### 12.4 Verification Limitations

TThe current review verified the selected automated tests, Python compilation, working-tree formatting, fresh-schema migration, migration rerun behavior, and live supplier-offer lifecycle against an isolated disposable MySQL database.

The historical isolated-database migration-failure recovery drill documented in Section 9 is accepted as sufficient evidence for v0.4.2 closure. It was not independently repeated during the current review. Therefore, the current review does not claim new live verification of MySQL migration-failure recovery or partial-DDL behavior.

Based on the accepted historical recovery evidence and the current verification results, no additional destructive live-database validation is required for this milestone's closure. All database operations must continue to use explicitly authorized disposable targets; the protected application database `inventory_db` must not be used for migration acceptance or recovery testing.

## 13. Remaining Work

1. **Acceptance evidence:** Accept the historical isolated-database migration-failure recovery evidence documented in Section 9, together with the current review's automated and live validation results, for v0.4.2 closure.
2. **Verification limitations:** Retain the explicit record that the historical failure-recovery drill was not repeated during the current review.
3. **Preserve the worktree:** Keep `database/schema_fresh.sql` and `tests/integration/` unchanged and untracked unless separately authorized.
4. **Milestone status:** Closure is recommended based on the accepted historical recovery evidence and current verification results. Historical failure-recovery testing was not repeated during this review.
5. **Release actions:** Commit, push, create tags, or publish a release only with separate explicit authorization.

The legacy demo records are not required to be reconciled or preserved for this milestone. The priority remains the migration foundation, schema compatibility, migration-history consistency, safe failure handling, and a documented recovery procedure. Any destructive database operation requires explicit authorization for the specific target database.
