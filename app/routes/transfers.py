from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from db import query_db
from app.utils import log_audit_action, roles_required
import datetime

bp = Blueprint('transfers', __name__, url_prefix='/transfers')

@bp.route('/')
@login_required
def list_transfers():
    transfers_query = """
        SELECT 
            t.id, t.status, t.transfer_date,
            origin.name AS origin_location_name,
            dest.name AS destination_location_name,
            u.full_name AS initiator_name
        FROM stock_transfers t
        JOIN item_locations origin ON t.origin_location_id = origin.id
        JOIN item_locations dest ON t.destination_location_id = dest.id
        JOIN users u ON t.initiated_by_user_id = u.id
        ORDER BY t.created_at DESC;
    """
    transfers = query_db(transfers_query)
    return render_template('transfers/list_transfers.html', transfers=transfers)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_transfer():
    locations = query_db("SELECT id, name FROM item_locations ORDER BY name ASC")
    items_for_selection = query_db("SELECT id, name, sku, unit_of_measure FROM items WHERE is_active = TRUE ORDER BY name ASC")

    if request.method == 'POST':
        origin_location_id = request.form.get('origin_location_id', type=int)
        destination_location_id = request.form.get('destination_location_id', type=int)
        transfer_date_str = request.form.get('transfer_date')
        notes = request.form.get('notes')
        driver_details = request.form.get('driver_details')
        waybill_number = request.form.get('waybill_number')

        # Basic validation
        if not all([origin_location_id, destination_location_id, transfer_date_str]):
            flash('Origin, Destination, and Transfer Date are required.', 'danger')
        elif origin_location_id == destination_location_id:
            flash('Origin and Destination locations cannot be the same.', 'danger')
        else:
            try:
                transfer_date = datetime.datetime.strptime(transfer_date_str, '%Y-%m-%d').date()

                # Handle dynamic items
                transfer_items_data = []
                i = 0
                while True:
                    item_id = request.form.get(f'item_id_{i}')
                    quantity_sent = request.form.get(f'quantity_sent_{i}')
                    if item_id and quantity_sent:
                        try:
                            transfer_items_data.append({
                                'item_id': int(item_id),
                                'quantity_sent': float(quantity_sent),
                                'batch_number': request.form.get(f'batch_number_{i}', ''),
                                'expiry_date': request.form.get(f'expiry_date_{i}', '')
                            })
                        except ValueError:
                            flash('Invalid quantity for one or more items.', 'danger')
                            # Re-render form with data
                            return render_template('transfers/transfer_form.html', 
                                                   locations=locations, 
                                                   items_for_selection=items_for_selection, 
                                                   form_data=request.form, 
                                                   form_action="Initiate New")
                    elif i > 0 and not item_id and not quantity_sent: # Stop if no more items are found after the first
                        break
                    elif i == 0 and not item_id and not quantity_sent: # No items submitted at all
                        flash('At least one item must be added to the transfer.', 'danger')
                        return render_template('transfers/transfer_form.html', 
                                               locations=locations, 
                                               items_for_selection=items_for_selection, 
                                               form_data=request.form, 
                                               form_action="Initiate New")
                    i += 1
                
                if not transfer_items_data:
                    flash('At least one item must be added to the transfer.', 'danger')
                else:
                    # Insert into stock_transfers table
                    transfer_id = query_db("""
                        INSERT INTO stock_transfers 
                        (origin_location_id, destination_location_id, initiated_by_user_id, 
                         status, transfer_date, notes, driver_details, waybill_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        origin_location_id, destination_location_id, current_user.id, 
                        'Pending', transfer_date, notes, driver_details, waybill_number
                    ), commit=True, is_insert=True)

                    if transfer_id:
                        # Process each item for transfer
                        for item_data in transfer_items_data:
                            item_id = item_data['item_id']
                            quantity_to_send = item_data['quantity_sent']
                            
                            # FIFO Logic for transfer_out: Find batches at origin
                            batches_query = """
                                SELECT 
                                    batch_number, 
                                    expiry_date, 
                                    SUM(quantity_changed) as quantity_on_hand,
                                    MIN(movement_date) as first_entry_date
                                FROM stock_movements
                                WHERE item_id = %s AND location_id = %s
                                GROUP BY batch_number, expiry_date
                                HAVING quantity_on_hand > 0
                                ORDER BY expiry_date ASC, first_entry_date ASC;
                            """
                            available_batches = query_db(batches_query, (item_id, origin_location_id))

                            sent_so_far_for_item = 0
                            for batch in available_batches:
                                if sent_so_far_for_item >= quantity_to_send:
                                    break

                                quantity_from_this_batch = min(batch['quantity_on_hand'], quantity_to_send - sent_so_far_for_item)

                                # Create stock_movement for transfer_out
                                query_db("""
                                    INSERT INTO stock_movements 
                                    (item_id, location_id, quantity_changed, movement_type, movement_date, user_id, 
                                     batch_number, expiry_date, notes)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    item_id, origin_location_id, -quantity_from_this_batch, 'transfer_out', 
                                    datetime.datetime.now(), current_user.id, batch['batch_number'], batch['expiry_date'],
                                    f"Transfer Out for Transfer #{transfer_id}"
                                ), commit=True)

                                # Insert into stock_transfer_items
                                query_db("""
                                    INSERT INTO stock_transfer_items 
                                    (transfer_id, item_id, batch_number, expiry_date, quantity_sent)
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (
                                    transfer_id, item_id, batch['batch_number'], batch['expiry_date'], quantity_from_this_batch
                                ), commit=True)

                                sent_so_far_for_item += quantity_from_this_batch

                        log_audit_action(f"Initiated Stock Transfer ID: {transfer_id}", f"From {origin_location_id} to {destination_location_id}")
                        flash('Stock Transfer initiated successfully!', 'success')
                        return redirect(url_for('transfers.list_transfers')) # Redirect to list for now
                    else:
                        flash('Failed to create transfer record.', 'danger')

            except ValueError as ve:
                flash(f'Invalid date format or quantity: {str(ve)}', 'danger')
            except Exception as e:
                current_app.logger.error(f"Error creating transfer by {current_user.username}: {str(e)}")
                flash(f'Error initiating transfer: {str(e)}', 'danger')
        
        # If there was an error, re-render the form with current data
        return render_template('transfers/transfer_form.html', 
                               locations=locations, 
                               items_for_selection=items_for_selection, 
                               form_data=request.form, 
                               form_action="Initiate New")

    # GET request
    return render_template('transfers/transfer_form.html', 
                           locations=locations, 
                           items_for_selection=items_for_selection, 
                           form_action="Initiate New",
                           current_date=datetime.date.today().strftime('%Y-%m-%d'))

@bp.route('/<int:transfer_id>')
@login_required
def view_transfer(transfer_id):
    transfer_data = query_db("""
        SELECT 
            t.*,
            origin.name AS origin_location_name,
            dest.name AS destination_location_name,
            u.full_name AS initiator_name
        FROM stock_transfers t
        JOIN item_locations origin ON t.origin_location_id = origin.id
        JOIN item_locations dest ON t.destination_location_id = dest.id
        JOIN users u ON t.initiated_by_user_id = u.id
        WHERE t.id = %s
    """, (transfer_id,), one=True)

    if not transfer_data:
        flash('Stock Transfer not found.', 'danger')
        return redirect(url_for('transfers.list_transfers'))

    # Security check: Only initiator, or users at origin/destination, or admin/manager can view
    can_view = False
    if current_user.role in ['admin', 'manager']:
        can_view = True
    elif current_user.id == transfer_data['initiated_by_user_id']:
        can_view = True
    # Assuming user has a department_id linked to a location, or direct location access
    # This part might need more sophisticated logic based on how users are linked to locations
    # For now, a simple check if user's department is linked to origin/destination location
    # (This requires department_id in users table to be linked to item_locations somehow, or a direct user-location mapping)
    # For simplicity, let's assume if user is manager/admin or initiator, they can view.
    # A more robust check would involve checking if current_user.location_id (if exists) matches origin/destination.
    
    if not can_view:
        flash('You do not have permission to view this transfer.', 'danger')
        abort(403)

    items_data = query_db("""
        SELECT 
            sti.*,
            i.name AS item_name,
            i.sku AS item_sku,
            i.unit_of_measure AS item_unit
        FROM stock_transfer_items sti
        JOIN items i ON sti.item_id = i.id
        WHERE sti.transfer_id = %s
    """, (transfer_id,))

    return render_template('transfers/view_transfer.html', 
                           transfer=transfer_data, 
                           items=items_data)

@bp.route('/<int:transfer_id>/receive', methods=['POST'])
@login_required
@roles_required(['admin', 'manager'])
def receive_transfer(transfer_id):
    transfer = query_db("SELECT * FROM stock_transfers WHERE id = %s", (transfer_id,), one=True)

    if not transfer:
        flash('Stock Transfer not found.', 'danger')
        return redirect(url_for('transfers.list_transfers'))

    if transfer['status'] == 'Completed':
        flash('This transfer has already been completed.', 'warning')
        return redirect(url_for('transfers.view_transfer', transfer_id=transfer_id))
    
    if transfer['status'] == 'Cancelled':
        flash('This transfer has been cancelled and cannot be received.', 'warning')
        return redirect(url_for('transfers.view_transfer', transfer_id=transfer_id))

    # Security check: Only admin/manager or user at destination can receive
    # For simplicity, assuming admin/manager can receive any. 
    # A more robust check would involve linking current_user to a location.
    # For now, roles_required handles it.

    try:
        # Update transfer status to Completed
        query_db("""
            UPDATE stock_transfers 
            SET status = %s, completed_by_user_id = %s, completion_date = %s
            WHERE id = %s
        """, ('Completed', current_user.id, datetime.datetime.now(), transfer_id), commit=True)

        # Get all items associated with this transfer
        transfer_items = query_db("SELECT * FROM stock_transfer_items WHERE transfer_id = %s", (transfer_id,))

        for item in transfer_items:
            # Create stock_movement for transfer_in at destination
            query_db("""
                INSERT INTO stock_movements 
                (item_id, location_id, quantity_changed, movement_type, movement_date, user_id, 
                 batch_number, expiry_date, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                item['item_id'], transfer['destination_location_id'], item['quantity_sent'], 'transfer_in', 
                datetime.datetime.now(), current_user.id, item['batch_number'], item['expiry_date'],
                f"Transfer In for Transfer #{transfer_id}"
            ), commit=True)

            # Update quantity_received in stock_transfer_items (assuming full receipt)
            query_db("""
                UPDATE stock_transfer_items SET quantity_received = %s WHERE id = %s
            """, (item['quantity_sent'], item['id']), commit=True)

        log_audit_action(f"Stock Transfer Received: ID {transfer_id}", f"Received by {current_user.username} at {transfer['destination_location_id']}")
        flash(f'Stock Transfer #{transfer_id} successfully marked as received and stock updated.', 'success')

    except Exception as e:
        current_app.logger.error(f"Error receiving transfer {transfer_id} by {current_user.username}: {str(e)}")
        flash(f'Error receiving transfer: {str(e)}', 'danger')

    return redirect(url_for('transfers.view_transfer', transfer_id=transfer_id))
