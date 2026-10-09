# MySQL Inventory Management

A desktop inventory management application built with Python, Tkinter, and MySQL. This project demonstrates practical relational database design, SQL fundamentals, CRUD operations, purchasing workflows, and inventory management through a real-world application.

## Project Status

**Current version:** `v0.4.1` — Schema Redesign
**Status:** Procurement schema design completed; data migration and related application changes are pending.

The project includes the original database schema, database connection layer, CRUD services, and basic GUI for categories, products, and suppliers. The purchasing and stock-in milestone was released in `v0.4.0`.

Version `v0.4.1` introduces a proposed procurement database redesign that separates product inventory units from supplier-specific purchase offers and package specifications.

**Important:** The procurement schema is a design draft, not a migration script. The existing `inventory_db` must not be modified using `database/schema_v2.sql`. Data migration is planned for `v0.4.2`.

## Goals

This project demonstrates practical understanding of:

- Python application development
- MySQL and SQL
- Relational database design and normalization
- Primary keys and foreign keys
- CRUD operations
- Database constraints and indexes
- Transactions and rollback
- Input validation and error handling
- Automated and manual testing
- Tkinter GUI development
- Inventory and purchasing workflows
- Explicit measurement-unit conversions
- Database migration planning

## Current Features

The project development includes:

- Project structure and Python virtual environment
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
- Tkinter-based desktop GUI
- Category management GUI
- Product management GUI
- Supplier management GUI
- Add, edit, delete, and refresh operations through the GUI
- Fictional demonstration data
- Relational schema with primary keys and foreign keys
- Unique and check constraints
- Database indexes
- Purchasing and stock-in functionality from the `v0.4.0` milestone
- Proposed procurement schema redesign in `v0.4.1`
- Procurement schema design documentation

The procurement redesign is currently a schema and documentation milestone. The proposed supplier-offer service, package and unit logic, data migration, and related purchase workflow integration are planned for subsequent versions.

## Database

### Existing database schema

The existing database contains seven core tables:

- `categories`
- `suppliers`
- `products`
- `purchases`
- `purchase_items`
- `sales`
- `sale_items`

These tables represent the existing application database structure. The original schema remains available in `database/schema.sql`.

### Existing relationships

```text
categories
    |
    └──< products >── suppliers

products
    |
    ├──< purchase_items >── purchases
    |
    └──< sale_items >────── sales
```

Foreign keys maintain relationships between the existing database entities.

### Proposed procurement schema

Version `v0.4.1` introduces a separate target schema draft in `database/schema_v2.sql`.

The proposed design introduces:

- `units` — measurement units such as kilogram, litre, and piece
- `unit_conversions` — explicit directed conversion factors
- `package_forms` — packaging forms such as carton, sack, box, and bottle
- `package_specifications` — purchasable package configurations
- `package_contents` — explicitly defined package contents and quantities
- `supplier_offers` — supplier-specific product and package prices

The target product design also proposes an inventory unit and fractional stock quantities. It is reference material only and is not an executable replacement for the existing `products` table.

The proposed model is intended to support multiple suppliers per product and different package configurations for the same product.

**Migration boundary:** The existing database must remain unchanged during `v0.4.1`. Migration planning and validation belong to `v0.4.2`. Historical purchase costs and subtotals must be preserved.

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

```text
mysql-inventory-management/
├── app/
│   ├── db/
│   ├── models/
│   ├── services/
│   ├── gui/
│   └── utils/
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   └── schema_v2.sql
├── tests/
├── screenshots/
├── docs/
│   ├── requirements.md
│   ├── database-architecture.md
│   └── procurement-schema-design.md
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

The directory structure reflects the main project organization. Individual files and modules may evolve as development continues.

## Documentation

- **Project requirements:** [`docs/requirements.md`](docs/requirements.md)
- **Existing database architecture:** [`docs/database-architecture.md`](docs/database-architecture.md)
- **Proposed procurement schema design:** [`docs/procurement-schema-design.md`](docs/procurement-schema-design.md)
- **Existing database schema:** [`database/schema.sql`](database/schema.sql)
- **Proposed target schema draft:** [`database/schema_v2.sql`](database/schema_v2.sql)

The existing database documentation describes the current schema. The procurement design document describes the proposed target model and its migration boundaries.

## Database Setup

The following commands initialize the existing database for local development. Use them only when setting up a fresh development database or when you intentionally want to initialize the schema.

### 1. Create the database schema

```bash
mysql -u root -p < database/schema.sql
```

### 2. Load demonstration data

```bash
mysql -u root -p < database/seed.sql
```

The seed file contains fictional demonstration data.

**Existing database warning:** Do not run the proposed `database/schema_v2.sql` against `inventory_db`. It is a target design draft, not a migration script.

## Configuration

Copy `.env.example` to `.env`.

Configure the connection values for your local MySQL installation.

Example:

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_NAME=inventory_db
DB_USER=root
DB_PASSWORD=your_password
```

Use the database name and credentials appropriate for your local environment.

Do not commit `.env`, passwords, or real credentials to the repository.

## Running the Project

Activate the project's virtual environment, install dependencies if necessary, and run:

```bash
python main.py
```

This launches the desktop GUI for the implemented application modules, including the core CRUD modules:

- Categories
- Products
- Suppliers

Available purchasing and stock-in functionality depends on the current implementation and configuration.

## Testing

Run the automated test suite with:

```bash
python -m pytest
```

Testing is expanded throughout development.

Manual QA checks cover areas such as:

- CRUD operations
- Input validation
- Duplicate protection
- Relationship rules
- Deletion restrictions
- Database transaction behaviour

The proposed procurement schema has also been tested for table creation in a separate temporary database. Successful table creation does not establish that all package, unit-conversion, migration, or application-level business rules have been implemented.

Those rules require further validation and automated tests as their corresponding services and migration are developed.

## Development Roadmap

The project follows this versioned roadmap:

| Version  | Focus                                                    |
| -------- | -------------------------------------------------------- |
| `v0.1.0` | Project foundation, schema, demo data, and documentation |
| `v0.2.1` | Database connection layer                                |
| `v0.2.2` | Category CRUD service                                    |
| `v0.2.3` | Product CRUD service                                     |
| `v0.2.4` | Supplier CRUD service                                    |
| `v0.2.5` | Basic CRUD GUI                                           |
| `v0.2.6` | CRUD QA and documentation                                |
| `v0.3.0` | Core CRUD milestone release                              |
| `v0.4.0` | Purchasing and stock-in                                  |
| `v0.4.1` | Schema redesign                                          |
| `v0.4.2` | Data migration                                           |
| `v0.4.3` | Supplier Offer service                                   |
| `v0.4.4` | Package and unit logic                                   |
| `v0.4.5` | Purchase refactor                                        |
| `v0.4.6` | Purchase GUI                                             |
| `v0.4.7` | Stock-in refactor                                        |
| `v0.5.0` | QA and documentation                                     |

The roadmap order and version numbers are maintained as defined for this project.

## Scope Boundaries

The initial application intentionally excludes several advanced features, including:

- Authentication and user roles
- Customer management
- Barcode scanning
- Multiple warehouses
- Cloud deployment
- REST API
- Mobile application
- Payment gateway
- GST-compliant invoicing
- Returns and refunds
- Advanced analytics
- Email notifications
- Supplier portal

Additional functionality may be considered after the core application and procurement workflow have been stabilized.

## Demo Data

The original demonstration data includes fictional records for:

- 4 categories
- 3 suppliers
- 8 products

This data is intended for local development and demonstration purposes.

## License

License information will be added before the final `v1.0.0` release.
