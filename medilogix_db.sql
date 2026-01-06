-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Jun 12, 2025 at 03:40 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `medilogix_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `audit_logs`
--

CREATE TABLE `audit_logs` (
  `id` bigint(20) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `action` varchar(255) NOT NULL,
  `details` text DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `audit_logs`
--

INSERT INTO `audit_logs` (`id`, `user_id`, `action`, `details`, `ip_address`, `timestamp`) VALUES
(1, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-05-29 15:50:19'),
(2, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-05-29 16:02:48'),
(3, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-05-29 16:03:19'),
(4, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-05-29 18:03:57'),
(5, 1, 'Updated item ID 1: \'Laptop\'', NULL, '127.0.0.1', '2025-05-29 18:05:51'),
(6, 1, 'Updated item ID 1: \'Laptop\'', NULL, '127.0.0.1', '2025-05-29 18:06:15'),
(7, 1, 'Added location: \'Makhandeni Clinic\'', NULL, '127.0.0.1', '2025-05-29 18:07:24'),
(8, 1, 'Stock Movement: initial_stock', 'Item: Laptop (ID: 1), Qty: 1.0, Loc ID: 1', '127.0.0.1', '2025-05-29 18:08:57'),
(9, 1, 'Stock Movement: initial_stock', 'Item: Laptop (ID: 1), Qty: 100.0, Loc ID: 1', '127.0.0.1', '2025-05-29 18:10:11'),
(10, 1, 'Stock Movement: issuance', 'Item: Laptop (ID: 1), Qty: -1.0, Loc ID: 1', '127.0.0.1', '2025-05-29 18:11:05'),
(11, 1, 'Created Requisition ID: 1', NULL, '127.0.0.1', '2025-05-29 18:11:52'),
(12, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-05-29 18:13:10'),
(13, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-05-30 10:38:42'),
(14, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-05-30 18:54:04'),
(15, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-06-01 11:06:55'),
(16, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-06-01 11:18:02'),
(17, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-06-01 11:18:13'),
(18, 1, 'Added item: \'Printer\' (SKU: 1101)', NULL, '127.0.0.1', '2025-06-01 11:18:54'),
(19, 1, 'Added item category: \'Hospital Equipment\'', NULL, '127.0.0.1', '2025-06-01 11:19:19'),
(20, 1, 'Created Requisition ID: 2', NULL, '127.0.0.1', '2025-06-01 11:20:16'),
(21, 1, 'Stock Movement: initial_stock', 'Item: Printer (ID: 2), Qty: 100.0, Loc ID: 1', '127.0.0.1', '2025-06-01 11:21:09'),
(22, 1, 'Stock Movement: issuance', 'Item: Printer (ID: 2), Qty: -1.0, Loc ID: 1', '127.0.0.1', '2025-06-01 11:21:55'),
(23, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-06-01 11:22:36'),
(24, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-06-01 11:34:08'),
(25, 1, 'Added item: \'Medicine\' (SKU: 83)', NULL, '127.0.0.1', '2025-06-01 11:34:58'),
(26, 1, 'Added item category: \'Medicine\'', NULL, '127.0.0.1', '2025-06-01 11:35:13'),
(27, 1, 'Added location: \'UBH\'', NULL, '127.0.0.1', '2025-06-01 11:35:31'),
(28, 1, 'Stock Movement: initial_stock', 'Item: Medicine (ID: 3), Qty: 1000.0, Loc ID: 2', '127.0.0.1', '2025-06-01 11:36:21'),
(29, 1, 'Stock Movement: issuance', 'Item: Medicine (ID: 3), Qty: -10.0, Loc ID: 1', '127.0.0.1', '2025-06-01 11:37:12'),
(30, 1, 'Created Requisition ID: 3', NULL, '127.0.0.1', '2025-06-01 11:37:53'),
(31, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-06-01 11:38:30'),
(32, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-06-01 12:09:21'),
(33, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-06-01 12:24:53'),
(34, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-06-02 11:55:34'),
(35, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-06-02 12:55:40'),
(36, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-06-02 13:44:46'),
(37, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-06-02 14:05:26'),
(38, 2, 'User Registered', 'New user: siza, Email: test@mail.com', '127.0.0.1', '2025-06-08 15:24:32'),
(39, 2, 'Login Success', 'User \'siza\' logged in.', '127.0.0.1', '2025-06-08 15:24:42'),
(40, NULL, 'Login Failed - Invalid Credentials', 'Attempt by user: test', '127.0.0.1', '2025-06-09 13:21:32'),
(41, 3, 'User Registered', 'New user: test, Email: test@test.com', '127.0.0.1', '2025-06-09 13:23:20'),
(42, 3, 'Login Success', 'User \'test\' logged in.', '127.0.0.1', '2025-06-09 13:23:54'),
(43, 3, 'Created Requisition ID: 4', NULL, '127.0.0.1', '2025-06-09 13:32:00'),
(44, 3, 'Logout Success', 'User \'test\' logged out.', '127.0.0.1', '2025-06-09 13:33:00'),
(45, NULL, 'Login Failed - Invalid Credentials', 'Attempt by user: jody', '127.0.0.1', '2025-06-09 13:33:18'),
(46, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-06-09 13:33:25'),
(47, 1, 'User Updated by Admin', 'Admin \'jody\' updated user \'siza\' (ID: 2): Full Name to \'Siza Mkhize\'; Email to \'test@mail.com\'; Role to \'manager\'; Department ID to \'1\'; Active to \'False\'.', '127.0.0.1', '2025-06-09 13:35:24'),
(48, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-06-09 13:35:28'),
(49, 2, 'Login Failed - Inactive Account', 'Attempt by user: siza', '127.0.0.1', '2025-06-09 13:35:36'),
(50, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-06-09 13:36:03'),
(51, 1, 'User Updated by Admin', 'Admin \'jody\' updated user \'siza\' (ID: 2): Full Name to \'Siza Mkhize\'; Email to \'test@mail.com\'; Role to \'manager\'; Department ID to \'1\'; Active to \'True\'.', '127.0.0.1', '2025-06-09 13:36:43'),
(52, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-06-09 13:36:47'),
(53, 3, 'Login Success', 'User \'test\' logged in.', '127.0.0.1', '2025-06-09 13:36:55'),
(54, 3, 'Logout Success', 'User \'test\' logged out.', '127.0.0.1', '2025-06-09 13:37:06'),
(55, 2, 'Login Success', 'User \'siza\' logged in.', '127.0.0.1', '2025-06-09 13:37:15'),
(56, 2, 'Logout Success', 'User \'siza\' logged out.', '127.0.0.1', '2025-06-09 13:45:28'),
(57, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-06-09 13:45:37'),
(58, 1, 'Requisition Approved: ID 4', 'Approved by jody', '127.0.0.1', '2025-06-09 13:56:02'),
(59, 1, 'Requisition Rejected: ID 3', 'Rejected by jody. Reason: Too much', '127.0.0.1', '2025-06-09 13:59:19'),
(60, 1, 'Stock Movement: issuance', 'Item: Medicine (ID: 3), Qty: -12.0, Loc ID: 1', '127.0.0.1', '2025-06-09 14:01:16'),
(61, 1, 'Stock Movement: issuance', 'Item: Printer (ID: 2), Qty: -45.0, Loc ID: 2', '127.0.0.1', '2025-06-09 14:01:39'),
(62, 1, 'Logout Success', 'User \'jody\' logged out.', '127.0.0.1', '2025-06-09 14:52:25'),
(63, 1, 'Login Success', 'User \'jody\' logged in.', '127.0.0.1', '2025-06-11 12:06:39'),
(64, 1, 'Logout Success', 'User \'admin\' logged out.', '127.0.0.1', '2025-06-11 13:38:26'),
(65, 1, 'Login Success', 'User \'admin\' logged in.', '127.0.0.1', '2025-06-11 13:43:33'),
(66, 1, 'Logout Success', 'User \'admin\' logged out.', '127.0.0.1', '2025-06-11 14:23:39'),
(67, 1, 'Login Success', 'User \'admin\' logged in.', '127.0.0.1', '2025-06-12 09:27:53'),
(68, 1, 'Logout Success', 'User \'admin\' logged out.', '127.0.0.1', '2025-06-12 13:36:44'),
(69, 3, 'Login Success', 'User \'test\' logged in.', '127.0.0.1', '2025-06-12 13:36:56'),
(70, 3, 'Logout Success', 'User \'test\' logged out.', '127.0.0.1', '2025-06-12 13:37:05'),
(71, 1, 'Login Success', 'User \'admin\' logged in.', '127.0.0.1', '2025-06-12 13:37:19'),
(72, 1, 'Logout Success', 'User \'admin\' logged out.', '127.0.0.1', '2025-06-12 13:40:00');

-- --------------------------------------------------------

--
-- Table structure for table `departments`
--

CREATE TABLE `departments` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `departments`
--

INSERT INTO `departments` (`id`, `name`, `description`, `created_at`) VALUES
(1, 'Pharmacy', 'Manages medication inventory, dispensing, and pharmaceutical supply tracking.', '2022-11-04 22:00:00'),
(2, 'Procurement', 'Oversees sourcing, purchasing, and supplier engagement for hospital goods.', '2023-01-17 22:00:00'),
(3, 'Stores', 'Central unit for receiving, storing, and distributing physical inventory.', '2022-09-21 22:00:00'),
(4, 'ICT', 'Handles system support, hardware, and digital infrastructure maintenance.', '2023-03-11 22:00:00'),
(5, 'Finance', 'Monitors expenditure, budgeting, and resource cost tracking.', '2022-10-02 22:00:00'),
(6, 'Nursing', 'Coordinates clinical supply use and manages ward stock needs.', '2023-02-23 22:00:00'),
(7, 'Laboratory', 'Responsible for test-related consumables and diagnostic equipment.', '2022-12-06 22:00:00'),
(8, 'Maintenance', 'In charge of facility upkeep, equipment servicing, and repair workflows.', '2023-04-14 22:00:00');

-- --------------------------------------------------------

--
-- Table structure for table `items`
--

CREATE TABLE `items` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `sku` varchar(100) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `category_id` int(11) DEFAULT NULL,
  `unit_of_measure` varchar(50) DEFAULT NULL,
  `reorder_threshold` decimal(10,2) DEFAULT 0.00,
  `preferred_supplier_id` int(11) DEFAULT NULL,
  `image_path` varchar(255) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `items`
--

INSERT INTO `items` (`id`, `name`, `sku`, `description`, `category_id`, `unit_of_measure`, `reorder_threshold`, `preferred_supplier_id`, `image_path`, `notes`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'Paracetamol 500mg Tablets', 'PHRM-001', 'Used for pain relief and fever reduction.', 1, 'box of 100', 50.00, 1, 'images/paracetamol.jpg', 'Store below 25°C.', 1, '2025-06-11 13:13:30', '2025-06-11 13:13:30'),
(2, 'Surgical Gloves - Medium', 'PPE-003', 'Disposable latex gloves for sterile procedures.', 4, 'box of 100 pairs', 30.00, 2, 'images/gloves.jpg', 'Avoid direct sunlight.', 1, '2025-06-11 13:13:30', '2025-06-11 13:13:30'),
(3, 'Automatic Blood Pressure Monitor', 'EQPM-012', 'Electronic BP monitor with digital display.', 2, 'each', 5.00, 3, 'images/bp_monitor.jpg', 'Calibrate annually.', 1, '2025-06-11 13:13:30', '2025-06-11 13:13:30'),
(4, 'Hand Sanitizer 500ml', 'SAN-007', 'Alcohol-based sanitizer for infection control.', 8, 'bottle', 100.00, 4, 'images/sanitizer.jpg', 'Flammable; store securely.', 1, '2025-06-11 13:13:30', '2025-06-11 13:13:30'),
(5, 'Laboratory Test Tubes (Plastic)', 'LAB-015', 'For sample storage in lab procedures.', 3, 'pack of 50', 20.00, 5, 'images/test_tubes.jpg', 'Avoid heat exposure.', 1, '2025-06-11 13:13:30', '2025-06-11 13:13:30'),
(6, 'A4 Copier Paper', 'OFF-002', 'Standard white paper for printing and copying.', 5, 'ream (500 sheets)', 10.00, 6, 'images/copier_paper.jpg', 'Keep dry.', 1, '2025-06-11 13:13:30', '2025-06-11 13:13:30'),
(7, 'Core i5 Desktop Computer', 'ICT-006', 'Standard workstation for admin and data entry.', 6, 'unit', 3.00, 7, 'images/desktop.jpg', 'Includes pre-installed software.', 1, '2025-06-11 13:13:30', '2025-06-11 13:13:30');

-- --------------------------------------------------------

--
-- Table structure for table `item_categories`
--

CREATE TABLE `item_categories` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `item_categories`
--

INSERT INTO `item_categories` (`id`, `name`, `description`, `created_at`, `updated_at`) VALUES
(1, 'Pharmaceuticals', 'Medicines, vaccines, and consumable drugs used in patient care.', '2025-06-11 13:09:30', '2025-06-11 13:09:30'),
(2, 'Medical Equipment', 'Reusable diagnostic and therapeutic tools such as BP machines, ECG units, and surgical kits.', '2025-06-11 13:09:30', '2025-06-11 13:09:30'),
(3, 'Laboratory Supplies', 'Chemicals, test kits, and consumables used in medical testing.', '2025-06-11 13:09:30', '2025-06-11 13:09:30'),
(4, 'Protective Equipment', 'Personal protective equipment including gloves, masks, and gowns.', '2025-06-11 13:09:30', '2025-06-11 13:09:30'),
(5, 'Office Supplies', 'Stationery and administrative tools required for hospital operations.', '2025-06-11 13:09:30', '2025-06-11 13:09:30'),
(6, 'ICT Equipment', 'Computers, printers, and networking devices used in hospital information systems.', '2025-06-11 13:09:30', '2025-06-11 13:09:30'),
(7, 'Furniture', 'Desks, chairs, filing cabinets, and beds used in clinics and wards.', '2025-06-11 13:09:30', '2025-06-11 13:09:30'),
(8, 'Sanitation Supplies', 'Cleaning materials and disinfectants used in facility hygiene and infection prevention.', '2025-06-11 13:09:30', '2025-06-11 13:09:30'),
(9, 'Fuel & Utilities', 'Diesel, petrol, and energy-related resources needed for hospital generators and operations.', '2025-06-11 13:09:30', '2025-06-11 13:09:30');

-- --------------------------------------------------------

--
-- Table structure for table `item_locations`
--

CREATE TABLE `item_locations` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `item_locations`
--

INSERT INTO `item_locations` (`id`, `name`, `description`, `created_at`, `updated_at`) VALUES
(1, 'Parirenyatwa Group of Hospitals', 'Zimbabwe’s largest referral and teaching hospital based in Harare. Specializes in surgery, oncology, internal medicine, and is affiliated with the University of Zimbabwe. CMO: Dr T. Magure. Contact: +263 242 702992. Email: publicrelations@parihosp.org', '2025-06-11 13:02:24', '2025-06-11 13:02:24'),
(2, 'Sally Mugabe Central Hospital', 'A major urban referral hospital offering maternal health, emergency medicine, pediatrics, and surgical services. Located in Southerton, Harare. Acting CMO: Mr H. Mungani. Phone: +263 242 621143. Email: ceosechch@gmail.com', '2025-06-11 13:02:24', '2025-06-11 13:02:24'),
(3, 'Mpilo Central Hospital', 'Bulawayo’s largest referral hospital serving the southern region of Zimbabwe. Known for trauma care, maternity, and infectious disease units. CMO: Dr N. Dzvanga. Contact: +263 292 205078. Email: info@mpilo.org.zw', '2025-06-11 13:02:24', '2025-06-11 13:02:24'),
(4, 'Ingutsheni Central Hospital', 'Zimbabwe’s primary psychiatric referral hospital, focusing on mental health services and rehabilitation. Located in Bulawayo. CMO: Dr N. Mawere. Phone: +263 292 466463. Email: information@ingutshenihospital.org.zw', '2025-06-11 13:02:24', '2025-06-11 13:02:24'),
(5, 'Chitungwiza Central Hospital', 'Provides general and specialist care to the Chitungwiza community and surrounding areas. Known for surgical and maternal services. CMO: Dr R. Makota. Phone: +263 242 130917.', '2025-06-11 13:02:24', '2025-06-11 13:02:24'),
(6, 'United Bulawayo Hospitals (UBH)', 'A teaching and referral hospital offering surgery, obstetrics, and radiology services. Supports the National University of Science and Technology (NUST). CMO: Dr W. Busumani. Phone: +263 292 238397. Email: info@ubh.org.zw', '2025-06-11 13:02:24', '2025-06-11 13:02:24'),
(7, 'Kwekwe General Hospital', 'A provincial referral hospital for Midlands, offering emergency, internal medicine, and outpatient services. Med Sup: Dr G. Mahere. Phone: +263 5525 22333.', '2025-06-11 13:02:24', '2025-06-11 13:02:24'),
(8, 'Kadoma General Hospital', 'A general hospital serving Kadoma district. Offers inpatient, outpatient, maternity, and lab services. Med Sup: Dr Kudzaiishe Masendeke. Phone: +263 6821 22066.', '2025-06-11 13:02:24', '2025-06-11 13:02:24'),
(9, 'Chivhu General Hospital', 'Covers Chikomba District and surrounding areas, focusing on maternal and child health, TB, and general medicine. Med Sup: Dr G. T. Munjanja. Phone: +263 5421 256.', '2025-06-11 13:02:24', '2025-06-11 13:02:24'),
(10, 'Rusape General Hospital', 'A provincial facility in Manicaland with focus on HIV/AIDS care, outpatient services, and maternity. Med Sup: Dr Karembo. Phone: +263 25205 3377.', '2025-06-11 13:02:24', '2025-06-11 13:02:24'),
(11, 'Ministry of Health and Child Care – Head Office', 'National policy, planning, and administration headquarters for Zimbabwe’s public health system. Located in Harare. Phone: +263 242 798555. Email: pr@mohcc.gov.zw', '2025-06-11 13:02:24', '2025-06-11 13:02:24');

-- --------------------------------------------------------

--
-- Table structure for table `suppliers`
--

CREATE TABLE `suppliers` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `contact_person` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `suppliers`
--

INSERT INTO `suppliers` (`id`, `name`, `contact_person`, `email`, `phone`, `address`, `notes`, `created_at`, `updated_at`) VALUES
(1, 'NatPharm', 'Dr. J. Moyo', 'info@natpharm.co.zw', '+263-242-789012', '123 Healthway, Harare', 'Primary supplier for essential medicines and medical sundries.', '2025-06-12 10:00:00', '2025-06-12 10:00:00'),
(2, 'MediSupply Distributors', 'Ms. S. Ncube', 'sales@medisupply.co.zw', '+263-772-123456', '45 Medical Ave, Bulawayo', 'Specializes in PPE and laboratory consumables.', '2025-06-12 10:00:00', '2025-06-12 10:00:00'),
(3, 'TechMed Solutions', 'Mr. T. Dube', 'info@techmed.co.zw', '+263-712-987654', '78 Innovation Rd, Harare', 'Supplier of medical equipment and devices.', '2025-06-12 10:00:00', '2025-06-12 10:00:00'),
(4, 'CleanCare Products', 'Mrs. R. Sibanda', 'orders@cleancare.co.zw', '+263-783-456789', '10 Sanitation St, Gweru', 'Provides cleaning and sanitation supplies.', '2025-06-12 10:00:00', '2025-06-12 10:00:00');

-- --------------------------------------------------------

--
-- Table structure for table `suppliers`
--

CREATE TABLE `suppliers` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `contact_person` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `suppliers`
--

INSERT INTO `suppliers` (`id`, `name`, `contact_person`, `email`, `phone`, `address`, `notes`, `created_at`, `updated_at`) VALUES
(1, 'NatPharm', 'Dr. J. Moyo', 'info@natpharm.co.zw', '+263-242-789012', '123 Healthway, Harare', 'Primary supplier for essential medicines and medical sundries.', '2025-06-12 10:00:00', '2025-06-12 10:00:00'),
(2, 'MediSupply Distributors', 'Ms. S. Ncube', 'sales@medisupply.co.zw', '+263-772-123456', '45 Medical Ave, Bulawayo', 'Specializes in PPE and laboratory consumables.', '2025-06-12 10:00:00', '2025-06-12 10:00:00'),
(3, 'TechMed Solutions', 'Mr. T. Dube', 'info@techmed.co.zw', '+263-712-987654', '78 Innovation Rd, Harare', 'Supplier of medical equipment and devices.', '2025-06-12 10:00:00', '2025-06-12 10:00:00'),
(4, 'CleanCare Products', 'Mrs. R. Sibanda', 'orders@cleancare.co.zw', '+263-783-456789', '10 Sanitation St, Gweru', 'Provides cleaning and sanitation supplies.', '2025-06-12 10:00:00', '2025-06-12 10:00:00');

-- --------------------------------------------------------

--
-- Table structure for table `purchase_orders`
--

CREATE TABLE `purchase_orders` (
  `id` int(11) NOT NULL,
  `supplier_id` int(11) NOT NULL,
  `order_date` date NOT NULL,
  `expected_delivery_date` date DEFAULT NULL,
  `status` enum('Pending','Approved','Rejected','Ordered','Partially Received','Received','Cancelled') NOT NULL DEFAULT 'Pending',
  `total_amount` decimal(12,2) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `hash` varchar(64) DEFAULT NULL,
  `previous_hash` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `goods_received_notes`
--

CREATE TABLE `goods_received_notes` (
  `id` int(11) NOT NULL,
  `purchase_order_id` int(11) NOT NULL,
  `received_date` date NOT NULL,
  `received_by_user_id` int(11) NOT NULL,
  `delivery_note_number` varchar(255) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `hash` varchar(64) DEFAULT NULL,
  `previous_hash` varchar(64) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `audit_chain_metadata`
--

CREATE TABLE `audit_chain_metadata` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `record_type` varchar(50) NOT NULL UNIQUE,
  `last_hash` varchar(64) DEFAULT NULL,
  `last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `audit_logs`
--
ALTER TABLE `audit_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `departments`
--
ALTER TABLE `departments`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `items`
--
ALTER TABLE `items`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `sku` (`sku`),
  ADD KEY `category_id` (`category_id`),
  ADD KEY `idx_item_name` (`name`);

--
-- Indexes for table `item_categories`
--
ALTER TABLE `item_categories`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `item_locations`
--
ALTER TABLE `item_locations`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `requisitions`
--
ALTER TABLE `requisitions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `department_id` (`department_id`),
  ADD KEY `approved_by_id` (`approved_by_id`),
  ADD KEY `idx_requisition_requester` (`requester_id`),
  ADD KEY `idx_requisition_status` (`status`);

--
-- Indexes for table `requisition_items`
--
ALTER TABLE `requisition_items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `requisition_id` (`requisition_id`),
  ADD KEY `item_id` (`item_id`);

--
-- Indexes for table `goods_received_notes`
--
ALTER TABLE `goods_received_notes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `purchase_order_id` (`purchase_order_id`),
  ADD KEY `received_by_user_id` (`received_by_user_id`);

--
-- Indexes for table `audit_chain_metadata`
--
ALTER TABLE `audit_chain_metadata`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `record_type` (`record_type`);

--
-- Indexes for table `stock_movements`
--
ALTER TABLE `stock_movements`
  ADD PRIMARY KEY (`id`),
  ADD KEY `location_id` (`location_id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `idx_stock_item_date` (`item_id`,`movement_date`),
  ADD KEY `idx_stock_location` (`item_id`,`location_id`);

--
-- Indexes for table `tracked_assets`
--
ALTER TABLE `tracked_assets`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_item_serial` (`item_id`,`serial_number`),
  ADD KEY `assigned_to_user_id` (`assigned_to_user_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `department_id` (`department_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `audit_logs`
--
ALTER TABLE `audit_logs`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=73;

--
-- AUTO_INCREMENT for table `departments`
--
ALTER TABLE `departments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `items`
--
ALTER TABLE `items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `item_categories`
--
ALTER TABLE `item_categories`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `item_locations`
--
ALTER TABLE `item_locations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `requisitions`
--
ALTER TABLE `requisitions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `requisition_items`
--
ALTER TABLE `requisition_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `goods_received_notes`
--
ALTER TABLE `goods_received_notes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `audit_chain_metadata`
--
ALTER TABLE `audit_chain_metadata`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `stock_movements`
--
ALTER TABLE `stock_movements`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT for table `tracked_assets`
--
ALTER TABLE `tracked_assets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `audit_logs`
--
ALTER TABLE `audit_logs`
  ADD CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `items`
--
ALTER TABLE `items`
  ADD CONSTRAINT `items_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `item_categories` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `requisitions`
--
ALTER TABLE `requisitions`
  ADD CONSTRAINT `requisitions_ibfk_1` FOREIGN KEY (`requester_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `requisitions_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `requisitions_ibfk_3` FOREIGN KEY (`approved_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `requisition_items`
--
ALTER TABLE `requisition_items`
  ADD CONSTRAINT `requisition_items_ibfk_1` FOREIGN KEY (`requisition_id`) REFERENCES `requisitions` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `requisition_items_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`);

--
-- Constraints for table `stock_movements`
--
ALTER TABLE `stock_movements`
  ADD CONSTRAINT `stock_movements_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `stock_movements_ibfk_2` FOREIGN KEY (`location_id`) REFERENCES `item_locations` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `stock_movements_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `goods_received_notes`
--
ALTER TABLE `goods_received_notes`
  ADD CONSTRAINT `goods_received_notes_ibfk_1` FOREIGN KEY (`purchase_order_id`) REFERENCES `purchase_orders` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `goods_received_notes_ibfk_2` FOREIGN KEY (`received_by_user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT;

--
-- Constraints for table `tracked_assets`
--
ALTER TABLE `tracked_assets`
  ADD CONSTRAINT `tracked_assets_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`),
  ADD CONSTRAINT `tracked_assets_ibfk_2` FOREIGN KEY (`assigned_to_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
