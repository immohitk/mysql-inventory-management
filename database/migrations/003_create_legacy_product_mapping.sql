
-- Migration v0.4.2: Preserve legacy product data for reviewed mapping.
-- Apply only to an isolated migration test database.
-- Do not run against inventory_db.
-- No units, package sizes, or supplier offers are inferred here.

CREATE TABLE legacy_product_mapping (
    product_id INT UNSIGNED PRIMARY KEY,
    legacy_category_id INT UNSIGNED NOT NULL,
    legacy_supplier_id INT UNSIGNED NOT NULL,
    legacy_sku VARCHAR(50) NOT NULL,
    legacy_name VARCHAR(150) NOT NULL,
    legacy_description VARCHAR(255) NULL,
    legacy_cost_price DECIMAL(10, 2) NOT NULL,
    legacy_selling_price DECIMAL(10, 2) NOT NULL,
    legacy_quantity INT UNSIGNED NOT NULL,
    legacy_reorder_level INT UNSIGNED NOT NULL,
    legacy_created_at TIMESTAMP NOT NULL,
    legacy_updated_at TIMESTAMP NOT NULL,

    inventory_unit_id INT UNSIGNED NULL,
    mapping_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    mapping_notes VARCHAR(500) NULL,

    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_legacy_mapping_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_legacy_mapping_unit
        FOREIGN KEY (inventory_unit_id)
        REFERENCES units(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT chk_legacy_mapping_status
        CHECK (mapping_status IN ('PENDING', 'APPROVED'))
);

INSERT INTO legacy_product_mapping (
    product_id,
    legacy_category_id,
    legacy_supplier_id,
    legacy_sku,
    legacy_name,
    legacy_description,
    legacy_cost_price,
    legacy_selling_price,
    legacy_quantity,
    legacy_reorder_level,
    legacy_created_at,
    legacy_updated_at,
    inventory_unit_id,
    mapping_status,
    mapping_notes
)
SELECT
    p.id,
    p.category_id,
    p.supplier_id,
    p.sku,
    p.name,
    p.description,
    p.cost_price,
    p.selling_price,
    p.quantity,
    p.reorder_level,
    p.created_at,
    p.updated_at,
    NULL,
    'PENDING',
    'Awaiting verified inventory unit, quantity basis, and supplier price basis.'
FROM products AS p
WHERE NOT EXISTS (
    SELECT 1
    FROM legacy_product_mapping AS m
    WHERE m.product_id = p.id
);
