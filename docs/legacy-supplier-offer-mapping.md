# Legacy Supplier Offer Mapping Register

**Roadmap:** v0.4.2.7 - Package and supplier offer mapping
**Status:** IN PROGRESS
**Source:** `inventory_migration_final_v042`, an isolated restored test database
**Safety:** The original `inventory_db` must remain untouched.

## Purpose

Record each legacy product's current supplier association and `cost_price` as candidate source data for supplier-offer migration. These values are not automatically approved as complete supplier offers.

This register must record verified evidence, unresolved assumptions, and the decision for each candidate before any offer is created.

## Mapping Rules

- Preserve the original source values in this register.
- Treat the current product supplier as a candidate association, not proof of a valid offer.
- Do not treat `cost_price` as a verified package price until its price basis is confirmed.
- Do not assume package size, inventory unit, or minimum order quantity.
- Do not create an offer when required mapping details remain unknown.
- Preserve historical purchase suppliers, unit costs, subtotals, and totals.
- Perform all migration tests only in an isolated database.

## Candidate Product Mapping

| Product ID | SKU      | Product            | Current Supplier        | Source Cost Price | Price Basis | Inventory Unit | Package Specification | MOQ     | Status           |
| ---------: | -------- | ------------------ | ----------------------- | ----------------: | ----------- | -------------- | --------------------- | ------- | ---------------- |
|          1 | ELEC-001 | Wireless Keyboard  | TechSource Supplies     |            850.00 | UNVERIFIED  | UNVERIFIED     | UNKNOWN               | UNKNOWN | PENDING EVIDENCE |
|          2 | ELEC-002 | Wireless Mouse     | TechSource Supplies     |            450.00 | UNVERIFIED  | UNVERIFIED     | UNKNOWN               | UNKNOWN | PENDING EVIDENCE |
|          3 | COMP-001 | USB-C Hub          | TechSource Supplies     |            900.00 | UNVERIFIED  | UNVERIFIED     | UNKNOWN               | UNKNOWN | PENDING EVIDENCE |
|          4 | COMP-002 | HDMI Cable         | TechSource Supplies     |            180.00 | UNVERIFIED  | UNVERIFIED     | UNKNOWN               | UNKNOWN | PENDING EVIDENCE |
|          5 | OFF-001  | Notebook           | OfficeMart Distributors |             60.00 | UNVERIFIED  | UNVERIFIED     | UNKNOWN               | UNKNOWN | PENDING EVIDENCE |
|          6 | OFF-002  | Ballpoint Pen Pack | OfficeMart Distributors |             45.00 | UNVERIFIED  | UNKNOWN        | UNKNOWN               | UNKNOWN | PENDING EVIDENCE |
|          7 | HOME-001 | Electric Kettle    | HomeTech Wholesale      |           1100.00 | UNVERIFIED  | UNVERIFIED     | UNKNOWN               | UNKNOWN | PENDING EVIDENCE |
|          8 | HOME-002 | Table Fan          | HomeTech Wholesale      |           1250.00 | UNVERIFIED  | UNVERIFIED     | UNKNOWN               | UNKNOWN | PENDING EVIDENCE |

**Important:** Source Cost Price records the legacy `products.cost_price` value only. It does not establish the price per individual item, package, or order. No supplier offer is approved by this table.

## Evidence Required Before Approval

For each candidate product, record the evidence and decision for:

1. **Inventory unit:** Confirm how stock and reorder level are counted.
2. **Package specification:** Confirm the package form and exact contents in the inventory base unit.
3. **Price basis:** Confirm whether the legacy cost price applies to one item, one package, or another defined quantity.
4. **Minimum order quantity:** Confirm the minimum number of packages or other explicitly defined order unit.
5. **Supplier association:** Confirm that the supplier is valid for the proposed offer.
6. **Target references:** Validate supplier, product, and package-specification IDs in the isolated target database.

Product names, current supplier associations, and legacy cost prices alone are not sufficient evidence to approve an offer.

## Acceptance Checklist

- [ ] All eight source products and their candidate supplier associations are recorded.
- [ ] Every candidate has documented inventory-unit evidence or remains explicitly unresolved.
- [ ] Every package specification and its contents are explicitly verified.
- [ ] Every proposed offer price has a verified price basis.
- [ ] Every minimum order quantity has a verified meaning.
- [ ] Unresolved candidates are excluded from offer creation and documented.
- [ ] Proposed mappings are tested only in an isolated database.
- [ ] Historical purchase suppliers, unit costs, subtotals, and totals remain unchanged.
- [ ] The original `inventory_db` remains untouched.

## Current Status

**Status: IN PROGRESS.** The source candidate values have been recorded, but no candidate offer is approved. Package details, inventory units, price bases, and minimum order quantities still require evidence. No supplier offers should be created from this register until the relevant mapping is verified.

## Source Description Review

The eight product descriptions were inspected in the isolated database `inventory_migration_final_v042`.

- **ELEC-001 — Wireless Keyboard:** "Compact wireless keyboard"; no package quantity or price basis stated.
- **ELEC-002 — Wireless Mouse:** "Ergonomic wireless mouse"; no package quantity or price basis stated.
- **COMP-001 — USB-C Hub:** "Multi-port USB-C connectivity hub"; no package quantity or price basis stated.
- **COMP-002 — HDMI Cable:** "High-speed HDMI cable"; no package quantity or price basis stated.
- **OFF-001 — Notebook:** "A5 ruled notebook"; format is described, but inventory unit, package quantity, and price basis remain unverified.
- **OFF-002 — Ballpoint Pen Pack:** "Pack of blue ballpoint pens"; the number of pens per pack is not stated.
- **HOME-001 — Electric Kettle:** "1.5 litre electric kettle"; the capacity does not establish the inventory unit or supplier package contents.
- **HOME-002 — Table Fan:** "Compact table fan"; no package quantity or price basis stated.

**Review result:** Product descriptions do not provide enough evidence to approve supplier offers. Inventory units, package specifications, price bases, and minimum order quantities remain unresolved. No offers are approved by this review.
