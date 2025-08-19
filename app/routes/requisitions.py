from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort, Response
from flask_login import login_required, current_user
from db import query_db
from app.utils import log_audit_action, roles_required # Import roles_required
import datetime
from weasyprint import HTML # For PDF generation

bp = Blueprint('requisitions', __name__, url_prefix='/requisitions')

REQUISITION_STATUSES = ['Pending', 'Approved', 'Rejected', 'Partially Fulfilled', 'Fulfilled', 'Cancelled']

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_requisition():
    items_for_selection = query_db("SELECT id, name, sku, unit_of_measure FROM items WHERE is_active = TRUE ORDER BY name ASC")

    # Fetch department name for the current user
    current_user_department_name = "N/A"
    if hasattr(current_user, 'department_id') and current_user.department_id:
        department_data = query_db("SELECT name FROM departments WHERE id = %s", (current_user.department_id,), one=True)
        if department_data:
            current_user_department_name = department_data['name']


    if request.method == 'POST':
        required_by_date_str = request.form.get('required_by_date')
        notes = request.form.get('notes')
        
        # Item details are expected as: item_id_X, quantity_X, item_notes_X
        requested_items = []
        i = 0
        while True:
            item_id = request.form.get(f'item_id_{i}')
            quantity = request.form.get(f'quantity_{i}')
            if item_id and quantity:
                try:
                    requested_items.append({
                        'item_id': int(item_id),
                        'quantity_requested': float(quantity),
                        'notes': request.form.get(f'item_notes_{i}', '')
                    })
                except ValueError:
                    flash('Invalid quantity for one or more items.', 'danger')
                    return render_template('requisitions/requisition_form.html', 
                                           items_for_selection=items_for_selection, 
                                           form_action="Create New", 
                                           form_data=request.form, # Persist form data
                                           current_user_department_name=current_user_department_name)
            elif i > 0 and not item_id and not quantity: # Stop if no more items are found after the first
                break
            elif i == 0 and not item_id and not quantity: # No items submitted at all
                flash('At least one item must be requested.', 'danger')
                return render_template('requisitions/requisition_form.html', 
                                       items_for_selection=items_for_selection, 
                                       form_action="Create New", 
                                       form_data=request.form,
                                       current_user_department_name=current_user_department_name)
            i += 1

        if not requested_items:
            flash('No items were added to the requisition.', 'danger')
        else:
            try:
                required_by_date = None
                if required_by_date_str:
                    required_by_date = datetime.datetime.strptime(required_by_date_str, '%Y-%m-%d').date()

                # Insert into requisitions table
                requisition_id = query_db("""
                    INSERT INTO requisitions (requester_id, department_id, required_by_date, notes, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (current_user.id, current_user.department_id, required_by_date, notes, 'Pending'), 
                commit=True, is_insert=True)

                if requisition_id:
                    # Insert into requisition_items table
                    for item_data in requested_items:
                        query_db("""
                            INSERT INTO requisition_items (requisition_id, item_id, quantity_requested, notes)
                            VALUES (%s, %s, %s, %s)
                        """, (requisition_id, item_data['item_id'], item_data['quantity_requested'], item_data['notes']),
                        commit=True) # Commit each item or batch commit after loop
                    
                    log_audit_action(f"Created Requisition ID: {requisition_id}")
                    flash('Requisition submitted successfully!', 'success')
                    return redirect(url_for('requisitions.view_requisition', requisition_id=requisition_id))
                else:
                    flash('Failed to create requisition header.', 'danger')

            except ValueError as ve:
                flash(f'Invalid date format: {str(ve)}', 'danger')
            except Exception as e:
                current_app.logger.error(f"Error creating requisition by {current_user.username}: {str(e)}")
                flash(f'Error creating requisition: {str(e)}', 'danger')
        
        return render_template('requisitions/requisition_form.html', 
                               items_for_selection=items_for_selection, 
                               form_action="Create New", 
                               current_user_department_name=current_user_department_name,
                               form_data=request.form, # Persist form data on error
                               requested_items_data=requested_items) # Persist dynamic rows

    return render_template('requisitions/requisition_form.html', 
                           items_for_selection=items_for_selection, 
                           form_action="Create New",
                           current_user_department_name=current_user_department_name)


@bp.route('/')
@login_required
def list_my_requisitions():
    # Shows requisitions created by the current user
    requisitions_data = query_db("""
        SELECT r.*, u.full_name as requester_name, d.name as department_name
        FROM requisitions r
        JOIN users u ON r.requester_id = u.id
        LEFT JOIN departments d ON r.department_id = d.id
        WHERE r.requester_id = %s
        ORDER BY r.request_date DESC
    """, (current_user.id,))
    return render_template('requisitions/list_requisitions.html', requisitions=requisitions_data, title="My Requisitions")

@bp.route('/all')
@login_required
def list_all_requisitions():
    # For managers/admins - add role check later
    if current_user.role not in ['admin', 'manager']:
        abort(403) # Forbidden

    requisitions_data = query_db("""
        SELECT r.*, u.full_name as requester_name, d.name as department_name
        FROM requisitions r
        JOIN users u ON r.requester_id = u.id
        LEFT JOIN departments d ON r.department_id = d.id
        ORDER BY r.request_date DESC
    """)
    return render_template('requisitions/list_requisitions.html', requisitions=requisitions_data, title="All Requisitions")

@bp.route('/<int:requisition_id>')
@login_required
def view_requisition(requisition_id):
    requisition_data = query_db("""
        SELECT r.*, 
               req_user.full_name as requester_name, 
               req_user.username as requester_username,
               dept.name as department_name,
               app_user.full_name as approver_name
        FROM requisitions r
        JOIN users req_user ON r.requester_id = req_user.id
        LEFT JOIN departments dept ON r.department_id = dept.id
        LEFT JOIN users app_user ON r.approved_by_id = app_user.id
        WHERE r.id = %s
    """, (requisition_id,), one=True)

    if not requisition_data:
        flash('Requisition not found.', 'danger')
        return redirect(url_for('requisitions.list_my_requisitions'))

    # Security check: User can view their own, or admin/manager can view any.
    if requisition_data['requester_id'] != current_user.id and current_user.role not in ['admin', 'manager']:
        abort(403) # Forbidden

    items_data = query_db("""
        SELECT ri.*, i.name as item_name, i.sku as item_sku, i.unit_of_measure as item_unit
        FROM requisition_items ri
        JOIN items i ON ri.item_id = i.id
        WHERE ri.requisition_id = %s
        ORDER BY i.name
    """, (requisition_id,))

    # Fetch locations for the fulfillment form
    locations = []
    if requisition_data['status'] in ['Approved', 'Partially Fulfilled'] and current_user.role in ['admin', 'manager']:
        locations = query_db("SELECT id, name FROM item_locations ORDER BY name ASC")

    return render_template('requisitions/view_requisition.html', 
                           requisition=requisition_data, 
                           items=items_data,
                           locations=locations) # Pass locations to template

@bp.route('/<int:requisition_id>/print')
@login_required
def print_requisition_form(requisition_id):
    requisition_data = query_db("""
        SELECT r.*, 
               req_user.full_name as requester_name, 
               req_user.username as requester_username,
               dept.name as department_name,
               app_user.full_name as approver_name
        FROM requisitions r
        JOIN users req_user ON r.requester_id = req_user.id
        LEFT JOIN departments dept ON r.department_id = dept.id
        LEFT JOIN users app_user ON r.approved_by_id = app_user.id
        WHERE r.id = %s
    """, (requisition_id,), one=True)

    if not requisition_data:
        flash('Requisition not found.', 'danger')
        return redirect(url_for('requisitions.list_my_requisitions'))

    if requisition_data['requester_id'] != current_user.id and current_user.role not in ['admin', 'manager']:
        abort(403)

    items_data = query_db("""
        SELECT ri.*, i.name as item_name, i.sku as item_sku, i.unit_of_measure as item_unit
        FROM requisition_items ri
        JOIN items i ON ri.item_id = i.id
        WHERE ri.requisition_id = %s ORDER BY i.name
    """, (requisition_id,))

    generation_time = datetime.datetime.now()
    html_out = render_template('requisitions/requisition_print_form.html', 
                               requisition=requisition_data, items=items_data, generation_time=generation_time)
    pdf_bytes = HTML(string=html_out, base_url=request.url_root).write_pdf()

    return Response(pdf_bytes, mimetype="application/pdf", headers={"Content-Disposition": f"attachment;filename=requisition_form_{requisition_id}_{generation_time.strftime('%Y%m%d')}.pdf"})

@bp.route('/<int:requisition_id>/process', methods=['POST'])
@login_required
@roles_required(['admin', 'manager'])
def process_requisition_approval(requisition_id):
    requisition = query_db("SELECT * FROM requisitions WHERE id = %s", (requisition_id,), one=True)
    if not requisition:
        flash('Requisition not found.', 'danger')
        return redirect(url_for('requisitions.list_all_requisitions'))

    if requisition['status'] != 'Pending':
        flash(f"Requisition #{requisition_id} is no longer pending and cannot be processed further.", 'warning')
        return redirect(url_for('requisitions.view_requisition', requisition_id=requisition_id))

    action = request.form.get('action')
    rejection_reason = request.form.get('rejection_reason', '').strip()
    processed_by_id = current_user.id
    processed_date = datetime.datetime.now()

    if action == 'approve':
        new_status = 'Approved'
        # Clear rejection reason if it was somehow set
        query_db("""
            UPDATE requisitions 
            SET status = %s, approved_by_id = %s, approval_date = %s, rejection_reason = NULL
            WHERE id = %s
        """, (new_status, processed_by_id, processed_date, requisition_id), commit=True)
        log_audit_action(f"Requisition Approved: ID {requisition_id}", f"Approved by {current_user.username}")
        flash(f'Requisition #{requisition_id} has been approved.', 'success')

    elif action == 'reject':
        if not rejection_reason:
            flash('Rejection reason is required when rejecting a requisition.', 'danger')
            return redirect(url_for('requisitions.view_requisition', requisition_id=requisition_id))
        new_status = 'Rejected'
        query_db("""
            UPDATE requisitions 
            SET status = %s, approved_by_id = %s, approval_date = %s, rejection_reason = %s
            WHERE id = %s
        """, (new_status, processed_by_id, processed_date, rejection_reason, requisition_id), commit=True)
        log_audit_action(f"Requisition Rejected: ID {requisition_id}", f"Rejected by {current_user.username}. Reason: {rejection_reason}")
        flash(f'Requisition #{requisition_id} has been rejected.', 'success') # Or 'info'

    else:
        flash('Invalid action specified.', 'danger')

    return redirect(url_for('requisitions.view_requisition', requisition_id=requisition_id))

@bp.route('/<int:requisition_id>/fulfill', methods=['POST'])
@login_required
@roles_required(['admin', 'manager'])
def fulfill_requisition(requisition_id):
    location_id = request.form.get('location_id', type=int)

    if not location_id:
        flash('You must select a location to issue stock from.', 'danger')
        return redirect(url_for('requisitions.view_requisition', requisition_id=requisition_id))

    requisition = query_db("SELECT * FROM requisitions WHERE id = %s", (requisition_id,), one=True)
    if not requisition or requisition['status'] not in ['Approved', 'Partially Fulfilled']:
        flash('This requisition cannot be fulfilled at this time.', 'warning')
        return redirect(url_for('requisitions.view_requisition', requisition_id=requisition_id))

    requested_items = query_db("SELECT * FROM requisition_items WHERE requisition_id = %s", (requisition_id,))
    
    total_items_to_fulfill = len(requested_items)
    items_fully_fulfilled = 0
    fulfillment_details = []

    for item in requested_items:
        quantity_to_issue = item['quantity_requested'] - item['quantity_issued']
        if quantity_to_issue <= 0:
            items_fully_fulfilled += 1
            continue

        # FIFO Logic: Get available batches for the item at the specified location, ordered by expiry date, then by entry date.
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
        available_batches = query_db(batches_query, (item['item_id'], location_id))

        if not available_batches:
            item_name = query_db("SELECT name FROM items WHERE id = %s", (item['item_id'],), one=True)['name']
            fulfillment_details.append(f"Item '{item_name}': Out of stock at the selected location.")
            continue

        issued_so_far_for_item = 0
        for batch in available_batches:
            if issued_so_far_for_item >= quantity_to_issue:
                break

            quantity_from_this_batch = min(batch['quantity_on_hand'], quantity_to_issue - issued_so_far_for_item)

            # Create the negative stock movement (issuance)
            query_db("""
                INSERT INTO stock_movements 
                (item_id, location_id, quantity_changed, movement_type, movement_date, user_id, 
                 batch_number, expiry_date, related_requisition_id, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                item['item_id'], location_id, -quantity_from_this_batch, 'issuance', 
                datetime.datetime.now(), current_user.id, batch['batch_number'], batch['expiry_date'],
                requisition_id, f"Fulfillment for Requisition #{requisition_id}"
            ), commit=True)

            issued_so_far_for_item += quantity_from_this_batch
        
        # Update the quantity_issued in requisition_items
        if issued_so_far_for_item > 0:
            query_db("""
                UPDATE requisition_items SET quantity_issued = quantity_issued + %s WHERE id = %s
            """, (issued_so_far_for_item, item['id']), commit=True)

        item_name = query_db("SELECT name FROM items WHERE id = %s", (item['item_id'],), one=True)['name']
        if issued_so_far_for_item < quantity_to_issue:
            fulfillment_details.append(f"Item '{item_name}': Partially issued {issued_so_far_for_item}/{quantity_to_issue}. Stock depleted.")
        else:
            fulfillment_details.append(f"Item '{item_name}': Fully issued ({issued_so_far_for_item}).")
            items_fully_fulfilled += 1

    # Update overall requisition status
    final_status = requisition['status']
    if items_fully_fulfilled == total_items_to_fulfill:
        final_status = 'Fulfilled'
    elif items_fully_fulfilled > 0 or any(fi.startswith("Partially") for fi in fulfillment_details):
        final_status = 'Partially Fulfilled'

    if final_status != requisition['status']:
        query_db("UPDATE requisitions SET status = %s WHERE id = %s", (final_status, requisition_id), commit=True)

    flash("Fulfillment process complete. See details below:", 'info')
    for detail in fulfillment_details:
        flash(detail, 'secondary')

    log_audit_action(f"Requisition Fulfillment Attempted: ID {requisition_id}", f"Status: {final_status}. Details: {'; '.join(fulfillment_details)}")
    return redirect(url_for('requisitions.view_requisition', requisition_id=requisition_id))
