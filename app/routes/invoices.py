from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from db import query_db
from app.utils import log_audit_action, roles_required
from app.models import Invoice # Import the Invoice model
import datetime
import os
from werkzeug.utils import secure_filename

bp = Blueprint('invoices', __name__, url_prefix='/invoices')

# Helper function to check allowed extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/')
@login_required
def list_invoices():
    invoices_data = query_db("""
        SELECT i.*, s.name as supplier_name, u.full_name as uploaded_by_user_name
        FROM invoices i
        JOIN suppliers s ON i.supplier_id = s.id
        JOIN users u ON i.uploaded_by_user_id = u.id
        ORDER BY i.invoice_date DESC
    """)
    invoices = [Invoice(**inv) for inv in invoices_data]
    return render_template('invoices/list_invoices.html', invoices=invoices)

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
@roles_required(['admin', 'manager'])
def upload_invoice():
    suppliers = query_db("SELECT id, name FROM suppliers ORDER BY name ASC")
    purchase_orders = query_db("SELECT id FROM purchase_orders ORDER BY id DESC")
    grns = query_db("SELECT id FROM goods_received_notes ORDER BY id DESC")

    if request.method == 'POST':
        invoice_number = request.form.get('invoice_number')
        supplier_id = request.form.get('supplier_id', type=int)
        invoice_date_str = request.form.get('invoice_date')
        amount_str = request.form.get('amount')
        currency = request.form.get('currency')
        due_date_str = request.form.get('due_date')
        status = request.form.get('status')
        related_po_id = request.form.get('related_po_id', type=int)
        related_grn_id = request.form.get('related_grn_id', type=int)
        notes = request.form.get('notes')

        # File upload handling
        if 'invoice_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['invoice_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if not all([invoice_number, supplier_id, invoice_date_str, amount_str, currency]):
            flash('Invoice Number, Supplier, Invoice Date, Amount, and Currency are required.', 'danger')
        elif file and allowed_file(file.filename):
            try:
                invoice_date = datetime.datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
                amount = float(amount_str)
                due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None

                filename = secure_filename(file.filename)
                # Ensure the upload folder exists
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                invoice_id = query_db("""
                    INSERT INTO invoices 
                    (invoice_number, supplier_id, invoice_date, amount, currency, due_date, status, 
                     file_path, related_po_id, related_grn_id, notes, uploaded_by_user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    invoice_number, supplier_id, invoice_date, amount, currency, due_date, status,
                    filename, related_po_id, related_grn_id, notes, current_user.id
                ), commit=True, is_insert=True)

                if invoice_id:
                    log_audit_action(f"Uploaded Invoice ID: {invoice_id}", f"Number: {invoice_number}, File: {filename}")
                    flash('Invoice uploaded successfully!', 'success')
                    return redirect(url_for('invoices.list_invoices'))
                else:
                    flash('Failed to upload invoice record.', 'danger')
            except ValueError as ve:
                flash(f'Invalid date or amount format: {str(ve)}', 'danger')
            except Exception as e:
                current_app.logger.error(f"Error uploading invoice by {current_user.username}: {str(e)}")
                flash(f'Error uploading invoice: {str(e)}', 'danger')
        else:
            flash('Allowed file types are PDF, PNG, JPG, JPEG, GIF', 'danger')

    return render_template('invoices/invoice_upload_form.html', 
                           suppliers=suppliers, 
                           purchase_orders=purchase_orders, 
                           grns=grns,
                           current_date=datetime.date.today().strftime('%Y-%m-%d'))

@bp.route('/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    invoice_data = query_db("""
        SELECT i.*, s.name as supplier_name, u.full_name as uploaded_by_user_name
        FROM invoices i
        JOIN suppliers s ON i.supplier_id = s.id
        JOIN users u ON i.uploaded_by_user_id = u.id
        WHERE i.id = %s
    """, (invoice_id,), one=True)

    if not invoice_data:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('invoices.list_invoices'))

    return render_template('invoices/view_invoice.html', invoice=invoice_data)

@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
