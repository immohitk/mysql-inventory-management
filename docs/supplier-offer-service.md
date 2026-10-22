# Supplier Offer Review Service

## Purpose

The supplier offer review service records review evidence and review decisions for supplier offers. It validates review input and checks the database before creating a review record.

## Review Data

A review may include:

- Package evidence
- Price evidence
- Minimum order quantity (MOQ) evidence
- Review status
- Reviewer
- Review notes

The review schema supports the statuses `PENDING`, `APPROVED`, and `REJECTED`.

## Validation and Persistence

The service validates the supplied database name, supplier offer ID, and review data before attempting to persist a review.

It checks whether a review already exists for the supplier offer and refuses to overwrite an existing review. It then inserts the review only when the referenced supplier offer exists and performs a follow-up query to verify persistence.

Database execution failures are reported as runtime errors, while invalid input and review-state conflicts are reported as value errors.

## Database Safety

The service accepts only database names matching the `inventory_migration_*` test-database naming convention. Use an isolated test database configured for integration testing.

**Never run integration tests or review-service operations against `inventory_db`.**

## Testing

Run the focused unit tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_supplier_offer_review_service.py tests\test_supplier_offer_review_schema.py -q
```

Run the full test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

MySQL integration tests require the project's explicit integration-test configuration and an isolated disposable test database.
