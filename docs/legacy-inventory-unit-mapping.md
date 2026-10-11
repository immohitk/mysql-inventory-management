# Legacy Inventory Unit Mapping Register

**Roadmap:** v0.4.2.6 — Create a legacy mapping register  
**Status:** IN PROGRESS  
**Source:** `inventory_migration_final_v042`, an isolated restored test database  
**Safety:** The original `inventory_db` must remain untouched.

## Purpose

Record each legacy product's proposed inventory base unit and the known limitations of the legacy quantity fields. Product descriptions and names alone do not prove how `quantity` or `reorder_level` was measured.

## Legacy Schema Findings

The legacy `products` table stores:
- `quantity INT UNSIGNED NOT NULL DEFAULT 0`
- `reorder_level INT UNSIGNED NOT NULL DEFAULT 0`

The schema does not store a unit for either field. Therefore, the meaning of legacy quantities must be confirmed before any production data conversion or migration.

## Product Mapping Register

| Product ID | SKU | Product | Category | Current Supplier | Legacy Quantity | Reorder Level | Proposed Base Unit | Status / Evidence |
|---:|---|---|---|---|---:|---:|---|---|
| 1 | ELEC-001 | Wireless Keyboard | Electronics | TechSource Supplies | 58 | 10 | Piece (provisional) | UNVERIFIED: unit inferred from product type; legacy quantity meaning not documented |
| 2 | ELEC-002 | Wireless Mouse | Electronics | TechSource Supplies | 60 | 15 | Piece (provisional) | UNVERIFIED: unit inferred from product type; legacy quantity meaning not documented |
| 3 | COMP-001 | USB-C Hub | Computer Accessories | TechSource Supplies | 14 | 8 | Piece (provisional) | UNVERIFIED: unit inferred from product type; legacy quantity meaning not documented |
| 4 | COMP-002 | HDMI Cable | Computer Accessories | TechSource Supplies | 54 | 20 | Piece (provisional) | UNVERIFIED: unit inferred from product type; legacy quantity meaning not documented |
| 5 | OFF-001 | Notebook | Office Supplies | OfficeMart Distributors | 75 | 25 | Piece (provisional) | UNVERIFIED: unit inferred from product type; legacy quantity meaning not documented |
| 6 | OFF-002 | Ballpoint Pen Pack | Office Supplies | OfficeMart Distributors | 143 | 30 | UNKNOWN | UNVERIFIED: cannot establish whether legacy quantities count packs or individual pens |
| 7 | HOME-001 | Electric Kettle | Home Appliances | HomeTech Wholesale | 11 | 5 | Piece (provisional) | UNVERIFIED: 1.5 litre describes kettle capacity, not the inventory quantity unit |
| 8 | HOME-002 | Table Fan | Home Appliances | HomeTech Wholesale | 6 | 5 | Piece (provisional) | UNVERIFIED: unit inferred from product type; legacy quantity meaning not documented |

## Mapping Rules

1. Proposed units are provisional until supported by reliable project or business records.
2. Do not infer a package count, conversion factor, or supplier-offer price basis from a product name or description.
3. Do not interpret the kettle's 1.5 litre capacity as its stock unit.
4. Keep the Ballpoint Pen Pack unit as UNKNOWN until it is confirmed whether stock is counted by pack or by pen.
5. Preserve legacy `quantity` and `reorder_level` values until an approved mapping is established.
6. Current product supplier associations do not override historical suppliers recorded on purchase headers.
7. Do not alter the original `inventory_db` during mapping or testing.

## Outstanding Evidence Required

- Confirm the inventory-counting unit for each product from reliable records or an explicit business decision.
- Confirm the intended meaning of `quantity` and `reorder_level`.
- Resolve whether Ballpoint Pen Pack quantities represent packs or individual pens.
- Record the evidence and decision for each mapping before marking it VERIFIED.

## Acceptance Status

- [x] All 8 legacy products listed using isolated test database records.
- [x] Legacy quantity and reorder-level fields identified from the schema.
- [x] Unverified assumptions and the pen-pack ambiguity recorded.
- [x] Every product has a provisional candidate unit or is explicitly marked UNKNOWN, with its unverified status and unresolved question recorded.
- [x] Mapping register reviewed against the legacy schema, target schema draft, and product GUI; unresolved unit decisions are documented.

**Current result:** Mapping register prepared and reviewed. All product-level unit decisions remain unverified pending explicit business confirmation; no data migration is approved by this register.


## Target Schema Alignment

The target schema requires one fixed inventory_unit_id per product and uses DECIMAL(14, 4) for quantity and reorder_level. Packaging conversions must be explicitly represented through package contents. The target design does not establish the legacy stock-counting unit for any product. Therefore, all proposed Piece units remain provisional and unverified; no unit conversion or legacy quantity transformation is approved by this register.


## Code and Schema Review

Reviewed the legacy schema, target schema draft, and product GUI. The legacy schema has no inventory-unit column, the GUI exposes generic Quantity and Reorder Level fields without a unit selector, and the target schema requires a fixed inventory unit per product. These sources do not establish the actual legacy stock-counting unit. Product-level unit decisions remain pending explicit business confirmation; proposed Piece values are not verified.




