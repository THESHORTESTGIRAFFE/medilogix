from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from db import query_db
from app.utils import log_audit_action, roles_required
from app.models import PurchaseOrder # Import the PurchaseOrder model
import datetime

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
                    po_id = query_db("""
                        INSERT INTO purchase_orders 
                        (supplier_id, order_date, expected_delivery_date, total_amount, notes, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        supplier_id, order_date, expected_delivery_date, total_amount, notes, 'Draft'
                    ), commit=True, is_insert=True)

                    if po_id:
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
                            total_amount = %s, notes = %s, status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        supplier_id, order_date, expected_delivery_date, 
                        total_amount, notes, status, po_id
                    ), commit=True)

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

    return render_template('purchase_orders/view_purchase_order.html', 
                           purchase_order=po_data, 
                           po_items=po_items_data)
