
-- Migration v0.4.2: Package and supplier tables
-- Apply only to an isolated migration test database.
-- Do not run against inventory_db.

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

CREATE INDEX idx_package_contents_specification
    ON package_contents(package_specification_id);

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
