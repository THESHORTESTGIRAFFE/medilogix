from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from db import query_db
from app.utils import log_audit_action, get_current_stock
import datetime

bp = Blueprint('stock', __name__, url_prefix='/stock')

MOVEMENT_TYPES = [
    'initial_stock', 'receipt', 'issuance', 
    'adjustment_in', 'adjustment_out', 
    'transfer_out', 'transfer_in', 'disposal'
]

@bp.route('/movements/add', methods=['GET', 'POST'])
@login_required
def add_stock_movement():
    items = query_db("SELECT id, name, sku FROM items WHERE is_active = TRUE ORDER BY name ASC")
    locations = query_db("SELECT id, name FROM item_locations ORDER BY name ASC")

    if request.method == 'POST':
        item_id = request.form.get('item_id', type=int)
        location_id = request.form.get('location_id', type=int)
        quantity_str = request.form.get('quantity_changed')
        movement_type = request.form.get('movement_type')
        movement_date_str = request.form.get('movement_date') # Expected format: YYYY-MM-DDTHH:MM
        batch_number = request.form.get('batch_number')
        expiry_date_str = request.form.get('expiry_date')
        cost_per_unit_str = request.form.get('cost_per_unit')
        notes = request.form.get('notes')

        # Validations
        if not all([item_id, location_id, quantity_str, movement_type, movement_date_str]):
            flash('Item, Location, Quantity, Movement Type, and Movement Date are required.', 'danger')
        elif movement_type not in MOVEMENT_TYPES:
            flash('Invalid movement type selected.', 'danger')
        else:
            try:
                quantity_changed = float(quantity_str)
                movement_date = datetime.datetime.strptime(movement_date_str, '%Y-%m-%dT%H:%M')
                
                expiry_date = None
                if expiry_date_str:
                    expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                
                cost_per_unit = None
                if cost_per_unit_str:
                    cost_per_unit = float(cost_per_unit_str)

                # For issuances, transfers_out, adjustments_out, disposal, quantity should be negative
                if movement_type in ['issuance', 'transfer_out', 'adjustment_out', 'disposal']:
                    if quantity_changed > 0:
                        quantity_changed = -quantity_changed # Ensure it's negative
                elif quantity_changed < 0: # For receipts, etc., ensure positive
                        flash('Quantity for this movement type should be positive.', 'warning')
                        quantity_changed = abs(quantity_changed)

                query_db("""
                    INSERT INTO stock_movements 
                    (item_id, location_id, quantity_changed, movement_type, movement_date, user_id, 
                     batch_number, expiry_date, cost_per_unit, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (item_id, location_id, quantity_changed, movement_type, movement_date, current_user.id,
                      batch_number if batch_number else None, 
                      expiry_date, 
                      cost_per_unit, 
                      notes if notes else None), commit=True)
                
                item_name = query_db("SELECT name FROM items WHERE id = %s", (item_id,), one=True)['name']
                log_audit_action(f"Stock Movement: {movement_type}", f"Item: {item_name} (ID: {item_id}), Qty: {quantity_changed}, Loc ID: {location_id}")
                flash(f'Stock movement ({movement_type}) for "{item_name}" recorded successfully!', 'success')
                return redirect(url_for('inventory.view_item', item_id=item_id)) # Redirect to item view to see changes

            except ValueError as ve:
                flash(f'Invalid data format: {str(ve)}', 'danger')
            except Exception as e:
                current_app.logger.error(f"Error adding stock movement by {current_user.username}: {str(e)}")
                flash(f'Error recording stock movement: {str(e)}', 'danger')
        
        return render_template('stock/stock_movement_form.html', items=items, locations=locations, movement_types=MOVEMENT_TYPES, form_data=request.form, form_action="Add New")

    return render_template('stock/stock_movement_form.html', items=items, locations=locations, movement_types=MOVEMENT_TYPES, form_action="Add New", current_datetime=datetime.datetime.now().strftime('%Y-%m-%dT%H:%M'))

@bp.route('/movements')
@login_required
def list_stock_movements():
    # Add search/filtering/pagination later
    movements_data = query_db("""
        SELECT 
            sm.id,
            sm.item_id, -- Add item_id here
            i.name as item_name,
            i.sku as item_sku,
            il.name as location_name,
            sm.quantity_changed,
            sm.movement_type,
            sm.movement_date,
            u.username as user_username,
            sm.batch_number,
            sm.expiry_date,
            sm.cost_per_unit,
            sm.notes
        FROM stock_movements sm
        JOIN items i ON sm.item_id = i.id
        JOIN item_locations il ON sm.location_id = il.id
        JOIN users u ON sm.user_id = u.id
        ORDER BY sm.movement_date DESC
    """)
    return render_template('stock/list_movements.html', movements=movements_data, title="All Stock Movements")