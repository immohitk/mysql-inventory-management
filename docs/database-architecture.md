# Database Architecture

## 1. Overview

The MySQL Inventory Management database uses a normalized relational design.

The database separates products, categories, suppliers, purchases, purchase items, sales, and sale items into dedicated tables.

The design uses primary keys and foreign keys to maintain relationships and referential integrity.

Inventory quantity is maintained at the product level and is changed through purchase and sales transactions.

---

## 2. Core Entities

The database contains seven core entities:

1. Categories
2. Products
3. Suppliers
4. Purchases
5. Purchase Items
6. Sales
7. Sale Items

---

## 3. Entity Structure

### 3.1 Categories

Stores product categories.

| Column      | Purpose                       |
| ----------- | ----------------------------- |
| id          | Unique category identifier    |
| name        | Category name                 |
| description | Optional category description |

Constraints:

- `id` is the primary key.
- `name` must be unique.
- `name` is required.

---

### 3.2 Products

Stores products managed by the inventory system.

| Column        | Purpose                                                  |
| ------------- | -------------------------------------------------------- |
| id            | Unique product identifier                                |
| category_id   | References the product category                          |
| supplier_id   | References the primary supplier                          |
| sku           | Unique product stock-keeping unit                        |
| name          | Product name                                             |
| description   | Optional product description                             |
| cost_price    | Cost of acquiring the product                            |
| selling_price | Price at which the product is sold                       |
| quantity      | Current available stock                                  |
| reorder_level | Stock level at which the product is considered low stock |
| created_at    | Record creation timestamp                                |
| updated_at    | Last update timestamp                                    |

Constraints:

- `id` is the primary key.
- `category_id` is a foreign key referencing `categories`.
- `supplier_id` is a foreign key referencing `suppliers`.
- `sku` must be unique.
- Required product fields must not be null.
- Prices must not be negative.
- Quantity must not be negative.
- Reorder level must not be negative.

---

### 3.3 Suppliers

Stores supplier information.

| Column  | Purpose                    |
| ------- | -------------------------- |
| id      | Unique supplier identifier |
| name    | Supplier name              |
| phone   | Supplier phone number      |
| email   | Supplier email address     |
| address | Supplier address           |

Constraints:

- `id` is the primary key.
- `name` is required.

---

### 3.4 Purchases

Stores purchase transactions.

| Column        | Purpose                               |
| ------------- | ------------------------------------- |
| id            | Unique purchase identifier            |
| supplier_id   | Supplier associated with the purchase |
| purchase_date | Date and time of purchase             |
| total_amount  | Total purchase value                  |
| status        | Purchase status                       |

Constraints:

- `id` is the primary key.
- `supplier_id` is a foreign key referencing `suppliers`.
- `supplier_id` is required.
- `purchase_date` is required.
- `total_amount` must not be negative.

---

### 3.5 Purchase Items

Stores individual products included in a purchase.

| Column      | Purpose                          |
| ----------- | -------------------------------- |
| id          | Unique purchase item identifier  |
| purchase_id | References the purchase          |
| product_id  | References the purchased product |
| quantity    | Quantity purchased               |
| unit_cost   | Cost per unit                    |
| subtotal    | Total cost for the item          |

Constraints:

- `id` is the primary key.
- `purchase_id` is a foreign key referencing `purchases`.
- `product_id` is a foreign key referencing `products`.
- `quantity` must be greater than zero.
- `unit_cost` must not be negative.
- `subtotal` must not be negative.

---

### 3.6 Sales

Stores sales transactions.

| Column       | Purpose                |
| ------------ | ---------------------- |
| id           | Unique sale identifier |
| sale_date    | Date and time of sale  |
| total_amount | Total sale value       |
| status       | Sale status            |

Constraints:

- `id` is the primary key.
- `sale_date` is required.
- `total_amount` must not be negative.

---

### 3.7 Sale Items

Stores individual products included in a sale.

| Column     | Purpose                     |
| ---------- | --------------------------- |
| id         | Unique sale item identifier |
| sale_id    | References the sale         |
| product_id | References the sold product |
| quantity   | Quantity sold               |
| unit_price | Selling price per unit      |
| subtotal   | Total value for the item    |

Constraints:

- `id` is the primary key.
- `sale_id` is a foreign key referencing `sales`.
- `product_id` is a foreign key referencing `products`.
- `quantity` must be greater than zero.
- `unit_price` must not be negative.
- `subtotal` must not be negative.

---

## 4. Relationships

### Categories → Products

One category can contain many products.

Relationship:

**One-to-Many**

```text
categories
    1
    |
    |
    N
products
```

A product belongs to one category.

---

### Suppliers → Products

One supplier can be associated with many products.

Relationship:

**One-to-Many**

```text
suppliers
    1
    |
    |
    N
products
```

The current v1 model associates each product with one primary supplier.

---

### Suppliers → Purchases

One supplier can have many purchase transactions.

Relationship:

**One-to-Many**

```text
suppliers
    1
    |
    |
    N
purchases
```

Each purchase belongs to one supplier.

---

### Purchases → Purchase Items

One purchase can contain multiple purchase items.

Relationship:

**One-to-Many**

```text
purchases
    1
    |
    |
    N
purchase_items
```

Each purchase item belongs to one purchase.

---

### Products → Purchase Items

One product can appear in many purchase items.

Relationship:

**One-to-Many**

```text
products
    1
    |
    |
    N
purchase_items
```

This allows the same product to be purchased multiple times.

---

### Sales → Sale Items

One sale can contain multiple sale items.

Relationship:

**One-to-Many**

```text
sales
    1
    |
    |
    N
sale_items
```

Each sale item belongs to one sale.

---

### Products → Sale Items

One product can appear in many sale items.

Relationship:

**One-to-Many**

```text
products
    1
    |
    |
    N
sale_items
```

This allows the same product to be sold across multiple transactions.

---

## 5. Complete Relationship Model

```text
                         ┌──────────────┐
                         │  categories  │
                         └──────┬───────┘
                                │
                                │ 1:N
                                │
                         ┌──────▼───────┐
                         │   products   │
                         └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                   1:N                     1:N
                    │                       │
             ┌──────▼────────┐       ┌──────▼───────┐
             │purchase_items │       │  sale_items  │
             └──────┬────────┘       └──────┬───────┘
                    │                       │
                   N:1                     N:1
                    │                       │
             ┌──────▼────────┐       ┌──────▼───────┐
             │   purchases   │       │    sales     │
             └──────┬────────┘       └──────────────┘
                    │
                   N:1
                    │
             ┌──────▼────────┐
             │   suppliers   │
             └───────────────┘
```

Additional relationship:

```text
suppliers
    1
    |
    N
purchases
```

And:

```text
suppliers
    1
    |
    N
products
```

---

## 6. Many-to-Many Relationships

Purchases and products form a many-to-many relationship:

- One purchase can contain many products.
- One product can appear in many purchases.

This relationship is resolved using:

`purchase_items`

```text
purchases
    |
    N
    |
purchase_items
    |
    N
    |
products
```

Sales and products also form a many-to-many relationship:

- One sale can contain many products.
- One product can appear in many sales.

This relationship is resolved using:

`sale_items`

```text
sales
    |
    N
    |
sale_items
    |
    N
    |
products
```

---

## 7. Primary Key Strategy

Each table will use a dedicated numeric primary key.

The primary keys are:

| Table          | Primary Key |
| -------------- | ----------- |
| categories     | id          |
| products       | id          |
| suppliers      | id          |
| purchases      | id          |
| purchase_items | id          |
| sales          | id          |
| sale_items     | id          |

These identifiers provide stable internal references between related tables.

Business identifiers such as SKU are stored separately from the primary key.

---

## 8. Foreign Key Strategy

Foreign keys will enforce relationships between tables.

| Table          | Foreign Key | References    |
| -------------- | ----------- | ------------- |
| products       | category_id | categories.id |
| products       | supplier_id | suppliers.id  |
| purchases      | supplier_id | suppliers.id  |
| purchase_items | purchase_id | purchases.id  |
| purchase_items | product_id  | products.id   |
| sale_items     | sale_id     | sales.id      |
| sale_items     | product_id  | products.id   |

Foreign keys provide referential integrity and prevent invalid relationships.

---

## 9. Normalization

The database follows a normalized relational structure.

### First Normal Form

Each column stores a single logical value.

For example, a purchase does not store multiple product IDs in one column.

Instead, products are stored as separate rows in `purchase_items`.

---

### Second Normal Form

Data that depends on individual transaction items is stored in the item tables.

For example:

- Purchase-level data belongs in `purchases`.
- Product-level data belongs in `products`.
- Purchase-item data belongs in `purchase_items`.

---

### Third Normal Form

Non-key attributes should depend on the key of their own table rather than being unnecessarily duplicated.

For example:

- Category information belongs in `categories`.
- Supplier information belongs in `suppliers`.
- Product information belongs in `products`.

This reduces unnecessary duplication and update anomalies.

---

## 10. Inventory Design

The current stock quantity is stored in:

`products.quantity`

Inventory changes through business transactions.

### Stock In

A completed purchase increases product quantity.

```text
products.quantity
+
purchase_items.quantity
```

### Stock Out

A completed sale decreases product quantity.

```text
products.quantity
-
sale_items.quantity
```

The application must prevent stock from becoming negative.

---

## 11. Transaction Design

Purchases and sales may involve multiple database operations.

### Purchase Transaction

A purchase workflow may perform:

1. Create purchase record.
2. Create purchase item records.
3. Increase product stock.
4. Commit transaction.

If any operation fails:

**ROLLBACK**

---

### Sale Transaction

A sale workflow may perform:

1. Verify available stock.
2. Create sale record.
3. Create sale item records.
4. Decrease product stock.
5. Commit transaction.

If any operation fails:

**ROLLBACK**

This ensures that partial inventory updates are not left in the database.

---

## 12. Index Strategy

Indexes will be added where they support common queries and relationships.

Likely indexed columns include:

- products.sku
- products.category_id
- products.supplier_id
- purchases.supplier_id
- purchases.purchase_date
- purchase_items.purchase_id
- purchase_items.product_id
- sales.sale_date
- sale_items.sale_id
- sale_items.product_id

Unique constraints may automatically create indexes where supported by MySQL.

Final indexes will be confirmed during schema implementation and SQL performance testing.

---

## 13. Data Integrity Rules

The database should enforce appropriate integrity rules.

Important rules include:

- Category names must be unique.
- Product SKUs must be unique.
- Required fields must not be NULL.
- Prices cannot be negative.
- Quantities cannot be negative.
- Purchase item quantities must be greater than zero.
- Sale item quantities must be greater than zero.
- Foreign keys must reference valid records.
- Inventory must not become negative.

Business rules that cannot be fully enforced by simple database constraints should be enforced by the application service layer and transactions.

---

## 14. Design Boundaries

The v1 database intentionally does not include:

- Customers
- User accounts
- Roles and permissions
- Warehouses
- Product variants
- Barcode data
- Returns
- Refunds
- Purchase orders
- Payment records
- GST invoice structures

These are outside the current application scope.

---

## 15. Final Entity Summary

```text
categories
    |
    └──< products >── suppliers
            |
            ├──< purchase_items >── purchases >── suppliers
            |
            └──< sale_items >────── sales
```

Core tables:

1. categories
2. products
3. suppliers
4. purchases
5. purchase_items
6. sales
7. sale_items

This architecture will be used as the basis for the MySQL schema implementation.
