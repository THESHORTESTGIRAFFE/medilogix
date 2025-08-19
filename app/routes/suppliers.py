from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from db import query_db
from app.utils import log_audit_action, roles_required
from app.models import Supplier # Import the Supplier model
import datetime

bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

@bp.route('/')
@login_required
def list_suppliers():
    suppliers_data = query_db("SELECT * FROM suppliers ORDER BY name ASC")
    suppliers = [Supplier(**s) for s in suppliers_data] # Convert to Supplier objects
    return render_template('suppliers/list_suppliers.html', suppliers=suppliers)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
@roles_required(['admin', 'manager'])
def create_supplier():
    if request.method == 'POST':
        name = request.form.get('name')
        contact_person = request.form.get('contact_person')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        payment_terms = request.form.get('payment_terms')
        rating_str = request.form.get('rating')
        is_blacklisted = 'is_blacklisted' in request.form
        notes = request.form.get('notes')

        if not name:
            flash('Supplier Name is required.', 'danger')
        else:
            try:
                rating = float(rating_str) if rating_str else 0.00
                supplier_id = query_db("""
                    INSERT INTO suppliers 
                    (name, contact_person, phone, email, address, payment_terms, rating, is_blacklisted, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    name, contact_person, phone, email, address, payment_terms, rating, is_blacklisted, notes
                ), commit=True, is_insert=True)

                if supplier_id:
                    log_audit_action(f"Created Supplier ID: {supplier_id}", f"Name: {name}")
                    flash('Supplier added successfully!', 'success')
                    return redirect(url_for('suppliers.list_suppliers'))
                else:
                    flash('Failed to add supplier.', 'danger')
            except ValueError:
                flash('Invalid rating format.', 'danger')
            except Exception as e:
                current_app.logger.error(f"Error creating supplier by {current_user.username}: {str(e)}")
                flash(f'Error adding supplier: {str(e)}', 'danger')

    return render_template('suppliers/supplier_form.html', form_action="Add New")

@bp.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required(['admin', 'manager'])
def edit_supplier(supplier_id):
    supplier = query_db("SELECT * FROM suppliers WHERE id = %s", (supplier_id,), one=True)
    if not supplier:
        flash('Supplier not found.', 'danger')
        return redirect(url_for('suppliers.list_suppliers'))

    if request.method == 'POST':
        name = request.form.get('name')
        contact_person = request.form.get('contact_person')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        payment_terms = request.form.get('payment_terms')
        rating_str = request.form.get('rating')
        is_blacklisted = 'is_blacklisted' in request.form
        notes = request.form.get('notes')

        if not name:
            flash('Supplier Name is required.', 'danger')
        else:
            try:
                rating = float(rating_str) if rating_str else 0.00
                query_db("""
                    UPDATE suppliers 
                    SET name = %s, contact_person = %s, phone = %s, email = %s, address = %s, 
                        payment_terms = %s, rating = %s, is_blacklisted = %s, notes = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    name, contact_person, phone, email, address, 
                    payment_terms, rating, is_blacklisted, notes, supplier_id
                ), commit=True)

                log_audit_action(f"Updated Supplier ID: {supplier_id}", f"Name: {name}")
                flash('Supplier updated successfully!', 'success')
                return redirect(url_for('suppliers.list_suppliers'))
            except ValueError:
                flash('Invalid rating format.', 'danger')
            except Exception as e:
                current_app.logger.error(f"Error updating supplier {supplier_id} by {current_user.username}: {str(e)}")
                flash(f'Error updating supplier: {str(e)}', 'danger')

    return render_template('suppliers/supplier_form.html', form_action="Edit", supplier=supplier)

@bp.route('/<int:supplier_id>')
@login_required
def view_supplier(supplier_id):
    supplier_data = query_db("SELECT * FROM suppliers WHERE id = %s", (supplier_id,), one=True)
    if not supplier_data:
        flash('Supplier not found.', 'danger')
        return redirect(url_for('suppliers.list_suppliers'))
    
    supplier = Supplier(**supplier_data)

    # Placeholder for history of orders, deliveries, disputes (Phase 3.2, 3.3, 3.4)
    # For now, just display supplier details.

    return render_template('suppliers/view_supplier.html', supplier=supplier)
