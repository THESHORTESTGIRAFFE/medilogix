# MediLogix - Medical Inventory Management System

MediLogix is a web-based application for managing medical inventory, originally named MediLogix (Stock and Asset Management System). It is designed to help healthcare facilities track stock levels, manage procurement, and ensure the availability of essential medical supplies.

## Features

The application includes the following features:

### Advanced Inventory Management
*   **Barcode & QR Integration:** Generate and display barcodes for items.
*   **Batch & Expiry Tracking:** Track items by batch and expiry date, with FIFO logic for issuing stock.
*   **Stock Transfer Module:** Transfer stock between locations with an approval workflow.
*   **Low Stock & Reorder Alerts:** Daily checks for low stock items with logging.

### Supplier & Procurement Management
*   **Supplier Directory:** Manage a directory of suppliers with contact information and performance ratings.
*   **Purchase Order (PO) Module:** Create and manage purchase orders with a multi-level approval process. Export POs to PDF and CSV.
*   **Goods Received Notes (GRNs):** Record the receipt of goods against purchase orders, with support for partial receipts.
*   **Invoice Upload & Tracking:** Upload and track supplier invoices.

### Security & Audit
*   **Blockchain-Based Audit Trails:** All critical transactions are recorded in an immutable audit trail using a blockchain-like hashing mechanism.

## Getting Started

### Prerequisites
*   Python 3.10+
*   MySQL

### Quick Start with Production Runner (`run_production.py`)
MediLogix provides a foolproof production runner script (`run_production.py`) that automates environment checks, virtual environment setup, dependency installation, database schema application, test execution, and application startup.

You can run `python run_production.py` without arguments for an interactive menu, or use specific subcommands:
```bash
# Setup database schema
python run_production.py setup

# Run unit tests
python run_production.py test

# Check system status
python run_production.py status

# Run the application (with automatic browser launch)
python run_production.py run
```

### Manual Installation & Running
1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd medilogix
    ```
2.  Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Set up the database:
    *   Create a MySQL database and user.
    *   Update the database connection settings in `config.py`.
    *   Import the database schema:
        ```bash
        mysql -u <username> -p <database_name> < medilogix_db.sql
        ```

### Running the Application
To run the web application manually, execute:
```bash
python run.py
```
The application will be available at `http://localhost:5000`.

### Running the Tests
To run the test suite manually, use `pytest`:
```bash
pytest
```

## Project Status

The `to-do.md` file in the project is outdated. Most of the features listed there have been implemented, at least partially. This `README.md` file provides a more accurate overview of the current project status.