# MySQL Inventory Management — Requirements

## 1. Project Overview

MySQL Inventory Management is a small desktop inventory management application built with Python, SQL, and MySQL.

The application is designed to demonstrate practical understanding of:

- Python
- SQL
- MySQL
- Relational database design
- CRUD operations
- Primary and foreign keys
- Table relationships
- JOIN queries
- Constraints
- Normalization
- Indexes
- Transactions
- Input validation
- GUI development
- Automated testing

The project prioritizes a clear relational database design and direct SQL interaction rather than hiding database operations behind an ORM.

---

## 2. Project Goals

The application should allow a small business to manage basic inventory operations through a graphical interface.

The completed application should allow users to:

1. Manage product categories.
2. Manage products.
3. Manage suppliers.
4. Record purchases.
5. Increase stock when products are purchased.
6. Record sales.
7. Decrease stock when products are sold.
8. Search and filter inventory.
9. View inventory and sales reports.
10. Monitor low-stock products.

---

## 3. Core Functional Requirements

### 3.1 Category Management

Users should be able to:

- Create a category.
- View categories.
- Update a category.
- Delete a category when allowed.

Category names must be unique.

---

### 3.2 Product Management

Users should be able to:

- Create products.
- View products.
- Update product information.
- Delete products when allowed.
- Search products.
- Filter products by category.
- View current stock.

Each product should contain information such as:

- SKU
- Name
- Description
- Category
- Supplier
- Cost price
- Selling price
- Quantity
- Reorder level

SKU must be unique.

---

### 3.3 Supplier Management

Users should be able to:

- Create suppliers.
- View suppliers.
- Update suppliers.
- Delete suppliers when allowed.
- Search suppliers.

Supplier information should include:

- Name
- Phone
- Email
- Address

---

## 4. Inventory Requirements

Inventory quantity represents the current stock available for sale.

Normal product CRUD must not be used to arbitrarily modify stock.

Stock should change through inventory transactions.

### Purchase

When a purchase is successfully recorded:

```text
Current Stock + Purchased Quantity
```

Example:

```text
Current stock = 20
Purchased = 10

New stock = 30
```

### Sale

When a sale is successfully recorded:

```text
Current Stock - Sold Quantity
```

Example:

```text
Current stock = 30
Sold = 5

New stock = 25
```

Stock must never become negative.

---

## 5. Purchase Requirements

Users should be able to record purchases from suppliers.

A purchase should contain:

- Supplier
- Purchase date
- Products
- Quantities
- Unit cost
- Subtotal
- Total amount
- Status

Recording a successful purchase must increase the corresponding product stock.

Purchase operations that modify multiple database records must use a database transaction.

If the operation fails, the transaction should be rolled back.

---

## 6. Sales Requirements

Users should be able to record sales.

A sale should contain:

- Sale date
- Products
- Quantities
- Unit price
- Subtotal
- Total amount
- Status

Before completing a sale, the application must verify that sufficient stock is available.

Example:

```text
Available stock = 5
Requested quantity = 8

Sale must be rejected.
```

A rejected sale must not reduce stock.

Successful sales must decrease product stock.

Sales involving multiple database operations must use a database transaction.

If the operation fails, the transaction should be rolled back.

---

## 7. Search and Filtering

The application should support searching and filtering inventory.

Required examples include:

- Search products by name.
- Search products by SKU.
- Filter products by category.
- Search suppliers.
- Identify low-stock products.

SQL should be used for search and filtering rather than loading the entire database into Python and filtering everything manually.

---

## 8. Reports

The application should provide at least the following reports.

### 8.1 Low Stock Report

Display products where:

```text
quantity <= reorder_level
```

---

### 8.2 Inventory Summary

The inventory report should provide useful information such as:

- Product count
- Total units
- Inventory value
- Category-level summaries

SQL aggregation should be demonstrated using functions such as:

- COUNT()
- SUM()
- AVG()

---

### 8.3 Sales Report

The sales report should provide information such as:

- Sales date
- Number of transactions
- Units sold
- Revenue

SQL aggregation and grouping should be demonstrated.

---

## 9. Database Requirements

The database must use MySQL.

The database design should contain the following core tables:

```text
categories
products
suppliers
purchases
purchase_items
sales
sale_items
```

The database must demonstrate:

- Primary keys
- Foreign keys
- UNIQUE constraints
- NOT NULL constraints
- Appropriate data types
- Appropriate indexes
- Referential integrity
- Normalized relational design

The database should avoid unnecessary duplication of data.

---

## 10. Relationship Requirements

The main relationships should be:

```text
categories
    |
    └──< products

suppliers
    |
    └──< products

suppliers
    |
    └──< purchases

purchases
    |
    └──< purchase_items >── products

sales
    |
    └──< sale_items >────── products
```

The application should demonstrate relational queries using JOIN operations.

---

## 11. SQL Requirements

The project must demonstrate practical SQL usage.

### Retrieval

- SELECT
- WHERE
- ORDER BY
- LIKE

### Relationships

- INNER JOIN
- LEFT JOIN where appropriate

### Aggregation

- COUNT
- SUM
- AVG
- GROUP BY
- HAVING

### Data Modification

- INSERT
- UPDATE
- DELETE

### Database Performance

- Indexes
- EXPLAIN

### Transactions

- COMMIT
- ROLLBACK

SQL should be written explicitly where appropriate so the database logic is visible and understandable.

---

## 12. GUI Requirements

The application must provide a graphical user interface.

The GUI should eventually contain:

- Dashboard
- Products
- Categories
- Suppliers
- Purchases
- Sales
- Reports

The GUI should allow users to perform the main inventory workflows without using the terminal.

The interface should provide understandable success and error feedback.

---

## 13. Validation Requirements

The application should validate user input before performing database operations.

Examples include:

- Required fields cannot be empty.
- Prices must be valid numeric values.
- Quantities must be valid positive values.
- SKU must be unique.
- Selling price and cost price must be valid.
- Sale quantity cannot exceed available stock.

Validation should exist at the appropriate application and database levels.

---

## 14. Error Handling Requirements

The application should handle expected errors without crashing.

Examples include:

- Database connection failures.
- Duplicate SKU.
- Duplicate category name.
- Invalid input.
- Missing required records.
- Insufficient stock.
- Foreign key violations.
- Transaction failures.

Users should receive clear and understandable error messages.

---

## 15. Configuration and Security Requirements

Database credentials must not be committed to Git.

The application should use environment variables for sensitive configuration.

The repository should contain:

```text
.env.example
```

but should not contain:

```text
.env
```

Passwords and other secrets must never be hard-coded into source files.

SQL queries should use parameterized queries rather than string concatenation with user input.

---

## 16. Testing Requirements

The project should contain automated tests using pytest.

Important workflows to test include:

- Product CRUD.
- Category CRUD.
- Supplier CRUD.
- Purchase creation.
- Stock increase after purchase.
- Sale creation.
- Stock decrease after sale.
- Sale rejection when stock is insufficient.
- Transaction rollback.
- Search/filter behavior.
- Report queries where practical.

Tests should cover important business logic rather than only checking whether functions execute.

---

## 17. Documentation Requirements

The repository should contain documentation covering:

- Project purpose
- Features
- Technology stack
- Installation
- MySQL setup
- Environment configuration
- Database schema
- ER diagram
- Application usage
- Testing
- Project structure
- Screenshots
- Known limitations

Documentation should describe the actual implementation and should not claim features that do not exist.

---

## 18. Explicitly Out of Scope for v1

The following features are intentionally excluded from the first stable release:

- User authentication
- User roles and permissions
- Customer management
- Barcode scanner
- Multi-warehouse inventory
- Cloud deployment
- REST API
- Mobile application
- Payment gateway
- GST-compliant invoicing
- Purchase orders
- Returns and refunds
- Advanced analytics
- Email notifications
- Supplier portal

These features may be considered in a future version after the core application is complete.

---

## 19. Technology Requirements

The initial technology stack is:

- Python
- MySQL
- SQL
- mysql-connector-python
- python-dotenv
- Tkinter / CustomTkinter
- pytest
- Git
- GitHub

Only technologies actually implemented and understood should be listed as part of the final project stack.

---

## 20. Acceptance Criteria

The application will be considered complete when a fresh user can:

1. Configure MySQL.
2. Configure environment variables.
3. Install project dependencies.
4. Initialize the database.
5. Start the application.
6. Use the GUI.
7. Create and manage categories.
8. Create and manage products.
9. Create and manage suppliers.
10. Record purchases.
11. See stock increase after purchases.
12. Record sales.
13. See stock decrease after sales.
14. Prevent sales that exceed available stock.
15. Search and filter inventory.
16. View reports.
17. Run the automated test suite successfully.

The final application should include:

- Clean source code
- Database schema
- Demo data where appropriate
- Automated tests
- Documentation
- Screenshots
- Safe configuration examples
- No committed secrets
