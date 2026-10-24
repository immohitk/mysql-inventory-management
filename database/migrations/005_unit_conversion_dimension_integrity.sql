-- Migration v0.4.4.1: Enforce unit conversion dimensions.
-- Apply only through the guarded migration runner.
-- Do not run against inventory_db.

-- Add the composite key required by dimension-aware foreign keys.
ALTER TABLE units
    ADD CONSTRAINT uq_units_id_type
    UNIQUE (id, unit_type);

-- Add nullable columns first so existing records can be backfilled.
ALTER TABLE unit_conversions
    ADD COLUMN from_unit_type VARCHAR(30) NULL,
    ADD COLUMN to_unit_type VARCHAR(30) NULL;

-- Derive the dimensions from the referenced units.
UPDATE unit_conversions AS uc
JOIN units AS uf ON uf.id = uc.from_unit_id
JOIN units AS ut ON ut.id = uc.to_unit_id
SET
    uc.from_unit_type = uf.unit_type,
    uc.to_unit_type = ut.unit_type;

-- Enforce populated dimensions and matching unit types.
ALTER TABLE unit_conversions
    MODIFY COLUMN from_unit_type VARCHAR(30) NOT NULL,
    MODIFY COLUMN to_unit_type VARCHAR(30) NOT NULL,
    DROP FOREIGN KEY fk_unit_conversions_from,
    DROP FOREIGN KEY fk_unit_conversions_to,
    ADD CONSTRAINT fk_unit_conversions_from
        FOREIGN KEY (from_unit_id, from_unit_type)
        REFERENCES units (id, unit_type)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT fk_unit_conversions_to
        FOREIGN KEY (to_unit_id, to_unit_type)
        REFERENCES units (id, unit_type)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT chk_unit_conversion_types_match
        CHECK (from_unit_type = to_unit_type);
