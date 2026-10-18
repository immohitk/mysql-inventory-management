-- MySQL Inventory Management
-- Fresh-install foundational schema
-- Procurement redesign: v0.4.2
-- Execute only as part of the verified fresh-install workflow.

CREATE TABLE categories (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255)
);

CREATE TABLE suppliers (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(30),
    email VARCHAR(150),
    address VARCHAR(255)
);

CREATE TABLE units (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(30) NOT NULL UNIQUE,
    unit_type VARCHAR(30) NOT NULL,
    CONSTRAINT uq_units_id_type UNIQUE (id, unit_type),
    CONSTRAINT chk_units_type
        CHECK (unit_type IN ('COUNT', 'MASS', 'VOLUME'))
);

CREATE TABLE unit_conversions (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    from_unit_id INT UNSIGNED NOT NULL,
    from_unit_type VARCHAR(30) NOT NULL,
    to_unit_id INT UNSIGNED NOT NULL,
    to_unit_type VARCHAR(30) NOT NULL,
    conversion_factor DECIMAL(18, 8) NOT NULL,
    CONSTRAINT fk_unit_conversions_from
        FOREIGN KEY (from_unit_id, from_unit_type)
        REFERENCES units(id, unit_type)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_unit_conversions_to
        FOREIGN KEY (to_unit_id, to_unit_type)
        REFERENCES units(id, unit_type)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT uq_unit_conversion
        UNIQUE (from_unit_id, to_unit_id),
    CONSTRAINT chk_unit_conversion_factor
        CHECK (conversion_factor > 0),
    CONSTRAINT chk_unit_conversion_types_match
        CHECK (from_unit_type = to_unit_type)
);

CREATE TABLE package_forms (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE products (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    category_id INT UNSIGNED NOT NULL,
    inventory_unit_id INT UNSIGNED NOT NULL,
    sku VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    selling_price DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    quantity DECIMAL(14, 4) NOT NULL DEFAULT 0.0000,
    reorder_level DECIMAL(14, 4) NOT NULL DEFAULT 0.0000,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_products_category
        FOREIGN KEY (category_id) REFERENCES categories(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_products_inventory_unit
        FOREIGN KEY (inventory_unit_id) REFERENCES units(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_products_selling_price
        CHECK (selling_price >= 0),
    CONSTRAINT chk_products_quantity
        CHECK (quantity >= 0),
    CONSTRAINT chk_products_reorder_level
        CHECK (reorder_level >= 0)
);

CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_inventory_unit_id
    ON products(inventory_unit_id);

CREATE TABLE purchases (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT UNSIGNED NOT NULL,
    purchase_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(30) NOT NULL DEFAULT 'COMPLETED',
    CONSTRAINT fk_purchases_supplier
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_purchases_total CHECK (total_amount >= 0)
);

CREATE TABLE purchase_items (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    purchase_id INT UNSIGNED NOT NULL,
    product_id INT UNSIGNED NOT NULL,
    quantity DECIMAL(14, 4) NOT NULL,
    unit_cost DECIMAL(12, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    CONSTRAINT fk_purchase_items_purchase
        FOREIGN KEY (purchase_id) REFERENCES purchases(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_purchase_items_product
        FOREIGN KEY (product_id) REFERENCES products(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_purchase_items_quantity CHECK (quantity > 0),
    CONSTRAINT chk_purchase_items_unit_cost CHECK (unit_cost >= 0),
    CONSTRAINT chk_purchase_items_subtotal CHECK (subtotal >= 0)
);

CREATE INDEX idx_purchases_supplier_id ON purchases(supplier_id);
CREATE INDEX idx_purchases_purchase_date ON purchases(purchase_date);
CREATE INDEX idx_purchase_items_purchase_id
    ON purchase_items(purchase_id);
CREATE INDEX idx_purchase_items_product_id
    ON purchase_items(product_id);

-- ============================================================
-- Sales: Product-Specific Selling Units
-- ============================================================

CREATE TABLE product_selling_units (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    product_id INT UNSIGNED NOT NULL,
    name VARCHAR(100) NOT NULL,
    inventory_quantity DECIMAL(18, 8) NOT NULL,
    selling_price DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_product_selling_units_product
        FOREIGN KEY (product_id)
        REFERENCES products(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT uq_product_selling_unit_name
        UNIQUE (product_id, name),

    CONSTRAINT chk_product_selling_units_quantity
        CHECK (inventory_quantity > 0),

    CONSTRAINT chk_product_selling_units_price
        CHECK (selling_price >= 0),

    CONSTRAINT uq_product_selling_unit_product_id
        UNIQUE (product_id, id)
);

CREATE INDEX idx_product_selling_units_product
    ON product_selling_units(product_id);

CREATE TABLE sales (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sale_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(30) NOT NULL DEFAULT 'COMPLETED',
    CONSTRAINT chk_sales_total CHECK (total_amount >= 0)
);

CREATE TABLE sale_items (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sale_id INT UNSIGNED NOT NULL,
    product_id INT UNSIGNED NOT NULL,
    selling_unit_id INT UNSIGNED NOT NULL,
    selling_unit_name VARCHAR(100) NOT NULL,
    quantity DECIMAL(14, 4) NOT NULL,
    inventory_quantity_per_unit DECIMAL(18, 8) NOT NULL,
    inventory_quantity_deducted DECIMAL(14, 4) NOT NULL,
    unit_price DECIMAL(12, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,

    CONSTRAINT fk_sale_items_sale
        FOREIGN KEY (sale_id) REFERENCES sales(id)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_sale_items_product
        FOREIGN KEY (product_id) REFERENCES products(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT fk_sale_items_selling_unit
        FOREIGN KEY (product_id, selling_unit_id)
        REFERENCES product_selling_units(product_id, id)
        ON UPDATE CASCADE ON DELETE RESTRICT,

    CONSTRAINT chk_sale_items_quantity
        CHECK (quantity > 0),

    CONSTRAINT chk_sale_items_inventory_per_unit
        CHECK (inventory_quantity_per_unit > 0),

    CONSTRAINT chk_sale_items_inventory_deducted
        CHECK (inventory_quantity_deducted > 0),

    CONSTRAINT chk_sale_items_unit_price
        CHECK (unit_price >= 0),

    CONSTRAINT chk_sale_items_subtotal
        CHECK (subtotal >= 0)
);

CREATE INDEX idx_sales_sale_date ON sales(sale_date);
CREATE INDEX idx_sale_items_sale_id ON sale_items(sale_id);
CREATE INDEX idx_sale_items_product_id ON sale_items(product_id);

-- ============================================================
-- Procurement: Package Specifications
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
-- Procurement: Package Contents
-- ============================================================

CREATE TABLE package_contents (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    package_specification_id INT UNSIGNED NOT NULL,
    parent_content_id INT UNSIGNED NULL,
    quantity DECIMAL(14, 4) NOT NULL,
    unit_id INT UNSIGNED NOT NULL,
    package_form_id INT UNSIGNED NULL,

    CONSTRAINT uq_package_content_id_spec
        UNIQUE (id, package_specification_id),

    CONSTRAINT fk_package_contents_specification
        FOREIGN KEY (package_specification_id)
        REFERENCES package_specifications(id)
        ON UPDATE CASCADE ON DELETE CASCADE,

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
-- Procurement: Supplier Offers
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

CREATE INDEX idx_supplier_offers_product
    ON supplier_offers(product_id);

CREATE INDEX idx_supplier_offers_active
    ON supplier_offers(is_active);

-- ============================================================
-- Migration v0.4.2: Track supplier offer evidence and review decisions.

CREATE TABLE supplier_offer_reviews (
    supplier_offer_id INT UNSIGNED PRIMARY KEY,

    package_evidence VARCHAR(500) NULL,
    price_evidence VARCHAR(500) NULL,
    moq_evidence VARCHAR(500) NULL,

    review_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    reviewer VARCHAR(100) NULL,
    reviewed_at TIMESTAMP NULL,
    review_notes VARCHAR(1000) NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_offer_reviews_offer
        FOREIGN KEY (supplier_offer_id)
        REFERENCES supplier_offers(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_offer_review_status
        CHECK (
            review_status IN ('PENDING', 'APPROVED', 'REJECTED')
        )
);
