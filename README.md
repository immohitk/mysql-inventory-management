# MySQL Inventory Management

A Python desktop application for inventory operations backed by MySQL.
The repository contains a Tkinter-based GUI, application services,
database/repository code, schema and migration utilities, supplier-offer
review persistence, and automated tests.

## Current Development Status

The current development focus is the **supplier-offer lifecycle and
review workflow (`v0.4.3`)**.

The repository includes supplier-offer repository/service functionality,
validation for supplier/product/package references, price and
minimum-order-quantity rules, review persistence, database-safety
tooling, and integration tests. The milestone should not be described as
released merely because its implementation or documentation exists;
acceptance and release preparation must follow the project roadmap.

The procurement schema redesign is being developed incrementally.
Proposed designs, requirements, and roadmap entries describe plans or
intended behavior unless confirmed by implementation and tests.

## Technology Stack

- **Language:** Python
- **Database:** MySQL
- **Database driver:** `mysql-connector-python`
- **Configuration:** `python-dotenv`
- **Desktop interface:** Tkinter
- **Testing:** `pytest`
- **Data access:** SQL-backed repository and service modules

## Features and Components

### Desktop application

The current GUI structure includes:

- Category management
- Product management
- Supplier management
- Purchase workflows
- Main application window

Application entry point: `main.py`

### Application services

The repository includes services for product, supplier, purchase, and
supplier-offer operations.

Supplier offers connect a supplier, product, and package specification
with a minimum order quantity (MOQ), purchase price, and active state.
The service layer supports offer creation, retrieval, updates, and
activation/deactivation, with validation for identifiers, references,
pricing, MOQ, and duplicate combinations.

### Supplier-offer reviews

The supplier-offer review workflow persists review evidence and decision
information separately from offer CRUD. The workflow supports reviewer
details, notes/evidence, a decision status, and a database-generated
timestamp. Supported review statuses include `PENDING`, `APPROVED`, and
`REJECTED`.

Review persistence validates its target and review data. Existing review
records are not silently overwritten as part of ordinary offer updates.

See [`docs/supplier-offer-service.md`](docs/supplier-offer-service.md)
for the service and persistence contracts.

### Database and validation tooling

The repository includes utilities for:

- Database migrations and fresh isolated migration-database setup
- Migration and reset safety checks
- Legacy inventory-unit and supplier-offer mapping validation
- Package-content validation
- Supplier-offer validation and review persistence

Database scripts have specific target restrictions. Read their
documentation and safeguards before running any database-changing
operation.

## Repository Structure

```text
.
├── app/
│   ├── config.py
│   ├── db/
│   ├── gui/
│   ├── repositories/
│   └── services/
├── database/
│   ├── migrations/
│   ├── migrate.py
│   ├── reset_dev.py
│   ├── seed_demo.py
│   ├── supplier_offer_approval.py
│   ├── supplier_offer_review_service.py
│   ├── validate_mappings.py
│   ├── validate_package_contents.py
│   ├── validate_supplier_offers.py
│   ├── schema.sql
│   ├── schema_base.sql
│   ├── schema_fresh.sql
│   ├── schema_v2.sql
│   └── seed.sql
├── docs/
│   ├── database-architecture.md
│   ├── legacy-inventory-unit-mapping.md
│   ├── legacy-supplier-offer-mapping.md
│   ├── procurement-schema-design.md
│   ├── requirements.md
│   └── supplier-offer-service.md
├── screenshots/
├── tests/
│   └── integration/
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

## Prerequisites

- Python
- MySQL Server
- Git
- A MySQL account with the privileges required for the intended
  application database

## Installation

Run these commands from the project root in PowerShell.

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure the environment

Create a local environment file from the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env` locally and set the connection values for your intended
application database. The example configuration uses these variable
names:

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_NAME=inventory_db
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
```

Replace the example credentials with your own local values. Never commit
`.env`, passwords, tokens, or connection secrets, and do not paste them
into chat or public issue reports.

### 4. Prepare the database

Before launching the application, verify that the configured database
exists and has the schema expected by the current code.

The repository contains multiple schema files intended for different
stages or purposes. Do not assume that they are interchangeable, and do
not run a schema or migration script against an existing database
without first understanding its effects.

**Database safety requirements:**

- **Never run migrations, schema SQL, test writes, seed/reset
  utilities, or other test operations against `inventory_db`.** It is
  the protected application database.
- Use only a separately verified, isolated
  `inventory_migration_<test_name>` database for migration and MySQL
  integration testing.
- Never assume a database is disposable because its name matches that
  pattern. Verify its ownership, contents, configuration, and
  permissions before use.
- Use a least-privileged account limited to the intended test
  database.
- Do not blindly rerun partially applied DDL or use
  `database/reset_dev.py` as a general-purpose reset command.
- Never print or commit credentials while diagnosing database setup.

The migration and database-creation utilities include target
restrictions and additional safety checks; those checks do not replace
verifying the actual target and its disposability.

## Run the Application

With the virtual environment activated and `.env` configured:

```powershell
python main.py
```

The entry point launches the desktop application through
`app.gui.main_window`.

If startup fails, check the installed dependencies, MySQL service, local
environment configuration, database availability, and compatibility of
the database schema with the current code. Do not use the protected
application database as a test target to diagnose failures.

## Testing

Run the default test suite:

```powershell
python -m pytest -q
```

Run integration tests separately when their required safety
configuration has been verified:

```powershell
python -m pytest tests/integration -q -rs
```

Read the integration-test helpers and safety tests before enabling live
MySQL integration tests. A live database test must use an explicitly
verified disposable database and a least-privileged account. Never point
integration tests at `inventory_db` or at an unverified existing
`inventory_migration_*` database.

Prefer `python -m pytest` if invoking the standalone `pytest` command
does not resolve the project modules correctly.

## Documentation

- [Database architecture](docs/database-architecture.md)
- [Project requirements](docs/requirements.md)
- [Procurement schema design](docs/procurement-schema-design.md)
- [Legacy inventory-unit mapping](docs/legacy-inventory-unit-mapping.md)
- [Legacy supplier-offer mapping](docs/legacy-supplier-offer-mapping.md)
- [Supplier-offer service and persistence contract](docs/supplier-offer-service.md)

Some documentation describes proposals, migration plans, or intended
behavior. Confirm implementation status by inspecting the current source
code and relevant tests.

## Roadmap and Release Status

The active milestone is **`v0.4.3` — supplier-offer lifecycle and review**.
Use the current recalibrated project roadmap as the authority for sub-version
scope, dependencies, and acceptance criteria. This README is a status summary,
not a substitute for the detailed roadmap.

Milestone completion requires implementation and verification evidence for all
acceptance criteria. Passing the automated suite alone does not establish that
live MySQL integration, manual GUI checks, or release requirements have passed.
Do not describe `v0.4.3` as released until the release gate is complete and a
release is actually published.

## Development Workflow

Follow the active roadmap and work on one bounded sub-version at a time:

1.  Capture the current Git status, recent history, branch, tags, and
    relevant version metadata. Preserve existing local work.
2.  Lock the sub-version's scope, dependencies, allowed files,
    acceptance criteria, and test plan before editing.
3.  Trace the relevant GUI/service/repository/schema path and inspect
    existing tests before implementing.
4.  Implement only the current topic; do not bundle unrelated refactors
    or future-version work.
5.  Run focused tests, then relevant regression tests and live MySQL or
    manual GUI checks when required.
6.  Review test output, database-target safety, changed files, secrets,
    and the final diff.
7.  Record acceptance as `PASS`, `PARTIAL`, `FAIL`, or `BLOCKED`. Make a
    local topic commit only after the relevant acceptance criteria pass.
8.  Do not push, tag, or publish a release while the main milestone is
    incomplete. Release steps happen only after the milestone-wide
    acceptance and release gate pass.

Useful review commands:

```powershell
git status --short
git log --oneline --decorate -12
git diff --check
git diff -- README.md
```

Do not use destructive Git commands to clear line-ending noise or
simplify the working tree. Review changes before staging or committing.

## Security and Data Integrity

- Keep `.env` and local database credentials out of Git and public
  archives.
- Use parameterized SQL for supplied values.
- Use least-privileged database accounts.
- Keep the application database separate from migration and
  integration-test databases.
- Preserve the integrity of real transactions when changing inventory
  or procurement behavior.
- Do not invent package conversions, units, or price bases; use
  explicitly defined business rules and stored evidence.
- Treat source files, schema definitions, requirements, and roadmap
  entries as different kinds of evidence. A design document or planned
  feature is not proof of a completed end-to-end workflow.

---

Update this README when verified implementation or project workflow
changes. Keep status statements aligned with the current repository and
roadmap; do not describe planned, untested, or unreleased work as
complete.

## License

License information has not yet been specified in this repository.
Add the intended license before publishing a public release.
