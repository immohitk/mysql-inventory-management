# Supplier Offer Service Contract

## Purpose and Scope

This document describes the existing supplier-offer service, repository, and review-persistence interfaces. These are application/database interfaces, not a REST API.

Supplier-offer CRUD and supplier-offer review are separate workflows. Updating an offer does not overwrite its review record.

## Supplier Offer CRUD

Implementation: `app/services/supplier_offer_service.py`

### Create an offer

`SupplierOfferService.create_offer(supplier_id, product_id, package_specification_id, minimum_order_quantity=Decimal("1.0000"), purchase_price=None, is_active=True)`

- Creates an offer and returns its new database ID.
- Supplier ID, product ID, and package specification ID must be positive integers; Boolean values are rejected.
- Minimum order quantity must be at least `0.0001`, with no more than four decimal places.
- Purchase price is required, must be non-negative, and may have at most two decimal places.
- `is_active` must be a Boolean.
- Duplicate supplier/product/package combinations raise `ValueError`.
- Missing referenced supplier, product, or package specification raises `ValueError`.
- Database errors not explicitly translated by the service propagate to the caller.

### Read offers

- `get_offer(offer_id)` returns one offer or `None` if it does not exist.
- `get_all_offers(active_only=False)` returns offers ordered by ID, optionally restricted to active offers.
- `get_offers_by_supplier(supplier_id, active_only=False)` returns offers for a supplier.
- `get_offers_by_product(product_id, active_only=False)` returns offers for a product.

IDs must be positive integers. `active_only` must be a Boolean. Invalid arguments raise `ValueError`.

The repository selects these columns: `id`, `supplier_id`, `product_id`, `package_specification_id`, `minimum_order_quantity`, `purchase_price`, `is_active`, `created_at`, and `updated_at`. Read methods close their cursors after fetching results.

Implementation: `app/repositories/supplier_offer_repository.py`

The repository requires a database connection wrapper. It uses parameterized SQL for supplied ID values.

### Update an offer

`SupplierOfferService.update_offer(offer_id, supplier_id, product_id, package_specification_id, minimum_order_quantity, purchase_price, is_active=True)`

Updates offer details and returns the database's affected-row count. If no rows are reported as changed, the service checks whether the offer exists; an unchanged existing offer is not treated as missing.

A nonexistent offer raises `ValueError`. Invalid fields, duplicate offer combinations, and missing referenced records also raise `ValueError`. Other database errors propagate.

The update preserves the separate review record.

### Activate and deactivate

- `activate_offer(offer_id)` sets the offer's active state to `True`.
- `deactivate_offer(offer_id)` sets the offer's active state to `False` without deleting its history.

Both return the affected-row count. A nonexistent offer raises `ValueError`; an unchanged existing state may result in zero affected rows.

### Connection ownership

`SupplierOfferService` accepts an optional database wrapper. If it creates the connection itself, `close()` closes that connection. If a wrapper is injected, `close()` does not close the caller-owned connection.

## Supplier Offer Review Persistence

Implementation: `database/supplier_offer_review_service.py`

Interface:

`save_review(database: str, offer_id: int, review: SupplierOfferReview) -> None`

The function persists a validated review and returns no value on success.

### Validation and review data

- The database name must match `inventory_migration_[A-Za-z0-9_]+`.
- The offer ID must be a positive integer; Boolean values are rejected.
- Review data is validated using `validate_review()` from `database.supplier_offer_approval`.
- Review evidence includes package evidence, price evidence, and minimum-order-quantity evidence.
- The review also stores its decision/status, reviewer, review notes, and a database-generated review timestamp.

The review schema supports `PENDING`, `APPROVED`, and `REJECTED`; the supplied review must pass the schema's validation.

### Persistence behavior

1. Check whether a review already exists for the offer.
2. Reject an existing review rather than overwrite it.
3. Insert a review only when the referenced supplier offer exists.
4. Query the database again to verify the review count.

Invalid database names, invalid IDs, invalid review data, existing reviews, and a post-insert check that finds no review raise ValueError. Database command failures, non-numeric query results, and a post-insert count other than one raise RuntimeError. If the post-insert check finds no review, the service raises `ValueError`; if it finds more than one, it raises `RuntimeError`.

## Database Safety

The review-persistence service is restricted by an application-level database-name check to the `inventory_migration_*` naming convention. Use an isolated, disposable test database for integration testing.

**Never run integration tests or review-service operations against `inventory_db`.**

## Testing

Run the focused review tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_supplier_offer_review_service.py tests\test_supplier_offer_review_schema.py -q
```

Run the complete test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

MySQL integration tests require the project's explicit integration-test configuration and an isolated disposable test database. Confirm the integration-test environment and safety checks before running them.
