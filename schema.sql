-- Purchase Order Approval History Table
CREATE TABLE po_approval_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    po_id INT NOT NULL,
    user_id INT NOT NULL,
    status_before VARCHAR(50) NOT NULL,
    status_after VARCHAR(50) NOT NULL,
    notes TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Purchase Order Approval History Table
CREATE TABLE IF NOT EXISTS goods_received_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_order_id INT NOT NULL,
    received_date DATETIME NOT NULL,
    received_by_user_id INT NOT NULL,
    delivery_note_number VARCHAR(50),
    notes TEXT,
    file_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    hash VARCHAR(64),
    previous_hash VARCHAR(64),
    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
    FOREIGN KEY (received_by_user_id) REFERENCES users(id)
);