from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from db import query_db
from app.models import TrackedAsset
from app.utils import log_audit_action, roles_required, utility_flash_messages_contain_category
import datetime

bp = Blueprint('assets', __name__, url_prefix='/assets')

ASSET_STATUSES = ['Available', 'Allocated', 'In Repair', 'Disposed', 'Missing']

@bp.route('/')
@login_required
@roles_required(['admin', 'manager'])
def list_tracked_assets():
    search_term = request.args.get('search', '').strip()
    query_params = []

    base_sql = """
        SELECT 
            ta.*, 
            i.name as item_name,
            u.full_name as assigned_user_name
        FROM tracked_assets ta
        JOIN items i ON ta.item_id = i.id
        LEFT JOIN users u ON ta.assigned_to_user_id = u.id
    """

    where_conditions = []
    if search_term:
        like_term = f"%{search_term}%"
        # Searchable fields: Item Name (i.name), Serial Number (ta.serial_number), 
        # Status (ta.status), Assigned To (u.full_name), Office/Location (ta.office_details)
        where_conditions.append("(i.name LIKE %s OR ta.serial_number LIKE %s OR ta.status LIKE %s OR u.full_name LIKE %s OR ta.office_details LIKE %s)")
        query_params.extend([like_term] * 5)

    final_sql = base_sql
    if where_conditions:
        final_sql += " WHERE " + " AND ".join(where_conditions)
    
    final_sql += " ORDER BY i.name ASC, ta.serial_number ASC"

    assets_data = query_db(final_sql, tuple(query_params))
    
    return render_template('assets/list_tracked_assets.html', 
                           assets=assets_data, 
                           title="Tracked Assets", 
                           search_term=search_term)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required(['admin', 'manager'])
def add_tracked_asset():
    items = query_db("SELECT id, name FROM items WHERE is_active = TRUE ORDER BY name ASC") # Assuming only active items can be assets
    users = query_db("SELECT id, full_name, username FROM users WHERE is_active = TRUE ORDER BY full_name ASC")

    if request.method == 'POST':
        item_id = request.form.get('item_id', type=int)
        serial_number = request.form.get('serial_number', '').strip()
        status = request.form.get('status')
        assigned_to_user_id_str = request.form.get('assigned_to_user_id')
        office_details = request.form.get('office_details', '').strip()
        purchase_date_str = request.form.get('purchase_date')
        warranty_expiry_date_str = request.form.get('warranty_expiry_date')
        notes = request.form.get('notes', '').strip()

        if not all([item_id, serial_number, status]):
            flash('Item, Serial Number, and Status are required.', 'danger')
        elif status not in ASSET_STATUSES:
            flash('Invalid asset status selected.', 'danger')
        else:
            # Check for duplicate serial number for the same item
            existing_asset = query_db("SELECT id FROM tracked_assets WHERE item_id = %s AND serial_number = %s", (item_id, serial_number), one=True)
            if existing_asset:
                flash(f'An asset for this item with serial number "{serial_number}" already exists.', 'warning')
            else:
                try:
                    assigned_to_user_id = int(assigned_to_user_id_str) if assigned_to_user_id_str else None
                    purchase_date = datetime.datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else None
                    warranty_expiry_date = datetime.datetime.strptime(warranty_expiry_date_str, '%Y-%m-%d').date() if warranty_expiry_date_str else None
                    allocation_date = datetime.datetime.now() if status == 'Allocated' and assigned_to_user_id else None

                    if status == 'Allocated' and not assigned_to_user_id:
                        flash('Assigned user is required if status is "Allocated".', 'warning')
                    elif status != 'Allocated':
                        assigned_to_user_id = None # Ensure user is not set if not allocated
                        office_details = None      # Ensure office is not set if not allocated
                        allocation_date = None

                    if not utility_flash_messages_contain_category('danger', req=request): # Proceed if no new flash errors
                        asset_id = query_db("""
                            INSERT INTO tracked_assets 
                            (item_id, serial_number, status, assigned_to_user_id, office_details, 
                             allocation_date, purchase_date, warranty_expiry_date, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (item_id, serial_number, status, assigned_to_user_id, office_details if status == 'Allocated' else None, 
                              allocation_date, purchase_date, warranty_expiry_date, notes),
                        commit=True, is_insert=True)

                        log_audit_action('Tracked Asset Added', f"Asset SN: '{serial_number}' for item ID {item_id} added by {current_user.username}. Status: {status}.")
                        flash(f'Tracked asset "{serial_number}" added successfully!', 'success')
                        return redirect(url_for('assets.list_tracked_assets'))

                except ValueError as ve:
                    flash(f'Invalid data format: {str(ve)}', 'danger')
                except Exception as e:
                    current_app.logger.error(f"Error adding tracked asset by {current_user.username}: {str(e)}")
                    flash(f'Error adding tracked asset: {str(e)}', 'danger')
        
        return render_template('assets/asset_form.html', form_action="Add New", items=items, users=users, statuses=ASSET_STATUSES, form_data=request.form)

    return render_template('assets/asset_form.html', form_action="Add New", items=items, users=users, statuses=ASSET_STATUSES)

@bp.route('/<int:asset_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required(['admin', 'manager'])
def edit_tracked_asset(asset_id):
    asset_data = query_db("SELECT * FROM tracked_assets WHERE id = %s", (asset_id,), one=True)
    if not asset_data:
        flash('Tracked asset not found.', 'danger')
        return redirect(url_for('assets.list_tracked_assets'))

    items = query_db("SELECT id, name FROM items WHERE is_active = TRUE ORDER BY name ASC")
    users = query_db("SELECT id, full_name, username FROM users WHERE is_active = TRUE ORDER BY full_name ASC")

    if request.method == 'POST':
        # item_id cannot be changed easily due to serial number uniqueness context.
        # serial_number change might be complex if it's a key identifier. For now, assume it's editable with care.
        serial_number = request.form.get('serial_number', '').strip()
        status = request.form.get('status')
        assigned_to_user_id_str = request.form.get('assigned_to_user_id')
        office_details = request.form.get('office_details', '').strip()
        purchase_date_str = request.form.get('purchase_date')
        warranty_expiry_date_str = request.form.get('warranty_expiry_date')
        notes = request.form.get('notes', '').strip()

        if not all([serial_number, status]): # item_id is fixed from GET
            flash('Serial Number and Status are required.', 'danger')
        elif status not in ASSET_STATUSES:
            flash('Invalid asset status selected.', 'danger')
        else:
            # Check for duplicate serial number if it changed
            if serial_number != asset_data['serial_number']:
                existing_asset = query_db("SELECT id FROM tracked_assets WHERE item_id = %s AND serial_number = %s AND id != %s", 
                                          (asset_data['item_id'], serial_number, asset_id), one=True)
                if existing_asset:
                    flash(f'Another asset for this item with serial number "{serial_number}" already exists.', 'warning')
            
            if not utility_flash_messages_contain_category('danger', req=request):
                try:
                    assigned_to_user_id = int(assigned_to_user_id_str) if assigned_to_user_id_str else None
                    purchase_date = datetime.datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else None
                    warranty_expiry_date = datetime.datetime.strptime(warranty_expiry_date_str, '%Y-%m-%d').date() if warranty_expiry_date_str else None
                    
                    allocation_date_to_set = asset_data['allocation_date'] # Preserve old one unless status changes

                    if status == 'Allocated' and not assigned_to_user_id:
                        flash('Assigned user is required if status is "Allocated".', 'warning')
                    elif status == 'Allocated' and (assigned_to_user_id != asset_data['assigned_to_user_id'] or status != asset_data['status']):
                        allocation_date_to_set = datetime.datetime.now() # Update allocation date if user changes or status becomes allocated
                    elif status != 'Allocated':
                        assigned_to_user_id = None
                        office_details = None
                        allocation_date_to_set = None # Clear allocation date if not allocated

                    if not utility_flash_messages_contain_category('danger', req=request):
                        query_db("""
                            UPDATE tracked_assets SET
                            serial_number = %s, status = %s, assigned_to_user_id = %s, office_details = %s,
                            allocation_date = %s, purchase_date = %s, warranty_expiry_date = %s, notes = %s,
                            updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (serial_number, status, assigned_to_user_id, office_details if status == 'Allocated' else None, 
                              allocation_date_to_set, purchase_date, warranty_expiry_date, notes, asset_id),
                        commit=True)

                        log_audit_action('Tracked Asset Updated', f"Asset ID {asset_id} (SN: '{serial_number}') updated by {current_user.username}. Status: {status}.")
                        flash(f'Tracked asset "{serial_number}" updated successfully!', 'success')
                        return redirect(url_for('assets.list_tracked_assets'))

                except ValueError as ve:
                    flash(f'Invalid data format: {str(ve)}', 'danger')
                except Exception as e:
                    current_app.logger.error(f"Error updating tracked asset ID {asset_id} by {current_user.username}: {str(e)}")
                    flash(f'Error updating tracked asset: {str(e)}', 'danger')

        # Preserve form data on error
        form_data = request.form.copy()
        form_data['item_id'] = asset_data['item_id'] # Ensure item_id is part of form_data for re-render
        return render_template('assets/asset_form.html', form_action=f"Edit Asset SN: '{asset_data['serial_number']}'", asset=asset_data, items=items, users=users, statuses=ASSET_STATUSES, form_data=form_data)

    # For GET request
    form_data_get = asset_data.copy()
    if form_data_get.get('purchase_date') and isinstance(form_data_get['purchase_date'], datetime.date):
        form_data_get['purchase_date'] = form_data_get['purchase_date'].strftime('%Y-%m-%d')
    if form_data_get.get('warranty_expiry_date') and isinstance(form_data_get['warranty_expiry_date'], datetime.date):
        form_data_get['warranty_expiry_date'] = form_data_get['warranty_expiry_date'].strftime('%Y-%m-%d')

    return render_template('assets/asset_form.html', form_action=f"Edit Asset SN: '{asset_data['serial_number']}'", asset=asset_data, items=items, users=users, statuses=ASSET_STATUSES, form_data=form_data_get)