# Blockchain-Based Audit Trails Implementation

This document outlines the implementation of a lightweight blockchain-based audit trail system within MediLogix to enhance data integrity and auditability for critical transactions.

## 1. Database Schema Changes

The following changes were made to the database schema in `medilogix_db.sql`:

-   **Added `hash` (VARCHAR(64)) and `previous_hash` (VARCHAR(64)) columns** to the `stock_movements`, `purchase_orders`, and `goods_received_notes` tables. These columns store the SHA256 hash of the current record and the hash of the previous record in the chain, respectively.

-   **Created a new table, `audit_chain_metadata`**:
    ```sql
    CREATE TABLE `audit_chain_metadata` (
      `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
      `record_type` varchar(50) NOT NULL UNIQUE,
      `last_hash` varchar(64) DEFAULT NULL,
      `last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    ```
    This table stores the `last_hash` for each record type (`stock_movement`, `purchase_order`, `grn`), serving as the head of each audit chain.

-   **Added `goods_received_notes` table definition**:
    The `goods_received_notes` table, which was missing from `medilogix_db.sql`, was added with `hash` and `previous_hash` columns and proper foreign key constraints.

-   **Updated Indexes and Auto-Increment settings**:
    Indexes and `AUTO_INCREMENT` settings were updated for the newly added `goods_received_notes` and `audit_chain_metadata` tables.

## 2. Hashing Logic Implementation

A SHA256 hashing function (`calculate_hash`) was already available in `app/utils.py`.

This hashing logic was integrated into the application's routes for creating and updating critical records to maintain the audit trail:

-   **`app/routes/stock.py` (`add_stock_movement` function)**:
    -   Retrieves the `previous_hash` for `stock_movement` from `audit_chain_metadata`.
    -   Calculates the `current_hash` of the new/updated `stock_movement` record.
    -   Stores both `current_hash` and `previous_hash` in the `stock_movements` record.
    -   Updates the `audit_chain_metadata` table with the `current_hash` as the new `last_hash` for `stock_movement`.

-   **`app/routes/purchase_orders.py` (`create_purchase_order` and `edit_purchase_order` functions)**:
    -   Similar logic as `stock_movements` for `purchase_order` records, ensuring that both creation and updates generate and store hashes, and update the `audit_chain_metadata`.

-   **`app/routes/grns.py` (`create_grn` function)**:
    -   Similar logic as `stock_movements` for `goods_received_note` records, ensuring that creation generates and stores hashes, and updates the `audit_chain_metadata`.

## 3. Verification Mechanism

A CLI command was implemented in `app/cli.py` to verify the integrity of the blockchain audit trails:

-   **`flask audit verify-chain` command**:
    -   Accessible via `flask audit verify-chain`.
    -   Traverses the audit chain for `stock_movement`, `purchase_order`, and `grn` record types.
    -   For each record, it re-calculates the hash based on the record's data.
    -   Compares the re-calculated hash with the stored `hash` value in the record.
    -   Verifies that each record's `previous_hash` matches the `hash` of the preceding record in the chain.
    -   Reports any discrepancies, indicating potential data tampering.

## 4. Model Updates

The `PurchaseOrder`, `GoodsReceivedNote`, and `StockMovement` classes in `app/models.py` were confirmed to already include `hash` and `previous_hash` attributes, aligning with the database schema changes. This step was already completed prior to this implementation cycle.