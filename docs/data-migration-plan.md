# Data Migration Plan

## 1. Purpose

This document defines the migration strategy for moving the existing inventory database toward the proposed procurement schema introduced in `v0.4.1`.

The goal of `v0.4.2` is to plan, implement, and validate data migration while preserving existing inventory data and historical purchase records.

## 2. Migration Scope

The source database contains seven tables:

- `categories`
- `suppliers`
- `products`
- `purchases`
- `purchase_items`
- `sales`
- `sale_items`

The proposed procurement design introduces:

- `units`
- `unit_conversions`
- `package_forms`
- `package_specifications`
- `package_contents`
- `supplier_offers`

The target product design also proposes inventory base units and fractional stock quantities.

The migration must preserve existing category, supplier, product, purchase, and sales data. Existing tables must not be destructively replaced before the migrated data has been validated.

## 3. Source Database Baseline

The following baseline was captured from `inventory_db` during read-only inspection.

| Table            | Existing row count |
| ---------------- | -----------------: |
| `categories`     |                  4 |
| `suppliers`      |                  3 |
| `products`       |                  8 |
| `purchases`      |                 16 |
| `purchase_items` |                 20 |
| `sales`          |                  0 |
| `sale_items`     |                  0 |

These counts are the reference values for the inspected database at the time of planning. They must be recaptured immediately before migration because the live database may change.

## 4. Verified Source Data Rules

- Product SKUs are unique.
- Products currently reference one supplier through `products.supplier_id`.
- Purchases reference suppliers through `purchases.supplier_id`.
- Purchase items store quantity, historical `unit_cost`, and historical `subtotal`.
- Purchases store `total_amount` and `status`.
- All 16 inspected purchases had status `COMPLETED`.
- The purchase-item orphan check returned zero rows.
- The purchase-total validation query returned no mismatches at a tolerance of `0.01`.
- Sales and sale-item tables were empty during the baseline inspection.

These observations describe the inspected database and must be verified again before migration.

## 5. Important Historical Supplier Differences

The source data contains seven purchase items where the supplier recorded on the purchase differs from the product's current supplier.

The differences occur in purchase IDs `17`, `20`, and `24`.

This does not automatically mean the records are invalid. Products may have been purchased from suppliers other than their currently associated supplier.

Migration rules:

- Preserve each historical `purchases.supplier_id`.
- Preserve each historical `purchase_items.unit_cost`.
- Preserve each historical `purchase_items.subtotal`.
- Do not derive historical suppliers from the current `products.supplier_id`.
- Do not overwrite historical purchase costs using current product costs or new supplier offers.

## 6. Proposed Data Mapping

The following mapping is a proposal and must be implemented and tested before production use.

| Source data              | Proposed target mapping                         | Notes                                                                         |
| ------------------------ | ----------------------------------------------- | ----------------------------------------------------------------------------- |
| `categories`             | Existing categories table                       | Preserve IDs and values                                                       |
| `suppliers`              | Existing suppliers table                        | Preserve IDs and values                                                       |
| `products.sku`           | Target product SKU/code                         | Preserve the existing unique SKU                                              |
| `products.name`          | Target product name                             | Preserve existing values                                                      |
| `products.description`   | Target product description                      | Preserve nullable values                                                      |
| `products.selling_price` | Target product selling price                    | Preserve existing values                                                      |
| `products.quantity`      | Target fractional stock quantity                | Convert numeric representation without inventing fractional precision         |
| `products.reorder_level` | Target fractional reorder level                 | Preserve the existing numeric value                                           |
| `products.supplier_id`   | Initial supplier association and proposed offer | Validate package and price assumptions before creating offers                 |
| `products.cost_price`    | Candidate initial supplier-offer price          | Confirm the meaning of this field before treating it as a current offer price |
| `purchases`              | Existing purchase history                       | Preserve purchase IDs, suppliers, dates, totals, and statuses                 |
| `purchase_items`         | Existing purchase history                       | Preserve item IDs, product references, quantities, unit costs, and subtotals  |
| `sales`                  | Existing sales history                          | Preserve records if present at migration time                                 |
| `sale_items`             | Existing sales history                          | Preserve records if present at migration time                                 |

Final mappings must match the actual target schema and migration implementation.

## 7. Unit and Package Mapping

Existing product names do not provide enough information to determine inventory units or package configurations reliably.

For example, a product described as a pack does not establish how many pieces it contains.

Therefore:

- Do not guess inventory units from product names.
- Do not invent package sizes.
- Do not assume unit conversions without explicit definitions.
- Do not create package-content records without verified quantities.
- Document unresolved product units and package details before completing migration.

Any missing unit or package information must be resolved explicitly or handled through a documented migration exception.

### Legacy Package Mapping Register

The following register records the current mapping status. It is a review register, not an approved source of package data.

| Legacy product                 | Inventory unit | Package specification | Package contents | Status  | Evidence required                                                 |
| ------------------------------ | -------------- | --------------------- | ---------------- | ------- | ----------------------------------------------------------------- |
| Wireless Keyboard (`ELEC-001`) | Unverified     | Unverified            | Unverified       | PENDING | Verified stock unit, package definition and quantity basis        |
| Wireless Mouse (`ELEC-002`)    | Unverified     | Unverified            | Unverified       | PENDING | Verified stock unit, package definition and quantity basis        |
| USB-C Hub (`COMP-001`)         | Unverified     | Unverified            | Unverified       | PENDING | Verified stock unit, package definition and quantity basis        |
| HDMI Cable (`COMP-002`)        | Unverified     | Unverified            | Unverified       | PENDING | Verified stock unit, package definition and quantity basis        |
| Notebook (`OFF-001`)           | Unverified     | Unverified            | Unverified       | PENDING | Verified stock unit, package definition and quantity basis        |
| Ballpoint Pen Pack (`OFF-002`) | Unverified     | Unverified            | Unverified       | PENDING | Verified stock unit and evidence of the number of pieces per pack |
| Electric Kettle (`HOME-001`)   | Unverified     | Unverified            | Unverified       | PENDING | Verified stock unit, package definition and quantity basis        |
| Table Fan (`HOME-002`)         | Unverified     | Unverified            | Unverified       | PENDING | Verified stock unit, package definition and quantity basis        |

**Approval rules**

- Do not infer a stock unit or package size from a product name.
- Record the source document or other verifiable evidence for every proposed mapping.
- Keep unsupported mappings pending; do not create corresponding package-content records.
- Approve a mapping only after its unit, quantity and package meaning have been reviewed.
- Record exceptions explicitly rather than silently substituting assumptions.

## 8. Supplier Offer Migration

The existing product-to-supplier relationship can provide a starting point for initial supplier offers.

The inspected source has eight products across three suppliers:

- TechSource Supplies: four products
- OfficeMart Distributors: two products
- HomeTech Wholesale: two products

Eight initial offer records are a possible mapping, not an automatic guarantee.

Before creating an offer, verify:

- The source `cost_price` is suitable as the initial offer price.
- The package specification is explicitly defined.
- The package's inventory-unit contents are known.
- The package price and minimum order quantity have valid meanings.
- The supplier, product, and package specification references are valid.

Historical purchases must not be rewritten to match these initial offers.

**Offer Mapping Rules**

- Treat each legacy product's supplier association as a candidate, not as proof that a complete offer can be created.
- Do not copy `products.cost_price` into `supplier_offers.purchase_price` until the price basis is confirmed.
- Require an explicitly defined package specification and verified package contents in the product's inventory base unit.
- Confirm that the price applies to one complete package and that the minimum order quantity means the number of those packages.
- Validate supplier, product, and package specification references in the isolated target database.
- If the unit, package size, price basis, or minimum-order meaning is unknown, do not create the offer. Record the unresolved mapping and evidence needed.
- Never use a current supplier offer to rewrite historical purchases, purchase-item `unit_cost`, `subtotal`, or purchase totals.
- Test proposed mappings only in an isolated database. Do not run these steps against the original `inventory_db`.

These rules define the mapping procedure; they do not approve any of the eight candidate offers or verify legacy package sizes, inventory units, prices, or minimum order quantities.

## 9. Migration Safety Strategy

The migration must be tested against a separate test database, not the live `inventory_db`.

Required sequence:

1. Capture a fresh source baseline.
2. Create and verify a recoverable database backup.
3. Create an isolated migration test database.
4. Apply the target schema to the test database.
5. Run the migration using explicit, documented mappings.
6. Validate record counts, identifiers, relationships, and financial values.
7. Test failure handling and rollback.
8. Review all migration exceptions.
9. Document the results before considering production migration.

The live database must remain unchanged during planning and test migration.

## 10. Validation Checklist

### Record preservation

- [x] Category, supplier, product, purchase, purchase-item, sales, and sale-item row counts matched the baseline after migrations in the latest fresh recovery database.
- [x] All 16 historical purchase records and 20 purchase-item records matched the backup in the previously documented row-by-row comparison.
- [x] Legacy product mapping fields were compared against the source in the previously verified isolated snapshot database, with zero mismatches across the documented fields.
- [ ] Complete field-by-field preservation comparison for every legacy table in the latest fresh recovery database.
- [ ] Existing identifiers and relationships individually verified wherever required.

### Financial integrity

- [x] Historical purchase headers and purchase-item records matched the backup in the previously documented row-by-row comparison.
- [x] Purchase headers and item subtotals both total `44,805.00` in the latest fresh recovery database.
- [x] The latest purchase reconciliation reported zero purchase-total mismatches.
- [ ] Complete field-by-field comparison of historical purchase `unit_cost`, `subtotal`, and `total_amount` values in the latest fresh recovery database.
- [x] No historical supplier was inferred solely from the current product-supplier relationship during mapping.
- [x] No current supplier-offer price was used to overwrite historical purchase costs.

### Schema integrity

- [x] All required target tables exist in the isolated test database.
- [x] Foreign keys were inspected and tested for the package-content parent relationship.
- [x] Unique constraints were tested for duplicate supplier offers.
- [x] Check constraints were tested for package quantity, supplier-offer price, and minimum order quantity.
- [x] Package specifications reference valid package forms.
- [x] Package contents have valid references and explicit quantities where records exist.
- [x] Supplier offers reference valid suppliers, products, and package specifications where records exist.
- [ ] No unsupported unit or package conversion is introduced.
- [ ] Actual inventory-unit, package-content, and supplier-offer mappings verified against reliable source evidence.

### Recovery

- [x] Verified backup restored successfully into isolated recovery databases.
- [x] A controlled migration failure was reproduced; earlier DDL changes remained after the error, confirming that MySQL did not automatically roll them back.
- [x] Migrations `001` through `004` completed successfully in the latest fresh recovery database.
- [x] A second migration-runner execution skipped all four recorded migrations.
- [x] The migration runner rejected `inventory_db` at database-name validation before executing migration SQL.
- [x] The original database was not modified by the isolated tests.
- [ ] Complete recovery procedure for a partially applied migration documented and tested, including cleanup before retrying.

## 11. Rollback Strategy

Do not rely solely on transaction rollback for the entire migration. MySQL schema changes may cause implicit commits.

The migration process must use a verified backup and an isolated test database. Test failures should be resolved in the test environment.

Production migration must not begin until the restoration procedure has been tested and the migration results have been reviewed.

## 12. Completion Criteria

The `v0.4.2` migration milestone is complete only when:

- The migration implementation is documented and tested.
- All source records are accounted for.
- Historical purchase data and supplier references are preserved.
- Financial validation checks pass.
- Unit and package mappings are explicit and defensible.
- Migration failures and recovery have been tested.
- The migration is repeatable or safely rejects an unintended second execution.
- Documentation accurately records any unresolved limitations.

## 13. Current Status

**Status: IN PROGRESS — schema migration and isolated recovery tests have passed; business-data mapping and final preservation checks remain incomplete.**

### Completed implementation and validation

- The original source database was backed up and restored into isolated test databases. The original `inventory_db` was not modified.
- The source baseline contained 4 categories, 3 suppliers, 8 products, 16 purchases, 20 purchase items, 0 sales, and 0 sale items.
- Migrations `001` through `004` were applied successfully in the fresh recovery database `inventory_migration_recovery_v042_final`.
- A second migration-runner execution skipped all four migrations because they were already recorded in `schema_migrations`.
- The latest recovery test preserved all seven legacy table row counts.
- Historical purchase headers and purchase-item records matched the backup in the previously documented row-by-row comparison: 16 purchases and 20 purchase items.
- In the latest recovery database, purchase totals and item subtotals both equaled `44,805.00`, with zero purchase-total mismatches.
- Migration `003_create_legacy_product_mapping.sql` captured all 8 legacy products. Previously documented field-level verification in `inventory_migration_snapshot_v043` found zero mismatches across category ID, supplier ID, SKU, name, description, cost price, selling price, quantity, reorder level, and creation/update timestamps.
- The legacy product mapping migration was rerun without duplicating mapping records. Migrations already recorded by the runner were skipped on subsequent runs.
- The migration runner rejected the protected database name `inventory_db` before executing migration SQL.
- A controlled migration failure was reproduced in an isolated database. Earlier DDL changes remained after the error, confirming that MySQL does not automatically roll back all schema changes.
- Schema constraints and indexes were inspected, and tests covered invalid package quantities, invalid parent relationships, duplicate supplier offers, negative offer prices, and invalid minimum order quantities.
- Supplier-offer review safeguards require evidence for approval and a reason for rejection. The review service prevents an existing review from being overwritten.
- The latest recovery database passed `database/validate_mappings.py`: all 8 source products have mapping records, with no missing product references, invalid statuses, or pending mappings without notes.

### Recovery evidence

The fresh recovery database was restored from `inventory_db_before_v042_test_restore.sql`. Its restore-friendly backup SHA-256 was verified twice:

`F886E70328C112ECD8A3D530FC0F216A42108590CBB6899F3B8A4B13A1FB2A8C`

The recovery test establishes matching legacy row counts, successful application of migrations `001`–`004`, migration-runner repeatability, and aggregate purchase reconciliation. It does not establish complete field-by-field preservation for every legacy table in this specific recovery database.

MySQL DDL may remain partially applied after a migration failure. The runner does not automatically restore the database or clean up every partial failure; the recovery procedure must account for this limitation.

### Outstanding blockers

- All 8 legacy product mappings remain `PENDING`, with `inventory_unit_id` unset.
- Inventory units, package sizes, package contents, and unit conversions have not been verified against reliable source evidence.
- `database/validate_package_contents.py` correctly returns `BLOCKED` because no package specifications or package contents exist in the recovery database.
- `database/validate_supplier_offers.py` correctly returns `BLOCKED` because no supplier offers exist in the recovery database.
- The legacy `products.cost_price` field has not been established as a verified current supplier-offer price.
- Supplier-offer package prices and minimum order quantities have not been verified.
- Complete field-by-field preservation checks for every legacy table in the latest recovery database remain outstanding.
- Recovery and cleanup of a partially applied migration still require a documented, tested procedure.

The validators verify structural rules and recorded review requirements. They do not independently authenticate evidence or prove that proposed business mappings reflect the real products and supplier terms.

### Remaining work

1. Obtain reliable source evidence for inventory units, package definitions, package contents, supplier-offer prices, and minimum order quantities.
2. Document and review explicit mappings for each legacy product and any proposed initial supplier offer.
3. Implement and test only mappings supported by that evidence. Keep unsupported mappings pending.
4. Complete field-by-field preservation checks and verify required identifiers, relationships, historical costs, subtotals, and totals in the latest recovery database.
5. Document and test recovery from a partially applied migration, including safe cleanup before retrying.
6. Reconcile every validation checklist item against recorded test evidence.
7. Re-run the test suite and documentation checks before considering the milestone complete.

**Completion decision:** `v0.4.2` remains in progress. Do not perform a production data migration, approve unsupported mappings, or mark the milestone complete until the outstanding evidence and validation requirements have been satisfied.

The original `inventory_db` remains unchanged by these tests. No production data migration has been performed.
