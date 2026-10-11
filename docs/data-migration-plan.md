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

- [ ] Category records preserved.
- [ ] Supplier records preserved.
- [ ] Product records preserved.
- [ ] Purchase records preserved.
- [ ] Purchase-item records preserved.
- [ ] Sales records preserved if present.
- [ ] Sale-item records preserved if present.
- [ ] Existing identifiers and relationships preserved where required.

### Financial integrity

- [ ] Historical purchase `unit_cost` values preserved.
- [ ] Historical purchase `subtotal` values preserved.
- [ ] Purchase `total_amount` values preserved.
- [ ] Purchase totals reconcile with item subtotals.
- [ ] No historical supplier is inferred from the current product supplier.
- [ ] No current offer price overwrites historical purchase costs.

### Schema integrity

- [x] All required target tables exist in the isolated test database.
- [x] Foreign keys were inspected and tested for the package-content parent relationship.
- [x] Unique constraints were tested for duplicate supplier offers.
- [x] Check constraints were tested for package quantity, supplier-offer price, and minimum order quantity.
- [x] Package specifications reference valid package forms.
- [x] Package contents have valid references and explicit quantities.
- [x] Supplier offers reference valid suppliers, products, and package specifications.
- [ ] No unsupported unit or package conversion is introduced.

### Recovery

- [x] Backup was restored successfully into isolated test databases and source row counts matched the expected baseline.
- [x] A controlled migration failure was reproduced; the test confirmed that earlier DDL changes remained after the error.
- [x] Restoration into a fresh recovery database was tested, and migrations `001` and `002` completed successfully afterward.
- [x] Original database was not modified by the isolated tests.

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

**Status: Schema migration tested in an isolated database; data migration remains incomplete.**

The following work has been completed:

- The original source database was backed up and restored into an isolated test database.
- Baseline row counts were verified: categories 4, suppliers 3, products 8, purchases 16, purchase_items 20, sales 0, and sale_items 0.
- Migration scripts `001` and `002` were executed in the isolated test database.
- The new procurement tables and their foreign keys, unique constraints, and check constraints were inspected.
- Tests confirmed that invalid package quantities, cross-specification parent references, duplicate supplier offers, negative offer prices, and zero minimum order quantities are rejected.
- Original table row counts remained unchanged after the schema migrations.
- Aggregate purchase totals and purchase-item subtotals both equal 44,805.00.
- No individual purchase-total mismatch was returned by the reconciliation query.
- A controlled migration failure was simulated in an isolated test database using a duplicate `supplier_offers` table. The migration failed as expected, and previously created tables remained, confirming that earlier DDL changes were not automatically rolled back.
- The verified backup was restored into a separate recovery database. Migrations `001` and `002` then completed successfully, and all seven source-table row counts matched the expected baseline.
- Final migration scripts were revalidated in a fresh isolated database. Migrations 001 and 002 executed successfully, source row counts remained unchanged, and the new tables' constraints and indexes were inspected.
- Historical purchase headers and purchase-item records were compared row by row against the backup in the isolated recovery database. All 16 purchase records and 20 purchase-item records matched after normalizing the backup's quote formatting.

Remaining work:

- Implement and test explicit data mappings for inventory units, package contents, and supplier offers.
- Review unresolved package, unit, and initial-offer assumptions.
- Complete documentation and the remaining validation checklist.

The original `inventory_db` has not been modified by these tests. No production data migration has been performed.

Do not consider v0.4.2 complete until the remaining migration, preservation, and recovery checks have passed.
