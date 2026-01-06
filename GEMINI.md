# MediLogix Project Plan

## Current Status
Project renaming from 'SAMS' to 'MediLogix' completed across the codebase.
All features outlined in the original `to-do.md` file have been implemented.

## New Features to Implement

### 1. Supplier & Procurement Integration
- Linked with external supplier APIs (e.g., NatPharm) - **Partially Implemented (Database Schema, CRUD for Suppliers, POs)**
- Attach delivery notes, GRNs, and invoice uploads - **Pending**
- Generate automated purchase orders based on stock thresholds - **Pending**

### 2. Predictive Analytics + AI
- Use historical stock movements to forecast demand - **Pending**
- Alert on trends: expiry surges, unusual stockouts, department overuse - **Pending**

### 3. Mobile-First Enhancements
- Offline-first Progressive Web App (PWA) for rural clinics - **Pending**
- Scan QR/barcodes for receiving and issuing items - **Pending**

## Current State (as of 2025-08-19)
We have completed all features outlined in the original `to-do.md` file. The last issue, a `NameError` related to the `invoices_bp` blueprint, has been addressed by ensuring all route decorators in `app/routes/invoices.py` correctly reference `invoices_bp`. The application should now run without that specific error.

We have successfully implemented the "Blockchain-Based Audit Trails" feature.


