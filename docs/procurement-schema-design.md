# Procurement Schema Design

**Version:** 0.4.1  
**Status:** Proposed design  
**Related schema:** `database/schema_v2.sql`

## 1. Purpose

This document describes the proposed procurement database redesign for the MySQL Inventory Management project.

The redesign separates a product's inventory unit from its supplier-specific purchase offers and package specifications. It is intended to support multiple suppliers per product and different purchasable package configurations.

**Important:** This document describes a target design. It is not a database migration guide or an executable schema. Do not execute `schema_v2.sql` against the existing `inventory_db`.

## 2. Design Goals

The proposed model must:

- Give each product a fixed inventory unit.
- Allow multiple suppliers to offer the same product.
- Allow different package specifications for purchasable products.
- Store explicit package contents and quantities.
- Avoid guessing undefined unit conversions.
- Preserve historical purchase costs and subtotals.
- Keep schema redesign separate from data migration and application refactoring.

## 3. Units and Measurement Conversions

### 3.1 Units

The `units` table stores measurement units such as:

- Mass: kilogram (`kg`), gram (`g`)
- Volume: litre (`litre`), millilitre (`ml`)
- Count: piece, bottle, egg

Each unit has a name, unique code and unit type.

Packaging forms such as carton, sack, box, bag and bottle are represented separately in `package_forms`.

### 3.2 Explicit conversions

The `unit_conversions` table stores directed conversion factors between units. The `conversion_factor` means the number of target units equivalent to one source unit.

For example, a conversion from kilograms to grams can explicitly define a factor of `1000`, meaning `1 kg = 1000 g`.

Application logic must:

- Reject conversions between incompatible unit types.
- Reject same-unit conversion definitions.
- Reject conversions that have not been defined or cannot be derived safely.
- Never infer mass-to-volume conversions without an explicitly supported rule.

The database enforces a positive conversion factor and uniqueness of each directed unit pair. Same-unit and dimensional compatibility validation are application responsibilities.

Packaging conversions must be derived from package contents rather than guessed from unit names.

## 4. Product Inventory Unit

Each product has one inventory unit, represented by `inventory_unit_id` in the proposed target product design.

Stock quantity and reorder level use `DECIMAL(14, 4)` so fractional inventory can be represented.

The target product definition is reference material only. The existing `products` table must not be replaced or altered during this milestone.

The proposed target product design removes `supplier_id` and `cost_price` from the product record because purchase offers are supplier-specific. Existing data must be preserved until the migration plan is designed and verified.

## 5. Package Forms and Specifications

The `package_forms` table stores packaging types such as carton, sack, box, bag and bottle.

The `package_specifications` table identifies a purchasable package configuration associated with a package form.

Examples include:

- A sack containing 25 kg of rice.
- A carton containing 20 bottles, each containing 1 litre.

A package specification describes the package offered for purchase. Its contents are represented separately in `package_contents`.

## 6. Package Contents

The `package_contents` table stores the quantity and unit of each component within a package specification.

It supports nested package contents through `parent_content_id`.

For example, a carton may contain 20 bottles, with each bottle containing 1 litre. The root row represents the quantities in one complete package. A child row's quantity represents the amount per one unit of its parent component, and the parent's quantity scales that amount. In this example, 20 bottles multiplied by 1 litre per bottle gives 20 litres. Quantities and units must be explicitly represented and interpreted consistently by application logic.

Application validation must:

- Ensure parent and child contents belong to the same package specification.
- Prevent circular parent-child hierarchies.
- Require positive quantities.
- Validate compatible units and package relationships.
- Calculate the resulting quantity in the product's inventory unit only when the required conversion rules are explicitly available.

The foreign keys enforce referential relationships, but they do not independently guarantee cycle prevention or valid conversion to a product's inventory unit.

## 7. Supplier Offers

The `supplier_offers` table connects a supplier, a product and a package specification.

An offer includes:

- `supplier_id`
- `product_id`
- `package_specification_id`
- `minimum_order_quantity`
- `purchase_price`
- `is_active`

`purchase_price` represents the price for one complete package specification.

`minimum_order_quantity` represents the minimum number of those packages required for the offer.

The proposed constraints prevent duplicate offers for the same supplier, product and package specification, reject non-positive minimum order quantities, and reject negative prices.

Application logic must also ensure that the selected package specification is meaningful for the product's inventory unit.

## 8. Historical Purchase Records

Existing purchase records must remain intact during the redesign.

In particular:

- Preserve `purchase_items.unit_cost`.
- Preserve `purchase_items.subtotal`.
- Treat historical purchase values as snapshots of the original transaction.
- Do not recalculate historical purchase values using current supplier offers.

Integrating supplier offers into the purchase workflow belongs to version `0.4.5`, not this schema-design milestone.

## 9. Migration Boundary

Version `0.4.1` defines the proposed schema design only.

Version `0.4.2` is responsible for planning and validating data migration.

Until migration is separately implemented and verified:

- Do not execute the target product definition.
- Do not drop `products.supplier_id`.
- Do not drop `products.cost_price`.
- Do not modify the existing `inventory_db` to match this draft.
- Preserve existing categories, suppliers, products, purchases, purchase items, sales and sale items.

The original `database/schema.sql` remains the reference for the existing database schema.

## 10. Validation and Testing Boundary

The redesigned tables were tested in a separate temporary database during development. Successful table creation validates the tested SQL definitions and constraints, but does not prove that all business rules are enforced.

Application-level validation and automated tests will be needed for:

- Unit compatibility and same-unit conversion rejection.
- Undefined conversions.
- Package hierarchy cycles.
- Package-to-inventory quantity calculations.
- Supplier offer and package compatibility.
- Preservation of historical purchase values.

These behaviours must be tested when the corresponding services and migration are implemented.

## 11. Related Roadmap

The procurement redesign follows the established project roadmap:

- `0.4.1` — Schema redesign
- `0.4.2` — Data migration
- `0.4.3` — Supplier Offer service
- `0.4.4` — Package & unit logic
- `0.4.5` — Purchase refactor
- `0.4.6` — Purchase GUI
- `0.4.7` — Stock-in refactor
- `0.5.0` — QA & docs

The roadmap order and version numbers remain unchanged.
