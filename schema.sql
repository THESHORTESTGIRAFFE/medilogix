-- SAMS PMD Database Schema - Initial Setup
-- Ensure you have created a database and a user with appropriate privileges.
-- Example:
-- CREATE DATABASE sams_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- CREATE USER 'sams_user'@'localhost' IDENTIFIED BY 'sams_password';
-- GRANT ALL PRIVILEGES ON sams_db.* TO 'sams_user'@'localhost';
-- FLUSH PRIVILEGES;

-- USE sams_db; -- Select your database before running this script

-- Departments Table
CREATE TABLE IF NOT EXISTS `departments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) UNIQUE NOT NULL,
    `description` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users Table
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) UNIQUE NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL, -- Store hashed passwords
    `full_name` VARCHAR(100),
    `role` ENUM('admin', 'manager', 'staff') NOT NULL DEFAULT 'staff',
    `department_id` INT,
    `email` VARCHAR(100) UNIQUE,
    `is_active` BOOLEAN DEFAULT TRUE,
    `last_login_at` TIMESTAMP NULL DEFAULT NULL, -- Added for last login tracking
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT, -- Can be NULL if action is system-generated before login
    `action` VARCHAR(255) NOT NULL,
    `details` TEXT,
    `ip_address` VARCHAR(45),
    `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Item Categories Table
CREATE TABLE IF NOT EXISTS `item_categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) UNIQUE NOT NULL,
    `description` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Item Locations Table (Storerooms, Shelves, etc.)
CREATE TABLE IF NOT EXISTS `item_locations` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) UNIQUE NOT NULL,
    `description` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Items Table
CREATE TABLE IF NOT EXISTS `items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `sku` VARCHAR(100) UNIQUE, -- Stock Keeping Unit
    `description` TEXT,
    `category_id` INT,
    `unit_of_measure` VARCHAR(50), -- e.g., 'pieces', 'box', 'kg', 'liters'
    `reorder_threshold` DECIMAL(10,2) DEFAULT 0.00,
    `preferred_supplier_id` INT, -- Optional, can link to a suppliers table later
    `image_path` VARCHAR(255), -- Path to an uploaded image
    `notes` TEXT,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`category_id`) REFERENCES `item_categories`(`id`) ON DELETE SET NULL
    -- FOREIGN KEY (`preferred_supplier_id`) REFERENCES `suppliers`(`id`) ON DELETE SET NULL -- If you add a suppliers table
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX idx_item_name ON items(name);

-- Stock Movements Table (Ledger for all inventory transactions)
CREATE TABLE IF NOT EXISTS `stock_movements` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `item_id` INT NOT NULL,
    `location_id` INT, -- Location where the stock is moved to/from.
    `quantity_changed` DECIMAL(10,2) NOT NULL, -- Positive for stock in, negative for stock out
    `movement_type` ENUM(
        'initial_stock', 'receipt', 'issuance', 
        'adjustment_in', 'adjustment_out', 
        'transfer_out', 'transfer_in', 'disposal'
    ) NOT NULL,
    `movement_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `user_id` INT, -- User who performed/authorized the transaction
    `batch_number` VARCHAR(100),
    `expiry_date` DATE,
    `cost_per_unit` DECIMAL(10,2), -- Optional: for valuation
    `related_purchase_order_id` VARCHAR(50), -- Link to PO
    `related_requisition_id` INT, -- Link to internal requisition
    `notes` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`item_id`) REFERENCES `items`(`id`) ON DELETE CASCADE, 
    FOREIGN KEY (`location_id`) REFERENCES `item_locations`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
    -- FOREIGN KEY (`related_requisition_id`) REFERENCES `requisitions`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX idx_stock_item_date ON stock_movements(item_id, movement_date);
CREATE INDEX idx_stock_location ON stock_movements(item_id, location_id);

-- Requisitions Table
CREATE TABLE IF NOT EXISTS `requisitions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `requester_id` INT NOT NULL,
    `department_id` INT, -- Department of the requester, can be auto-filled
    `status` ENUM(
        'Pending', 'Approved', 'Rejected', 
        'Partially Fulfilled', 'Fulfilled', 'Cancelled'
    ) NOT NULL DEFAULT 'Pending',
    `request_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `required_by_date` DATE,
    `approved_by_id` INT,
    `approval_date` TIMESTAMP NULL DEFAULT NULL,
    `rejection_reason` TEXT,
    `notes` TEXT, -- General notes for the requisition
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`requester_id`) REFERENCES `users`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`approved_by_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX idx_requisition_requester ON requisitions(requester_id);
CREATE INDEX idx_requisition_status ON requisitions(status);

-- Requisition Items Table
CREATE TABLE IF NOT EXISTS `requisition_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `requisition_id` INT NOT NULL,
    `item_id` INT NOT NULL,
    `quantity_requested` DECIMAL(10,2) NOT NULL,
    `quantity_approved` DECIMAL(10,2) DEFAULT 0.00,
    `quantity_issued` DECIMAL(10,2) DEFAULT 0.00,
    `notes` TEXT, -- Notes specific to this item in the requisition
    FOREIGN KEY (`requisition_id`) REFERENCES `requisitions`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`item_id`) REFERENCES `items`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Stock Transfers Table
CREATE TABLE IF NOT EXISTS `stock_transfers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `origin_location_id` INT NOT NULL,
    `destination_location_id` INT NOT NULL,
    `initiated_by_user_id` INT NOT NULL,
    `status` ENUM('Pending', 'In Transit', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Pending',
    `transfer_date` DATE NOT NULL,
    `notes` TEXT,
    `driver_details` VARCHAR(255),
    `waybill_number` VARCHAR(100),
    `completed_by_user_id` INT,
    `completion_date` TIMESTAMP NULL DEFAULT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`origin_location_id`) REFERENCES `item_locations`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`destination_location_id`) REFERENCES `item_locations`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`initiated_by_user_id`) REFERENCES `users`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`completed_by_user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Stock Transfer Items Table
CREATE TABLE IF NOT EXISTS `stock_transfer_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `transfer_id` INT NOT NULL,
    `item_id` INT NOT NULL,
    `batch_number` VARCHAR(100),
    `expiry_date` DATE,
    `quantity_sent` DECIMAL(10,2) NOT NULL,
    `quantity_received` DECIMAL(10,2),
    `notes` TEXT,
    FOREIGN KEY (`transfer_id`) REFERENCES `stock_transfers`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`item_id`) REFERENCES `items`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dummy table for future supplier integration
CREATE TABLE IF NOT EXISTS `suppliers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `contact_person` VARCHAR(100),
    `phone` VARCHAR(50),
    `email` VARCHAR(100),
    `address` TEXT,
    `payment_terms` VARCHAR(100), -- e.g., 'Net 30', 'COD'
    `rating` DECIMAL(3,2) DEFAULT 0.00, -- Supplier rating (e.g., 1.00 to 5.00)
    `is_blacklisted` BOOLEAN DEFAULT FALSE, -- True if supplier is blacklisted
    `notes` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dummy table for future purchase orders
CREATE TABLE IF NOT EXISTS `purchase_orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `supplier_id` INT NOT NULL,
    `order_date` DATE NOT NULL,
    `expected_delivery_date` DATE,
    `status` VARCHAR(50) DEFAULT 'Draft', -- e.g., Draft, Submitted, Approved, Fulfilled
    `total_amount` DECIMAL(12,2),
    `notes` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`supplier_id`) REFERENCES `suppliers`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dummy table for future purchase order items
CREATE TABLE IF NOT EXISTS `purchase_order_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `purchase_order_id` INT NOT NULL,
    `item_id` INT NOT NULL,
    `quantity` DECIMAL(10,2) NOT NULL,
    `unit_price` DECIMAL(10,2),
    `total_price` DECIMAL(12,2),
    FOREIGN KEY (`purchase_order_id`) REFERENCES `purchase_orders`(`id`),
    FOREIGN KEY (`item_id`) REFERENCES `items`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Goods Received Notes (GRN) Table
CREATE TABLE IF NOT EXISTS `goods_received_notes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `purchase_order_id` INT NOT NULL,
    `received_date` DATE NOT NULL,
    `received_by_user_id` INT NOT NULL,
    `delivery_note_number` VARCHAR(100), -- Supplier's delivery note number
    `notes` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`purchase_order_id`) REFERENCES `purchase_orders`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`received_by_user_id`) REFERENCES `users`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Goods Received Note Items Table
CREATE TABLE IF NOT EXISTS `goods_received_note_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `grn_id` INT NOT NULL,
    `item_id` INT NOT NULL,
    `quantity_received` DECIMAL(10,2) NOT NULL,
    `batch_number` VARCHAR(100), -- Batch number of received item
    `expiry_date` DATE, -- Expiry date of received item
    `unit_price` DECIMAL(10,2), -- Unit price at time of receipt (from PO or actual)
    `notes` TEXT,
    FOREIGN KEY (`grn_id`) REFERENCES `goods_received_notes`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`item_id`) REFERENCES `items`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Invoices Table
CREATE TABLE IF NOT EXISTS `invoices` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `invoice_number` VARCHAR(100) UNIQUE NOT NULL,
    `supplier_id` INT NOT NULL,
    `invoice_date` DATE NOT NULL,
    `amount` DECIMAL(12,2) NOT NULL,
    `currency` VARCHAR(10) DEFAULT 'USD',
    `due_date` DATE,
    `status` ENUM('Pending', 'Paid', 'Overdue') NOT NULL DEFAULT 'Pending',
    `file_path` VARCHAR(255), -- Path to the uploaded invoice file
    `related_po_id` INT, -- Link to Purchase Order
    `related_grn_id` INT, -- Link to Goods Received Note
    `notes` TEXT,
    `uploaded_by_user_id` INT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`supplier_id`) REFERENCES `suppliers`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`related_po_id`) REFERENCES `purchase_orders`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`related_grn_id`) REFERENCES `goods_received_notes`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`uploaded_by_user_id`) REFERENCES `users`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
