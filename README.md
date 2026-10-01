# MySQL Inventory Management

A small inventory management application built with Python and MySQL, designed to demonstrate practical relational database and SQL fundamentals through a real-world inventory workflow.

## Project Status

**Current version:** `v0.1.0`
**Status:** Foundation release

The current release establishes the project's requirements, database architecture, MySQL schema, relationships, constraints, indexes, and safe demo data.

The application GUI and inventory workflows will be implemented in subsequent versions.

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

The `v0.1.0` foundation includes:

- Project structure and Python environment
- Defined functional and technical requirements
- Documented database architecture
- MySQL relational schema
- Primary keys and foreign keys
- Unique constraints
- Check constraints
- Referential integrity rules
- Database indexes
- Safe fictional demo data
- Basic application entry point
- Environment-based database configuration template

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
- Tkinter / CustomTkinter — planned for the GUI

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

Some directories are intentionally empty during the foundation stage and will be populated in later versions.

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

The current foundation entry point confirms that the application environment is initialized.

The full inventory GUI will be introduced in later versions.

## Testing

Run:

    python -m pytest

At the foundation stage, automated application tests have not yet been implemented.

## Planned Development

The project will evolve through the following releases:

| Version   | Focus                                  |
| --------- | -------------------------------------- |
| `v0.1.0`  | Project foundation + database          |
| `v0.2.0`  | Core CRUD                              |
| `v0.3.0`  | Purchasing / stock-in                  |
| `v0.4.0`  | Sales / stock-out                      |
| `v0.5.0`  | SQL depth + search/filtering           |
| `v0.6.0`  | Complete GUI                           |
| `v0.7.0`  | Reports + dashboard                    |
| `v0.8.0`  | Validation + error handling + security |
| `v0.9.0`  | Testing + stabilization                |
| `v0.10.0` | Documentation + release preparation    |
| `v1.0.0`  | Complete stable system                 |

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
