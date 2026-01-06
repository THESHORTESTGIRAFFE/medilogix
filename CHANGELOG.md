# Changelog

## [Unreleased] - 2025-10-22

### Added

- **Blockchain-Based Audit Trails Feature:**
    - Added `hash` and `previous_hash` columns to `stock_movements`, `purchase_orders`, and `goods_received_notes` tables in `schema.sql`.
    - Created a new `audit_chain_metadata` table to store the last hash for each record type.
    - Implemented a `calculate_hash` function in `app/utils.py` to compute SHA256 hashes for records.
    - Modified the `add_stock_movement`, `create_purchase_order`, and `create_grn` functions in their respective route files to calculate and store hashes for new records, creating a blockchain-like chain.
    - Created a new CLI command `flask audit verify-chain` in `app/cli.py` to verify the integrity of the audit chains.
    - Updated the `PurchaseOrder` and `GoodsReceivedNote` models in `app/models.py` to include `hash` and `previous_hash` attributes.
    - Added a new `StockMovement` model to `app/models.py`.

### Fixed

- Resolved a `NameError` in `app/__init__.py` by adding the import for `invoices_bp`.
- Corrected `NameError`s in `app/routes/invoices.py` by using the correct blueprint variable `bp` instead of `invoices_bp` in route decorators.
