-- Migration v0.4.2: Base procurement tables
-- Apply only to an isolated migration test database.
-- Do not run against inventory_db.

CREATE TABLE units (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(30) NOT NULL UNIQUE,
    unit_type VARCHAR(30) NOT NULL,
    CONSTRAINT chk_units_type
        CHECK (unit_type IN ('COUNT', 'MASS', 'VOLUME'))
);

CREATE TABLE unit_conversions (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    from_unit_id INT UNSIGNED NOT NULL,
    to_unit_id INT UNSIGNED NOT NULL,
    conversion_factor DECIMAL(18, 8) NOT NULL,
    CONSTRAINT fk_unit_conversions_from
        FOREIGN KEY (from_unit_id) REFERENCES units(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_unit_conversions_to
        FOREIGN KEY (to_unit_id) REFERENCES units(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_unit_conversion
        UNIQUE (from_unit_id, to_unit_id),
    CONSTRAINT chk_unit_conversion_factor
        CHECK (conversion_factor > 0)
);

CREATE TABLE package_forms (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);
