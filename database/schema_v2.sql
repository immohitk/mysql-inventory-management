-- MySQL Inventory Management
-- Procurement Model Redesign
-- Version: 0.4.1
--
-- TARGET SCHEMA DESIGN DRAFT ONLY.
-- DO NOT EXECUTE against the existing inventory_db.
-- Data migration and ALTER statements belong to v0.4.2.
--
-- Design goals:
-- 1. Each product has a fixed inventory unit.
-- 2. A product can have offers from multiple suppliers.
-- 3. Each offer specifies a supplier, product and package.
-- 4. Package contents explicitly define their quantities.
-- 5. Undefined unit conversions must never be guessed.
-- 6. Historical purchase costs must be preserved.

-- ============================================================
-- 1. Units
-- Examples: kg, g, litre, ml, piece, bottle, egg.
-- Packaging forms such as carton and sack are stored separately.
-- ============================================================

CREATE TABLE units (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(30) NOT NULL UNIQUE,
    unit_type VARCHAR(30) NOT NULL,

    CONSTRAINT chk_units_type
        CHECK (unit_type IN ('COUNT', 'MASS', 'VOLUME'))
);

-- ============================================================
-- 2. Unit Conversions
-- Explicit, directed conversions between compatible units.
-- conversion_factor = target units per one source unit.
-- Example: from kg to g with factor 1000 means 1 kg = 1000 g.
-- Packaging conversions are defined through package contents.
-- ============================================================

CREATE TABLE unit_conversions (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    from_unit_id INT UNSIGNED NOT NULL,
    to_unit_id INT UNSIGNED NOT NULL,
    conversion_factor DECIMAL(18, 8) NOT NULL,

    CONSTRAINT fk_unit_conversions_from
        FOREIGN KEY (from_unit_id)
        REFERENCES units(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_unit_conversions_to
        FOREIGN KEY (to_unit_id)
        REFERENCES units(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT uq_unit_conversion
        UNIQUE (from_unit_id, to_unit_id),

    CONSTRAINT chk_unit_conversion_factor
        CHECK (conversion_factor > 0)
);

-- Same-unit conversion and measurement-dimension compatibility
-- must be validated by application logic.

-- ============================================================
-- 3. Package Forms
-- Examples: carton, sack, box, bag, bottle.
-- ============================================================

CREATE TABLE package_forms (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- ============================================================
-- Target Products Table Design (reference only)
--
-- Do not create this table now.
-- The existing products table will be migrated in v0.4.2.
--
-- inventory_unit_id defines the unit used for stock.
-- DECIMAL quantity supports fractional inventory.
-- supplier_id and cost_price are intentionally omitted:
-- supplier-specific purchase prices belong to supplier_offers.
-- ============================================================

-- CREATE TABLE products (
--     id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
--     category_id INT UNSIGNED NOT NULL,
--     inventory_unit_id INT UNSIGNED NOT NULL,
--     sku VARCHAR(50) NOT NULL UNIQUE,
--     name VARCHAR(150) NOT NULL,
--     description TEXT,
--     selling_price DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
--     quantity DECIMAL(14, 4) NOT NULL DEFAULT 0.0000,
--     reorder_level DECIMAL(14, 4) NOT NULL DEFAULT 0.0000,
--     created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
--         ON UPDATE CURRENT_TIMESTAMP,
--
--     CONSTRAINT fk_products_category
--         FOREIGN KEY (category_id)
--         REFERENCES categories(id)
--         ON UPDATE CASCADE ON DELETE RESTRICT,
--
--     CONSTRAINT fk_products_inventory_unit
--         FOREIGN KEY (inventory_unit_id)
--         REFERENCES units(id)
--         ON UPDATE CASCADE ON DELETE RESTRICT,
--
--     CONSTRAINT chk_products_selling_price
--         CHECK (selling_price >= 0),
--
--     CONSTRAINT chk_products_quantity
--         CHECK (quantity >= 0),
--
--     CONSTRAINT chk_products_reorder_level
--         CHECK (reorder_level >= 0)
-- );

-- ============================================================
-- 4. Package Specifications
--
-- Each specification describes one purchasable package.
-- Examples:
--   Carton containing 20 bottles, each containing 1 litre.
--   Sack containing 25 kg of loose rice.
-- ============================================================

CREATE TABLE package_specifications (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    package_form_id INT UNSIGNED NOT NULL,
    name VARCHAR(150) NOT NULL,

    CONSTRAINT fk_package_specifications_form
        FOREIGN KEY (package_form_id)
        REFERENCES package_forms(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT uq_package_specification
        UNIQUE (package_form_id, name)
);

-- ============================================================
-- 5. Package Contents
--
-- Each row describes a component quantity within a package.
-- Root rows describe quantities in one complete package.
-- A child row's quantity is per ONE unit of its parent component;
-- the parent's quantity scales the child quantity.
--
-- Example: carton of 20 bottles, each containing 1 litre:
--   Root content: quantity 20, unit bottle.
--   Child content: quantity 1, unit litre, parent = bottle row.
--   Interpreted total: 20 bottles * 1 litre per bottle = 20 litres.
--
-- Example: loose rice sack:
--   Root content: quantity 25, unit kg.
--
-- Application logic must validate hierarchy, compatible units,
-- and conversion to the product's inventory unit.
-- ============================================================

CREATE TABLE package_contents (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    package_specification_id INT UNSIGNED NOT NULL,
    parent_content_id INT UNSIGNED NULL,
    quantity DECIMAL(14, 4) NOT NULL,
    unit_id INT UNSIGNED NOT NULL,
    package_form_id INT UNSIGNED NULL,

    -- Required for the composite parent foreign key.
    CONSTRAINT uq_package_content_id_spec
        UNIQUE (id, package_specification_id),

    CONSTRAINT fk_package_contents_specification
        FOREIGN KEY (package_specification_id)
        REFERENCES package_specifications(id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    -- Parent and child must belong to the same specification.
    CONSTRAINT fk_package_contents_parent
        FOREIGN KEY (parent_content_id, package_specification_id)
        REFERENCES package_contents(id, package_specification_id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_package_contents_unit
        FOREIGN KEY (unit_id)
        REFERENCES units(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_package_contents_form
        FOREIGN KEY (package_form_id)
        REFERENCES package_forms(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT chk_package_contents_quantity
        CHECK (quantity > 0)
);

CREATE INDEX idx_package_contents_parent
    ON package_contents(parent_content_id);

CREATE INDEX idx_package_contents_specification
    ON package_contents(package_specification_id);

-- ============================================================
-- 6. Supplier Offers
--
-- An offer connects one supplier, one product and one package
-- specification.
--
-- purchase_price = price for one complete package.
-- minimum_order_quantity = number of those packages required.
--
-- A supplier may offer the same product in different packages.
-- Different suppliers may offer the same product.
-- ============================================================

CREATE TABLE supplier_offers (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT UNSIGNED NOT NULL,
    product_id INT UNSIGNED NOT NULL,
    package_specification_id INT UNSIGNED NOT NULL,
    minimum_order_quantity DECIMAL(12, 4) NOT NULL DEFAULT 1.0000,
    purchase_price DECIMAL(12, 2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_supplier_offers_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_supplier_offers_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_supplier_offers_package_specification
        FOREIGN KEY (package_specification_id)
        REFERENCES package_specifications(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT uq_supplier_product_package
        UNIQUE (supplier_id, product_id, package_specification_id),

    CONSTRAINT chk_supplier_offers_moq
        CHECK (minimum_order_quantity > 0),

    CONSTRAINT chk_supplier_offers_price
        CHECK (purchase_price >= 0)
);

-- The unique constraint above starts with supplier_id, so it also
-- provides an index for supplier_id lookups and its foreign key.
-- Keep separate indexes for product and active-status lookups.
CREATE INDEX idx_supplier_offers_product
    ON supplier_offers(product_id);

CREATE INDEX idx_supplier_offers_active
    ON supplier_offers(is_active);

-- ============================================================
-- 7. Migration and Compatibility Notes
--
-- This file is a design draft, not a migration script.
--
-- Preserve existing categories, suppliers, products, purchases,
-- purchase_items, sales and sale_items during migration.
--
-- Do not drop products.supplier_id or products.cost_price until
-- the migration and application changes have been verified.
--
-- Preserve purchase_items.unit_cost and subtotal as historical
-- purchase snapshots.
--
-- inventory_unit_id must reference a valid units.id.
--
-- Package contents and unit conversions need application-level
-- validation. Prevent cycles and reject undefined conversions.
--
-- Purchase workflow integration with supplier_offers belongs
-- to v0.4.5. Do not implement that refactor in this draft.
-- ============================================================
