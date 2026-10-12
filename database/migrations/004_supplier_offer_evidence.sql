
-- Migration v0.4.2: Track supplier offer evidence and review decisions.
-- Apply only to an isolated inventory_migration_* test database.
-- Never apply to inventory_db.

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
