-- MySQL Inventory Management
-- Demo / Seed Data
-- Version: 0.1.5

USE inventory_db;


-- ============================================================
-- 1. Categories
-- ============================================================

INSERT INTO categories (name, description)
VALUES
    ('Electronics', 'Consumer electronic products'),
    ('Office Supplies', 'General office and stationery supplies'),
    ('Home Appliances', 'Small household appliances'),
    ('Computer Accessories', 'Accessories and peripherals for computers');


-- ============================================================
-- 2. Suppliers
-- ============================================================

INSERT INTO suppliers (name, phone, email, address)
VALUES
    (
        'TechSource Supplies',
        '+91-9000000001',
        'contact@techsource.example',
        'Bengaluru, Karnataka'
    ),
    (
        'OfficeMart Distributors',
        '+91-9000000002',
        'sales@officemart.example',
        'Pune, Maharashtra'
    ),
    (
        'HomeTech Wholesale',
        '+91-9000000003',
        'orders@hometech.example',
        'Delhi, India'
    );


-- ============================================================
-- 3. Products
-- ============================================================

INSERT INTO products (
    category_id,
    supplier_id,
    sku,
    name,
    description,
    cost_price,
    selling_price,
    quantity,
    reorder_level
)
VALUES
    (
        1,
        1,
        'ELEC-001',
        'Wireless Keyboard',
        'Compact wireless keyboard',
        850.00,
        1199.00,
        25,
        10
    ),
    (
        1,
        1,
        'ELEC-002',
        'Wireless Mouse',
        'Ergonomic wireless mouse',
        450.00,
        699.00,
        40,
        15
    ),
    (
        4,
        1,
        'COMP-001',
        'USB-C Hub',
        'Multi-port USB-C connectivity hub',
        900.00,
        1399.00,
        12,
        8
    ),
    (
        4,
        1,
        'COMP-002',
        'HDMI Cable',
        'High-speed HDMI cable',
        180.00,
        299.00,
        50,
        20
    ),
    (
        2,
        2,
        'OFF-001',
        'Notebook',
        'A5 ruled notebook',
        60.00,
        99.00,
        75,
        25
    ),
    (
        2,
        2,
        'OFF-002',
        'Ballpoint Pen Pack',
        'Pack of blue ballpoint pens',
        45.00,
        80.00,
        100,
        30
    ),
    (
        3,
        3,
        'HOME-001',
        'Electric Kettle',
        '1.5 litre electric kettle',
        1100.00,
        1599.00,
        8,
        5
    ),
    (
        3,
        3,
        'HOME-002',
        'Table Fan',
        'Compact table fan',
        1250.00,
        1799.00,
        6,
        5
    );


-- ============================================================
-- End of Demo Data
-- ============================================================