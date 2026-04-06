-- Municipal Tax Collection System
-- Execute this script in MySQL through XAMPP phpMyAdmin or MySQL console.

DROP DATABASE IF EXISTS municipal_tax_collection;
CREATE DATABASE municipal_tax_collection;
USE municipal_tax_collection;

-- Admin table stores municipal staff login accounts.
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Taxpayer table stores citizen account details.
CREATE TABLE taxpayers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    address VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Property table stores all registered municipal properties.
CREATE TABLE properties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    taxpayer_id INT NOT NULL,
    property_code VARCHAR(30) NOT NULL UNIQUE,
    property_type ENUM('Residential', 'Commercial', 'Industrial') NOT NULL DEFAULT 'Residential',
    address VARCHAR(255) NOT NULL,
    area_sqft DECIMAL(10,2) NOT NULL,
    property_value DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_property_taxpayer
        FOREIGN KEY (taxpayer_id) REFERENCES taxpayers(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT chk_property_area CHECK (area_sqft > 0),
    CONSTRAINT chk_property_value CHECK (property_value > 0)
);

-- Tax table stores yearly property tax assessment.
CREATE TABLE taxes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    tax_year YEAR NOT NULL,
    base_tax DECIMAL(12,2) NOT NULL,
    penalty_amount DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    total_due DECIMAL(12,2) NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('UNPAID', 'PARTIAL', 'PAID') NOT NULL DEFAULT 'UNPAID',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tax_property_year UNIQUE (property_id, tax_year),
    CONSTRAINT fk_tax_property
        FOREIGN KEY (property_id) REFERENCES properties(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Payment table stores payment transaction history.
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tax_id INT NOT NULL,
    taxpayer_id INT NOT NULL,
    amount_paid DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_reference VARCHAR(50) NOT NULL UNIQUE,
    payment_status ENUM('SUCCESS', 'FAILED', 'PENDING') NOT NULL DEFAULT 'SUCCESS',
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payment_tax
        FOREIGN KEY (tax_id) REFERENCES taxes(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_payment_taxpayer
        FOREIGN KEY (taxpayer_id) REFERENCES taxpayers(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT chk_payment_amount CHECK (amount_paid > 0)
);

-- Helpful indexes for fast search and report generation.
CREATE INDEX idx_taxpayer_email ON taxpayers(email);
CREATE INDEX idx_property_taxpayer ON properties(taxpayer_id);
CREATE INDEX idx_tax_property_status ON taxes(property_id, status);
CREATE INDEX idx_payment_taxpayer_paid_at ON payments(taxpayer_id, paid_at);
CREATE INDEX idx_payment_tax_id ON payments(tax_id);

DELIMITER $$

-- Stored procedure calculates tax automatically using property details.
CREATE PROCEDURE sp_generate_property_tax(IN in_property_id INT, IN in_tax_year YEAR)
BEGIN
    DECLARE v_property_value DECIMAL(12,2);
    DECLARE v_area_sqft DECIMAL(10,2);
    DECLARE v_property_type VARCHAR(20);
    DECLARE v_multiplier DECIMAL(5,2);
    DECLARE v_base_tax DECIMAL(12,2);

    SELECT property_value, area_sqft, property_type
    INTO v_property_value, v_area_sqft, v_property_type
    FROM properties
    WHERE id = in_property_id;

    SET v_multiplier = CASE
        WHEN v_property_type = 'Commercial' THEN 1.20
        WHEN v_property_type = 'Industrial' THEN 1.35
        ELSE 1.00
    END;

    SET v_base_tax = ((v_property_value * 0.01) + (v_area_sqft * 2)) * v_multiplier;

    INSERT INTO taxes (property_id, tax_year, base_tax, penalty_amount, total_due, due_date, status)
    VALUES (in_property_id, in_tax_year, ROUND(v_base_tax, 2), 0.00, ROUND(v_base_tax, 2), STR_TO_DATE(CONCAT(in_tax_year, '-09-30'), '%Y-%m-%d'), 'UNPAID')
    ON DUPLICATE KEY UPDATE
        base_tax = VALUES(base_tax),
        penalty_amount = 0.00,
        total_due = VALUES(total_due),
        due_date = VALUES(due_date),
        status = IF(status = 'PAID', status, 'UNPAID');
END$$

-- Trigger adds late payment penalty automatically before payment insert.
CREATE TRIGGER trg_before_payment_insert_penalty
BEFORE INSERT ON payments
FOR EACH ROW
BEGIN
    DECLARE v_due_date DATE;
    DECLARE v_status VARCHAR(10);
    DECLARE v_base_tax DECIMAL(12,2);
    DECLARE v_penalty DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_days_late INT DEFAULT 0;
    DECLARE v_months_late INT DEFAULT 0;

    SELECT due_date, status, base_tax
    INTO v_due_date, v_status, v_base_tax
    FROM taxes
    WHERE id = NEW.tax_id;

    IF v_status <> 'PAID' AND CURDATE() > v_due_date THEN
        SET v_days_late = DATEDIFF(CURDATE(), v_due_date);
        SET v_months_late = CEIL(v_days_late / 30);
        SET v_penalty = ROUND(v_base_tax * 0.02 * v_months_late, 2);

        UPDATE taxes
        SET penalty_amount = v_penalty,
            total_due = ROUND(base_tax + v_penalty, 2)
        WHERE id = NEW.tax_id;
    END IF;
END$$

-- Trigger updates payment status after each successful payment.
CREATE TRIGGER trg_after_payment_insert_update_tax
AFTER INSERT ON payments
FOR EACH ROW
BEGIN
    DECLARE v_total_paid DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_total_due DECIMAL(12,2) DEFAULT 0.00;

    SELECT COALESCE(SUM(amount_paid), 0.00)
    INTO v_total_paid
    FROM payments
    WHERE tax_id = NEW.tax_id AND payment_status = 'SUCCESS';

    SELECT total_due
    INTO v_total_due
    FROM taxes
    WHERE id = NEW.tax_id;

    UPDATE taxes
    SET status = CASE
        WHEN v_total_paid >= v_total_due THEN 'PAID'
        WHEN v_total_paid > 0 THEN 'PARTIAL'
        ELSE 'UNPAID'
    END
    WHERE id = NEW.tax_id;
END$$

DELIMITER ;

-- View gives a ready-made report for admin dashboard and exports.
CREATE VIEW vw_tax_collection_report AS
SELECT
    tp.full_name AS taxpayer_name,
    p.property_code,
    p.address,
    t.tax_year,
    t.base_tax,
    t.penalty_amount,
    t.total_due,
    COALESCE(SUM(CASE WHEN pay.payment_status = 'SUCCESS' THEN pay.amount_paid ELSE 0 END), 0.00) AS total_paid,
    ROUND(t.total_due - COALESCE(SUM(CASE WHEN pay.payment_status = 'SUCCESS' THEN pay.amount_paid ELSE 0 END), 0.00), 2) AS balance_due,
    t.status AS tax_status
FROM taxes t
INNER JOIN properties p ON p.id = t.property_id
INNER JOIN taxpayers tp ON tp.id = p.taxpayer_id
LEFT JOIN payments pay ON pay.tax_id = t.id
GROUP BY tp.full_name, p.property_code, p.address, t.tax_year, t.base_tax, t.penalty_amount, t.total_due, t.status;

-- Sample admin account.
INSERT INTO admins (username, full_name, password_hash)
VALUES ('admin', 'Municipal Administrator', SHA2('admin123', 256));

-- Sample taxpayers.
INSERT INTO taxpayers (full_name, email, phone, address, password_hash) VALUES
('Rahul Sharma', 'rahul@example.com', '9876543210', 'Ward 12, Green Colony', SHA2('user123', 256)),
('Anita Verma', 'anita@example.com', '9876501234', 'Ward 8, River View', SHA2('user123', 256));

-- Sample properties.
INSERT INTO properties (taxpayer_id, property_code, property_type, address, area_sqft, property_value) VALUES
(1, 'PROP-1001', 'Residential', '12 Green Colony, Block A', 1250.00, 2500000.00),
(1, 'PROP-1002', 'Commercial', '24 Market Road', 1800.00, 4200000.00),
(2, 'PROP-1003', 'Industrial', 'Plot 7, Small Industrial Area', 3000.00, 5800000.00);

-- Generate current year tax for each property.
CALL sp_generate_property_tax(1, YEAR(CURDATE()));
CALL sp_generate_property_tax(2, YEAR(CURDATE()));
CALL sp_generate_property_tax(3, YEAR(CURDATE()));

-- Create one overdue tax to demonstrate penalty trigger.
UPDATE taxes
SET due_date = DATE_SUB(CURDATE(), INTERVAL 75 DAY)
WHERE property_id = 1 AND tax_year = YEAR(CURDATE());

-- Sample payments.
INSERT INTO payments (tax_id, taxpayer_id, amount_paid, payment_method, payment_reference, payment_status)
VALUES
(
    (SELECT id FROM taxes WHERE property_id = 1 AND tax_year = YEAR(CURDATE())),
    1,
    10000.00,
    'Online',
    'PAY-DEMO-10001',
    'SUCCESS'
),
(
    (SELECT id FROM taxes WHERE property_id = 2 AND tax_year = YEAR(CURDATE())),
    1,
    15000.00,
    'UPI',
    'PAY-DEMO-10002',
    'SUCCESS'
);
