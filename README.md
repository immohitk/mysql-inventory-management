# MySQL Inventory Management

A small inventory management application built with Python and MySQL, designed to demonstrate practical relational database and SQL fundamentals through a real-world inventory workflow.

## Project Status

**Current version:** `v0.2.5`
**Status:** Core CRUD GUI implementation complete; QA in progress

The project foundation, database layer, core CRUD services, and basic GUI for categories, products, and suppliers are implemented.

Version `v0.2.6` is focused on CRUD quality assurance and documentation before the Core CRUD milestone is released as `v0.3.0`.

## Goals

This project is designed to demonstrate practical understanding of:

- Python
- MySQL
- SQL
- Relational database design
- CRUD operations
- Primary and foreign keys
- Table relationships
- Normalization
- Constraints
- Indexes
- Transactions
- Validation
- Testing
- GUI development

## Current Features

The current development state includes:

- Project structure and Python environment
- Environment-based database configuration
- MySQL connection lifecycle management
- Transaction commit and rollback support
- Category CRUD
- Product CRUD
- Supplier CRUD
- Category, product, and supplier validation
- Duplicate protection
- Foreign-key deletion protection
- Product category and supplier relationship validation
- Product search and filtering at the service level
- Tkinter-based GUI
- Category management GUI
- Product management GUI
- Supplier management GUI
- Add, edit, delete, and refresh operations through the GUI
- Safe fictional demo data
- Relational database schema with primary keys and foreign keys
- Unique and check constraints
- Database indexes

## Database

The project currently contains seven core tables:

- `categories`
- `suppliers`
- `products`
- `purchases`
- `purchase_items`
- `sales`
- `sale_items`

### Relationships

The database relationships are:

    categories
       │
       └──< products >── suppliers

    products
       │
       ├──< purchase_items >── purchases
       │
       └──< sale_items >────── sales

The database is designed around normalized relational structures and uses foreign keys to maintain relationships between entities.

## Technology Stack

### Application

- Python
- Tkinter / ttk

### Database

- MySQL
- SQL
- `mysql-connector-python`

### Testing

- pytest

### Configuration

- `python-dotenv`

## Project Structure

    mysql-inventory-management/
    ├── app/
    │   ├── db/
    │   ├── models/
    │   ├── services/
    │   ├── gui/
    │   └── utils/
    ├── database/
    │   ├── schema.sql
    │   └── seed.sql
    ├── tests/
    ├── screenshots/
    ├── docs/
    │   ├── requirements.md
    │   └── database-architecture.md
    ├── .env.example
    ├── .gitignore
    ├── main.py
    ├── requirements.txt
    └── README.md

## Documentation

Project requirements:

`docs/requirements.md`

Database architecture:

`docs/database-architecture.md`

## Database Setup

### 1. Create the database schema

    mysql -u root -p < database/schema.sql

### 2. Load demo data

    mysql -u root -p < database/seed.sql

The seed file contains fictional demonstration data only.

## Configuration

Copy `.env.example` to `.env`.

Configure the database connection values for your local MySQL installation.

Example:

    DB_HOST=localhost
    DB_PORT=3306
    DB_NAME=inventory_db
    DB_USER=root
    DB_PASSWORD=your_password

Do not commit `.env` or real credentials to the repository.

## Running the Project

Activate the virtual environment and run:

    python main.py

This launches the desktop GUI for the current core CRUD modules:

- Categories
- Products
- Suppliers

## Testing

Run:

    python -m pytest

Automated tests will be expanded during later stabilization work.

Manual CRUD QA is performed during the development process to verify validation, duplicate protection, relationship rules, and deletion restrictions.

## Planned Development

| Version   | Focus                                  |
| --------- | -------------------------------------- |
| `v0.1.0`  | Project foundation + database          |
| `v0.2.1`  | Database connection layer              |
| `v0.2.2`  | Category CRUD service                  |
| `v0.2.3`  | Product CRUD service                   |
| `v0.2.4`  | Supplier CRUD service                  |
| `v0.2.5`  | Basic CRUD GUI                         |
| `v0.2.6`  | CRUD QA + documentation                |
| `v0.3.0`  | Core CRUD milestone release            |
| `v0.4.0`  | Purchasing / stock-in                  |
| `v0.5.0`  | Sales / stock-out                      |
| `v0.6.0`  | SQL depth + search/filtering           |
| `v0.7.0`  | Complete GUI                           |
| `v0.8.0`  | Reports + dashboard                    |
| `v0.9.0`  | Validation + error handling + security |
| `v0.10.0` | Testing + stabilization                |
| `v1.0.0`  | Documentation + final stable release   |

## Scope Boundaries

The first version intentionally does not include:

- Authentication
- User roles
- Customer management
- Barcode scanning
- Multiple warehouses
- Cloud deployment
- REST API
- Mobile application
- Payment gateway
- GST-compliant invoicing
- Purchase orders
- Returns or refunds
- Advanced analytics
- Email notifications
- Supplier portal

## Demo Data

The repository includes fictional seed data for:

- 4 categories
- 3 suppliers
- 8 products

The data is intended for local development and demonstration.

## License

License information will be added before the final `v1.0.0` release.
