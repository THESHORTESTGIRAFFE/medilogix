from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from db import query_db
from app.utils import log_audit_action, get_current_stock, calculate_hash
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
        movement_type = request.form.get('movement_type')
        movement_date_str = request.form.get('movement_date') # Expected format: YYYY-MM-DDTHH:MM
        notes = request.form.get('notes')

        # --- Parse multiple batches ---
        batches = []
        batch_keys = [key for key in request.form.keys() if key.startswith('batches[')]
        if not batch_keys:
            flash('No batch information was submitted. Please add at least one batch.', 'danger')
            return redirect(request.url)

        num_batches = max([int(key.split('[')[1].split(']')[0]) for key in batch_keys]) + 1

        for i in range(num_batches):
            quantity_str = request.form.get(f'batches[{i}][quantity]')
            batch_number = request.form.get(f'batches[{i}][batch_number]')
            expiry_date_str = request.form.get(f'batches[{i}][expiry_date]')
            cost_per_unit_str = request.form.get(f'batches[{i}][cost_per_unit]')

            if quantity_str: # Process only if quantity is present
                batches.append({
                    'quantity': quantity_str,
                    'batch_number': batch_number,
                    'expiry_date': expiry_date_str,
                    'cost_per_unit': cost_per_unit_str,
                })

        # Validations
        if not all([item_id, location_id, movement_type, movement_date_str]):
            flash('Item, Location, Movement Type, and Movement Date are required.', 'danger')
        elif not batches:
            flash('At least one batch with a quantity is required.', 'danger')
        elif movement_type not in MOVEMENT_TYPES:
            flash('Invalid movement type selected.', 'danger')
        else:
            try:
                movement_date = datetime.datetime.strptime(movement_date_str, '%Y-%m-%dT%H:%M')
                
                total_quantity_processed = 0

                for batch in batches:
                    quantity_changed = float(batch['quantity'])
                    
                    expiry_date = None
                    if batch['expiry_date']:
                        expiry_date = datetime.datetime.strptime(batch['expiry_date'], '%Y-%m-%d').date()
                    
                    cost_per_unit = None
                    if batch['cost_per_unit']:
                        cost_per_unit = float(batch['cost_per_unit'])

                    # For issuances, transfers_out, adjustments_out, disposal, quantity should be negative
                    if movement_type in ['issuance', 'transfer_out', 'adjustment_out', 'disposal']:
                        if quantity_changed > 0:
                            quantity_changed = -quantity_changed # Ensure it's negative
                    elif quantity_changed < 0: # For receipts, etc., ensure positive
                            flash('Quantity for this movement type should be positive.', 'warning')
                            quantity_changed = abs(quantity_changed)

                    # --- Blockchain Audit Trail ---
                    previous_hash_record = query_db("SELECT last_hash FROM audit_chain_metadata WHERE record_type = %s", ('stock_movement',), one=True)
                    previous_hash = previous_hash_record['last_hash'] if previous_hash_record else None

                    # Insert the record and get its ID
                    new_movement_id = query_db("""
                        INSERT INTO stock_movements 
                        (item_id, location_id, quantity_changed, movement_type, movement_date, user_id, 
                         batch_number, expiry_date, cost_per_unit, notes, previous_hash)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """, (item_id, location_id, quantity_changed, movement_type, movement_date, current_user.id,
                          batch['batch_number'] if batch['batch_number'] else None, 
                          expiry_date, 
                          cost_per_unit, 
                          notes if notes else None,
                          previous_hash), commit=True, one=True)['id']

                    # Now, calculate the hash of the full record
                    record_data = {
                        'id': new_movement_id,
                        'item_id': item_id,
                        'location_id': location_id,
                        'quantity_changed': quantity_changed,
                        'movement_type': movement_type,
                        'movement_date': movement_date,
                        'user_id': current_user.id,
                        'batch_number': batch['batch_number'],
                        'expiry_date': expiry_date,
                        'cost_per_unit': cost_per_unit,
                        'notes': notes,
                        'previous_hash': previous_hash
                    }
                    current_hash = calculate_hash(record_data)

                    # Update the record with its own hash
                    query_db("UPDATE stock_movements SET hash = %s WHERE id = %s", (current_hash, new_movement_id), commit=True)

                    # Update the metadata table with the new hash
                    query_db("""
                        INSERT INTO audit_chain_metadata (record_type, last_hash) 
                        VALUES (%s, %s) 
                        ON DUPLICATE KEY UPDATE last_hash = VALUES(last_hash)
                    """, ('stock_movement', current_hash), commit=True)
                    # --- End Blockchain Audit Trail ---
                    
                    total_quantity_processed += quantity_changed

                item_name = query_db("SELECT name FROM items WHERE id = %s", (item_id,), one=True)['name']
                log_audit_action(f"Stock Movement: {movement_type}", f"Item: {item_name} (ID: {item_id}), Total Qty: {total_quantity_processed} across {len(batches)} batches, Loc ID: {location_id}")
                flash(f'Stock movement ({movement_type}) for "{item_name}" recorded successfully for {len(batches)} batches!', 'success')
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

@bp.route('/items/<int:item_id>/batches')
@login_required
def get_item_batches(item_id):
    """
    Returns available batches for a given item, sorted by expiry date (FIFO).
    This is intended for an AJAX call.
    """
    # This query calculates the current stock for each batch
    sql = """
        SELECT 
            sm.batch_number, 
            sm.expiry_date, 
            SUM(sm.quantity_changed) as batch_stock
        FROM stock_movements sm
        WHERE sm.item_id = %s
        GROUP BY sm.batch_number, sm.expiry_date
        HAVING batch_stock > 0
        ORDER BY sm.expiry_date ASC, sm.batch_number ASC;
    """
    try:
        batches = query_db(sql, (item_id,))
        return jsonify(batches)
    except Exception as e:
        current_app.logger.error(f"Error fetching batches for item {item_id}: {str(e)}")
        return jsonify({'error': 'Could not fetch batch data.'}), 500