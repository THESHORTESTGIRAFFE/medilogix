from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort, Response
from weasyprint import HTML
from flask_login import login_required, current_user
from db import query_db
from app.utils import log_audit_action, roles_required, calculate_hash
from app.models import PurchaseOrder # Import the PurchaseOrder model
from app.notifications import send_email
import datetime
import csv
import io

bp = Blueprint('purchase_orders', __name__, url_prefix='/purchase_orders')

@bp.route('/')
@login_required
def list_purchase_orders():
    purchase_orders_data = query_db("""
        SELECT po.*, s.name as supplier_name
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        ORDER BY po.order_date DESC
    """)
    purchase_orders = [PurchaseOrder(**po) for po in purchase_orders_data]
    return render_template('purchase_orders/list_purchase_orders.html', purchase_orders=purchase_orders)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
@roles_required(['admin', 'manager'])
def create_purchase_order():
    suppliers = query_db("SELECT id, name FROM suppliers ORDER BY name ASC")
    items_for_selection = query_db("SELECT id, name, sku, unit_of_measure FROM items WHERE is_active = TRUE ORDER BY name ASC")

    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id', type=int)
        order_date_str = request.form.get('order_date')
        expected_delivery_date_str = request.form.get('expected_delivery_date')
        notes = request.form.get('notes')

        if not all([supplier_id, order_date_str]):
            flash('Supplier and Order Date are required.', 'danger')
        else:
            try:
                order_date = datetime.datetime.strptime(order_date_str, '%Y-%m-%d').date()
                expected_delivery_date = None
                if expected_delivery_date_str:
                    expected_delivery_date = datetime.datetime.strptime(expected_delivery_date_str, '%Y-%m-%d').date()

                po_items_data = []
                total_amount = 0.00
                i = 0
                while True:
                    item_id = request.form.get(f'item_id_{i}')
                    quantity = request.form.get(f'quantity_{i}')
                    unit_price = request.form.get(f'unit_price_{i}')
                    if item_id and quantity and unit_price:
                        try:
                            qty = float(quantity)
                            price = float(unit_price)
                            item_total = qty * price
                            po_items_data.append({
                                'item_id': int(item_id),
                                'quantity': qty,
                                'unit_price': price,
                                'total_price': item_total
                            })
                            total_amount += item_total
                        except ValueError:
                            flash('Invalid quantity or unit price for one or more items.', 'danger')
                            return render_template('purchase_orders/purchase_order_form.html', 
                                                   suppliers=suppliers, 
                                                   items_for_selection=items_for_selection, 
                                                   form_data=request.form, 
                                                   form_action="Create New")
                    elif i > 0 and not item_id and not quantity and not unit_price: # Stop if no more items are found after the first
                        break
                    elif i == 0 and not item_id and not quantity and not unit_price: # No items submitted at all
                        flash('At least one item must be added to the purchase order.', 'danger')
                        return render_template('purchase_orders/purchase_order_form.html', 
                                               suppliers=suppliers, 
                                               items_for_selection=items_for_selection, 
                                               form_data=request.form, 
                                               form_action="Create New")
                    i += 1
                
                if not po_items_data:
                    flash('At least one item must be added to the purchase order.', 'danger')
                else:
                    # --- Blockchain Audit Trail ---
                    previous_hash_record = query_db("SELECT last_hash FROM audit_chain_metadata WHERE record_type = %s", ('purchase_order',), one=True)
                    previous_hash = previous_hash_record['last_hash'] if previous_hash_record else None

                    po_id = query_db("""
                        INSERT INTO purchase_orders 
                        (supplier_id, order_date, expected_delivery_date, total_amount, notes, status, previous_hash)
                        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """, (
                        supplier_id, order_date, expected_delivery_date, total_amount, notes, 'Pending Approval (Dept Head)', previous_hash
                    ), commit=True, one=True)['id']

                    if po_id:
                        # Now, calculate the hash of the full record
                        record_data = {
                            'id': po_id,
                            'supplier_id': supplier_id,
                            'order_date': order_date,
                            'expected_delivery_date': expected_delivery_date,
                            'total_amount': total_amount,
                            'notes': notes,
                            'status': 'Pending Approval (Dept Head)',
                            'previous_hash': previous_hash
                        }
                        current_hash = calculate_hash(record_data)

                        # Update the record with its own hash
                        query_db("UPDATE purchase_orders SET hash = %s WHERE id = %s", (current_hash, po_id), commit=True)

                        # Update the metadata table with the new hash
                        query_db("""
                            INSERT INTO audit_chain_metadata (record_type, last_hash) 
                            VALUES (%s, %s) 
                            ON DUPLICATE KEY UPDATE last_hash = VALUES(last_hash)
                        """, ('purchase_order', current_hash), commit=True)
                        # --- End Blockchain Audit Trail ---

                        for item_data in po_items_data:
                            query_db("""
                                INSERT INTO purchase_order_items 
                                (purchase_order_id, item_id, quantity, unit_price, total_price)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (
                                po_id, item_data['item_id'], item_data['quantity'], 
                                item_data['unit_price'], item_data['total_price']
                            ), commit=True)
                        
                        log_audit_action(f"Created Purchase Order ID: {po_id}", f"Supplier: {supplier_id}")
                        flash('Purchase Order created successfully!', 'success')
                        return redirect(url_for('purchase_orders.list_purchase_orders'))
                    else:
                        flash('Failed to create purchase order record.', 'danger')

            except ValueError as ve:
                flash(f'Invalid date format: {str(ve)}', 'danger')
            except Exception as e:
                current_app.logger.error(f"Error creating PO by {current_user.username}: {str(e)}")
                flash(f'Error creating purchase order: {str(e)}', 'danger')
        
        return render_template('purchase_orders/purchase_order_form.html', 
                               suppliers=suppliers, 
                               items_for_selection=items_for_selection, 
                               form_data=request.form, 
                               form_action="Create New")

    return render_template('purchase_orders/purchase_order_form.html', 
                           suppliers=suppliers, 
                           items_for_selection=items_for_selection, 
                           form_action="Create New",
                           current_date=datetime.date.today().strftime('%Y-%m-%d'))

@bp.route('/<int:po_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required(['admin', 'manager'])
def edit_purchase_order(po_id):
    po_data = query_db("SELECT * FROM purchase_orders WHERE id = %s", (po_id,), one=True)
    if not po_data:
        flash('Purchase Order not found.', 'danger')
        return redirect(url_for('purchase_orders.list_purchase_orders'))

    po_items_data = query_db("SELECT * FROM purchase_order_items WHERE purchase_order_id = %s", (po_id,))

    suppliers = query_db("SELECT id, name FROM suppliers ORDER BY name ASC")
    items_for_selection = query_db("SELECT id, name, sku, unit_of_measure FROM items WHERE is_active = TRUE ORDER BY name ASC")

    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id', type=int)
        order_date_str = request.form.get('order_date')
        expected_delivery_date_str = request.form.get('expected_delivery_date')
        notes = request.form.get('notes')
        status = request.form.get('status') # Allow status update

        if not all([supplier_id, order_date_str]):
            flash('Supplier and Order Date are required.', 'danger')
        else:
            try:
                order_date = datetime.datetime.strptime(order_date_str, '%Y-%m-%d').date()
                expected_delivery_date = None
                if expected_delivery_date_str:
                    expected_delivery_date = datetime.datetime.strptime(expected_delivery_date_str, '%Y-%m-%d').date()

                po_items_data_updated = []
                total_amount = 0.00
                i = 0
                while True:
                    item_id = request.form.get(f'item_id_{i}')
                    quantity = request.form.get(f'quantity_{i}')
                    unit_price = request.form.get(f'unit_price_{i}')
                    if item_id and quantity and unit_price:
                        try:
                            qty = float(quantity)
                            price = float(unit_price)
                            item_total = qty * price
                            po_items_data_updated.append({
                                'item_id': int(item_id),
                                'quantity': qty,
                                'unit_price': price,
                                'total_price': item_total
                            })
                            total_amount += item_total
                        except ValueError:
                            flash('Invalid quantity or unit price for one or more items.', 'danger')
                            return render_template('purchase_orders/purchase_order_form.html', 
                                                   suppliers=suppliers, 
                                                   items_for_selection=items_for_selection, 
                                                   form_data=request.form, 
                                                   form_action="Edit", 
                                                   purchase_order=po_data, 
                                                   po_items=po_items_data_updated)
                    elif i > 0 and not item_id and not quantity and not unit_price:
                        break
                    elif i == 0 and not item_id and not quantity and not unit_price:
                        flash('At least one item must be added to the purchase order.', 'danger')
                        return render_template('purchase_orders/purchase_order_form.html', 
                                               suppliers=suppliers, 
                                               items_for_selection=items_for_selection, 
                                               form_data=request.form, 
                                               form_action="Edit", 
                                               purchase_order=po_data, 
                                               po_items=po_items_data_updated)
                    i += 1
                
                if not po_items_data_updated:
                    flash('At least one item must be added to the purchase order.', 'danger')
                else:
                    query_db("""
                        UPDATE purchase_orders 
                        SET supplier_id = %s, order_date = %s, expected_delivery_date = %s, 
                            total_amount = %s, notes = %s, status = %s, updated_at = CURRENT_TIMESTAMP, 
                            hash = %s, previous_hash = %s
                        WHERE id = %s
                    """, (
                        supplier_id, order_date, expected_delivery_date, 
                        total_amount, notes, status, current_hash, previous_hash, po_id
                    ), commit=True)

                    # Update the metadata table with the new hash
                    query_db("""
                        INSERT INTO audit_chain_metadata (record_type, last_hash) 
                        VALUES (%s, %s) 
                        ON DUPLICATE KEY UPDATE last_hash = VALUES(last_hash)
                    """, ('purchase_order', current_hash), commit=True)
                    # --- End Blockchain Audit Trail ---

                    # Delete old items and insert new ones
                    query_db("DELETE FROM purchase_order_items WHERE purchase_order_id = %s", (po_id,), commit=True)
                    for item_data in po_items_data_updated:
                        query_db("""
                            INSERT INTO purchase_order_items 
                            (purchase_order_id, item_id, quantity, unit_price, total_price)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            po_id, item_data['item_id'], item_data['quantity'], 
                            item_data['unit_price'], item_data['total_price']
                        ), commit=True)
                    
                    log_audit_action(f"Updated Purchase Order ID: {po_id}", f"Supplier: {supplier_id}")
                    flash('Purchase Order updated successfully!', 'success')
                    return redirect(url_for('purchase_orders.list_purchase_orders'))

            except ValueError as ve:
                flash(f'Invalid date format: {str(ve)}', 'danger')
            except Exception as e:
                current_app.logger.error(f"Error updating PO {po_id} by {current_user.username}: {str(e)}")
                flash(f'Error updating purchase order: {str(e)}', 'danger')
        
        return render_template('purchase_orders/purchase_order_form.html', 
                               suppliers=suppliers, 
                               items_for_selection=items_for_selection, 
                               form_data=request.form, 
                               form_action="Edit", 
                               purchase_order=po_data, 
                               po_items=po_items_data_updated)

    return render_template('purchase_orders/purchase_order_form.html', 
                           suppliers=suppliers, 
                           items_for_selection=items_for_selection, 
                           form_action="Edit", 
                           purchase_order=po_data, 
                           po_items=po_items_data)

@bp.route('/<int:po_id>')
@login_required
def view_purchase_order(po_id):
    po_data = query_db("""
        SELECT po.*, s.name as supplier_name
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        WHERE po.id = %s
    """, (po_id,), one=True)

    if not po_data:
        flash('Purchase Order not found.', 'danger')
        return redirect(url_for('purchase_orders.list_purchase_orders'))

    po_items_data = query_db("""
        SELECT poi.*, i.name as item_name, i.sku as item_sku, i.unit_of_measure as item_unit
        FROM purchase_order_items poi
        JOIN items i ON poi.item_id = i.id
        WHERE poi.purchase_order_id = %s
    """, (po_id,))

    approval_history = query_db("""
        SELECT ph.status_before, ph.status_after, ph.notes, ph.timestamp, u.full_name
        FROM po_approval_history ph
        JOIN users u ON ph.user_id = u.id
        WHERE ph.po_id = %s
        ORDER BY ph.timestamp ASC
    """, (po_id,))

    return render_template('purchase_orders/view_purchase_order.html', 
                           purchase_order=po_data, 
                           po_items=po_items_data,
                           approval_history=approval_history)

@bp.route('/<int:po_id>/approve', methods=['POST'])
@login_required
def approve_po(po_id):
    po = query_db("SELECT * FROM purchase_orders WHERE id = %s", (po_id,), one=True)
    if not po:
        flash('Purchase Order not found.', 'danger')
        return redirect(url_for('purchase_orders.list_purchase_orders'))

    action = request.form.get('action')
    notes = request.form.get('approval_notes')
    
    current_status = po['status']
    new_status = None
    notification_recipient = None

    # Define the roles required for each approval step
    approval_roles = {
        'Pending Approval (Dept Head)': 'dept_head',
        'Pending Approval (Procurement)': 'procurement_officer',
        'Pending Approval (Finance)': 'finance_officer',
    }

    # Check if the user has the required role for the action
    can_approve = current_user.role == 'admin' or (required_role and current_user.role == required_role)
    can_reject = current_user.role == 'admin' or current_user.role in approval_roles.values()

    if action == 'reject' and can_reject:
        new_status = 'Rejected'
    elif action.startswith('approve_') and can_approve:
        if action == 'approve_dept_head' and current_status == 'Pending Approval (Dept Head)':
            new_status = 'Pending Approval (Procurement)'
            notification_recipient = 'procurement_officer'
        elif action == 'approve_procurement' and current_status == 'Pending Approval (Procurement)':
            new_status = 'Pending Approval (Finance)'
            notification_recipient = 'finance_officer'
        elif action == 'approve_finance' and current_status == 'Pending Approval (Finance)':
            new_status = 'Approved'
    else:
        flash('You are not authorized to perform this action.', 'danger')
        return redirect(url_for('purchase_orders.view_purchase_order', po_id=po_id))

    if new_status:
        try:
            # Log the approval action
            query_db("""
                INSERT INTO po_approval_history (po_id, user_id, status_before, status_after, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (po_id, current_user.id, current_status, new_status, notes), commit=True)

            query_db("UPDATE purchase_orders SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s", (new_status, po_id), commit=True)
            
            log_message = f"PO #{po_id} status changed from '{current_status}' to '{new_status}' by {current_user.username}."
            if notes:
                log_message += f" Notes: {notes}"
            
            log_audit_action('PO Status Change', log_message)
            flash(f'Purchase Order #{po_id} has been {new_status}.', 'success')

            # Send notification to the next approver
            if notification_recipient:
                users_to_notify = query_db("SELECT email FROM users WHERE role = %s AND is_active = TRUE", (notification_recipient,))
                for user in users_to_notify:
                    send_email(user['email'], 
                               f'Purchase Order #{po_id} requires your approval', 
                               'email/po_approval_notification.html', 
                               po_id=po_id, 
                               new_status=new_status)

        except Exception as e:
            current_app.logger.error(f"Error updating PO status for PO ID {po_id} by {current_user.username}: {str(e)}")
            flash('Error updating purchase order status.', 'danger')
    else:
        flash('Invalid action or PO status.', 'warning')

    return redirect(url_for('purchase_orders.view_purchase_order', po_id=po_id))

@bp.route('/<int:po_id>/export/pdf')
@login_required
def export_po_pdf(po_id):
    po_data = query_db("""
        SELECT po.*, s.name as supplier_name, s.address as supplier_address, s.email as supplier_email
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        WHERE po.id = %s
    """, (po_id,), one=True)

    if not po_data:
        flash('Purchase Order not found.', 'danger')
        return redirect(url_for('purchase_orders.list_purchase_orders'))

    po_items_data = query_db("""
        SELECT poi.*, i.name as item_name, i.sku as item_sku, i.unit_of_measure as item_unit
        FROM purchase_order_items poi
        JOIN items i ON poi.item_id = i.id
        WHERE poi.purchase_order_id = %s
    """, (po_id,))

    # For PDF rendering, we might want to pass the absolute URL for static assets if any are used
    base_url = request.url_root

    html_out = render_template('purchase_orders/purchase_order_pdf.html', 
                               purchase_order=po_data, 
                               po_items=po_items_data,
                               base_url=base_url)
    
    pdf_bytes = HTML(string=html_out, base_url=base_url).write_pdf()

    response = Response(pdf_bytes, mimetype='application/pdf')
    response.headers['Content-Disposition'] = f'attachment; filename=PO_{po_id}.pdf'
    return response

@bp.route('/<int:po_id>/export/csv')
@login_required
def export_po_csv(po_id):
    po_items_data = query_db("""
        SELECT poi.item_id, i.name as item_name, i.sku as item_sku, poi.quantity, poi.unit_price, poi.total_price
        FROM purchase_order_items poi
        JOIN items i ON poi.item_id = i.id
        WHERE poi.purchase_order_id = %s
    """, (po_id,))

    if not po_items_data:
        flash('No items found for this purchase order.', 'danger')
        return redirect(url_for('purchase_orders.view_purchase_order', po_id=po_id))

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Item ID', 'Item Name', 'SKU', 'Quantity', 'Unit Price', 'Total Price'])
    
    # Write data
    for item in po_items_data:
        writer.writerow([item['item_id'], item['item_name'], item['item_sku'], item['quantity'], item['unit_price'], item['total_price']])
    
    output.seek(0)
    
    response = Response(output, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=PO_{po_id}_items.csv'
    return response

@bp.route('/auto-generate', methods=['GET'])
@login_required
@roles_required(['admin', 'manager', 'procurement_officer'])
def auto_generate_pos():
    from app.utils import get_low_stock_items # Import here to avoid circular dependency
    
    # 1. Identify low stock items
    low_stock_items = get_low_stock_items(threshold_multiplier=1.0)
    
    if not low_stock_items:
        flash('No items are currently below their reorder threshold.', 'info')
        return redirect(url_for('purchase_orders.list_purchase_orders'))
    
    # 2. Group by preferred supplier
    items_by_supplier = {}
    for item in low_stock_items:
        supplier_id = item['preferred_supplier_id']
        if not supplier_id:
            # Handle items without a preferred supplier
            continue
            
        if supplier_id not in items_by_supplier:
            items_by_supplier[supplier_id] = {
                'supplier_name': item['preferred_supplier_name'],
                'items': []
            }
        items_by_supplier[supplier_id]['items'].append(item)
    
    generated_count = 0
    
    # 3. Create Draft POs
    for supplier_id, data in items_by_supplier.items():
        try:
            # --- Blockchain Audit Trail ---
            previous_hash_record = query_db("SELECT last_hash FROM audit_chain_metadata WHERE record_type = %s", ('purchase_order',), one=True)
            previous_hash = previous_hash_record['last_hash'] if previous_hash_record else None

            po_id = query_db("""
                INSERT INTO purchase_orders 
                (supplier_id, order_date, status, notes, previous_hash)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (
                supplier_id, datetime.date.today(), 'Draft', 'Auto-generated based on low stock alerts', previous_hash
            ), commit=True, one=True)['id']
            
            if po_id:
                 # Calculate hash for PO
                record_data = {
                    'id': po_id,
                    'supplier_id': supplier_id,
                    'order_date': datetime.date.today(),
                    'status': 'Draft',
                    'notes': 'Auto-generated based on low stock alerts',
                    'previous_hash': previous_hash
                }
                current_hash = calculate_hash(record_data)
                query_db("UPDATE purchase_orders SET hash = %s WHERE id = %s", (current_hash, po_id), commit=True)
                query_db("""
                    INSERT INTO audit_chain_metadata (record_type, last_hash) 
                    VALUES (%s, %s) 
                    ON DUPLICATE KEY UPDATE last_hash = VALUES(last_hash)
                """, ('purchase_order', current_hash), commit=True)


                # Add items to PO
                for item in data['items']:
                    # Logic: Restock to (threshold * 2) - current_stock
                    target_stock = float(item['reorder_threshold']) * 2
                    qty_to_order = target_stock - float(item['current_stock'])
                    
                    if qty_to_order <= 0:
                        qty_to_order = item['reorder_quantity'] # Fallback
                    
                    unit_price = 0.00 
                    
                    query_db("""
                        INSERT INTO purchase_order_items 
                        (purchase_order_id, item_id, quantity, unit_price, total_price)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        po_id, item['id'], qty_to_order, unit_price, 0.00
                    ), commit=True)
                
                log_audit_action(f"Auto-Generated PO ID: {po_id}", f"Supplier: {data['supplier_name']}, Items: {len(data['items'])}")
                generated_count += 1
                
        except Exception as e:
            current_app.logger.error(f"Failed to auto-generate PO for supplier {supplier_id}: {str(e)}")
            continue

    if generated_count > 0:
        flash(f'Successfully generated {generated_count} Draft Purchase Orders.', 'success')
    else:
        flash('No Purchase Orders were generated. Check if low stock items have preferred suppliers assigned.', 'warning')
        
    return redirect(url_for('purchase_orders.list_purchase_orders'))
