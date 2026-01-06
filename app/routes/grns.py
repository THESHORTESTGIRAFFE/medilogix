from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from db import query_db
from app.utils import log_audit_action, roles_required, calculate_hash
from app.models import GoodsReceivedNote # Import the GoodsReceivedNote model
import datetime
import os
from werkzeug.utils import secure_filename

bp = Blueprint('grns', __name__, url_prefix='/grns')

@bp.route('/')
@login_required
def list_grns():
    grns_data = query_db("""
        SELECT grn.*, po.id as purchase_order_number, u.full_name as received_by_user_name
        FROM goods_received_notes grn
        JOIN purchase_orders po ON grn.purchase_order_id = po.id
        JOIN users u ON grn.received_by_user_id = u.id
        ORDER BY grn.received_date DESC
    """)
    grns = [GoodsReceivedNote(**g) for g in grns_data]
    return render_template('grns/list_grns.html', grns=grns)

@bp.route('/new/<int:po_id>', methods=['GET', 'POST'])
@login_required
@roles_required(['admin', 'manager'])
def create_grn(po_id):
    purchase_order = query_db("SELECT po.*, s.name as supplier_name FROM purchase_orders po JOIN suppliers s ON po.supplier_id = s.id WHERE po.id = %s", (po_id,), one=True)
    if not purchase_order:
        flash('Purchase Order not found.', 'danger')
        return redirect(url_for('purchase_orders.list_purchase_orders'))

    po_items = query_db("SELECT poi.*, i.name as item_name, i.sku as item_sku, i.unit_of_measure as item_unit FROM purchase_order_items poi JOIN items i ON poi.item_id = i.id WHERE poi.purchase_order_id = %s", (po_id,))
    locations = query_db("SELECT id, name FROM item_locations ORDER BY name ASC")

    if request.method == 'POST':
        received_date_str = request.form.get('received_date')
        delivery_note_number = request.form.get('delivery_note_number')
        notes = request.form.get('notes')
        location_id = request.form.get('location_id', type=int)

        if not received_date_str or not location_id:
            flash('Received Date and Location are required.', 'danger')
        else:
            try:
                received_date = datetime.datetime.strptime(received_date_str, '%Y-%m-%d').date()

                # File upload handling
                file_path = None
                if 'delivery_note_file' in request.files:
                    file = request.files['delivery_note_file']
                    if file and file.filename != '':
                        filename = secure_filename(file.filename)
                        upload_folder = current_app.config['GRN_UPLOAD_FOLDER']
                        os.makedirs(upload_folder, exist_ok=True)
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)
                        # Store relative path for database or serving
                        file_path = filename 

                grn_items_data = []
                i = 0
                for po_item in po_items:
                    item_id = po_item['item_id']
                    quantity_received_str = request.form.get(f'quantity_received_{i}')
                    
                    if quantity_received_str:
                        try:
                            qty_rec = float(quantity_received_str)
                            
                            ordered_qty = po_item['quantity']
                            variance = ordered_qty - qty_rec
                            reason = request.form.get(f'reason_{i}')

                            # Prevent receiving more than ordered
                            already_received_qty_result = query_db("SELECT SUM(grni.quantity_received) as total_received FROM goods_received_note_items grni JOIN goods_received_notes grn ON grni.grn_id = grn.id WHERE grn.purchase_order_id = %s AND grni.item_id = %s", (po_id, item_id), one=True)
                            already_received_qty = already_received_qty_result['total_received'] if already_received_qty_result['total_received'] else 0
                            
                            if qty_rec > (ordered_qty - already_received_qty):
                                flash(f"Quantity received for {po_item['item_name']} exceeds ordered quantity.", 'danger')
                                return render_template('grns/grn_form.html', 
                                                       purchase_order=purchase_order, 
                                                       po_items=po_items, 
                                                       locations=locations,
                                                       form_data=request.form, 
                                                       form_action="Create GRN")

                            batch_number = request.form.get(f'batch_number_{i}')
                            expiry_date = request.form.get(f'expiry_date_{i}')
                            unit_price = request.form.get(f'unit_price_{i}')

                            grn_items_data.append({
                                'item_id': int(item_id),
                                'quantity_ordered': ordered_qty,
                                'quantity_received': qty_rec,
                                'variance': variance,
                                'reason': reason,
                                'batch_number': batch_number if batch_number else None,
                                'expiry_date': datetime.datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None,
                                'unit_price': float(unit_price) if unit_price else po_item['unit_price']
                            })
                        except ValueError:
                            flash('Invalid quantity, batch, or expiry date format for one or more items.', 'danger')
                            return render_template('grns/grn_form.html', 
                                                   purchase_order=purchase_order, 
                                                   po_items=po_items, 
                                                   locations=locations,
                                                   form_data=request.form, 
                                                   form_action="Create GRN")
                    i += 1
                
                if not grn_items_data:
                    flash('At least one item must be received.', 'danger')
                else:
                    # --- Blockchain Audit Trail ---
                    previous_hash_record = query_db("SELECT last_hash FROM audit_chain_metadata WHERE record_type = %s", ('grn',), one=True)
                    previous_hash = previous_hash_record['last_hash'] if previous_hash_record else None

                    grn_id = query_db("""
                        INSERT INTO goods_received_notes 
                        (purchase_order_id, received_date, received_by_user_id, delivery_note_number, notes, previous_hash, file_path)
                        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """, (
                        po_id, received_date, current_user.id, delivery_note_number, notes, previous_hash, file_path
                    ), commit=True, one=True)['id']

                    if grn_id:
                        # Now, calculate the hash of the full record
                        record_data = {
                            'id': grn_id,
                            'purchase_order_id': po_id,
                            'received_date': received_date,
                            'received_by_user_id': current_user.id,
                            'delivery_note_number': delivery_note_number,
                            'notes': notes,
                            'previous_hash': previous_hash
                        }
                        current_hash = calculate_hash(record_data)

                        # Update the record with its own hash
                        query_db("UPDATE goods_received_notes SET hash = %s WHERE id = %s", (current_hash, grn_id), commit=True)

                        # Update the metadata table with the new hash
                        query_db("""
                            INSERT INTO audit_chain_metadata (record_type, last_hash) 
                            VALUES (%s, %s) 
                            ON DUPLICATE KEY UPDATE last_hash = VALUES(last_hash)
                        """, ('grn', current_hash), commit=True)
                        # --- End Blockchain Audit Trail ---

                        for item_data in grn_items_data:
                            # Insert into goods_received_note_items
                            query_db("""
                                INSERT INTO goods_received_note_items 
                                (grn_id, item_id, quantity_ordered, quantity_received, variance, reason, batch_number, expiry_date, unit_price)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                grn_id, item_data['item_id'], item_data['quantity_ordered'], item_data['quantity_received'], 
                                item_data['variance'], item_data['reason'], item_data['batch_number'], 
                                item_data['expiry_date'], item_data['unit_price']
                            ), commit=True)

                            # Create stock_movement for receipt
                            query_db("""
                                INSERT INTO stock_movements 
                                (item_id, location_id, quantity_changed, movement_type, movement_date, user_id, 
                                 batch_number, expiry_date, cost_per_unit, related_purchase_order_id, notes)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                item_data['item_id'], 
                                location_id,
                                item_data['quantity_received'], 'receipt', 
                                datetime.datetime.now(), current_user.id, 
                                item_data['batch_number'], item_data['expiry_date'], 
                                item_data['unit_price'], po_id, f"GRN #{grn_id} from PO #{po_id}"
                            ), commit=True)
                        
                        # Update PO status based on received quantities
                        po_items_total = query_db("SELECT SUM(quantity) as total_ordered FROM purchase_order_items WHERE purchase_order_id = %s", (po_id,), one=True)
                        total_ordered = po_items_total['total_ordered'] if po_items_total['total_ordered'] else 0

                        grn_items_total = query_db("SELECT SUM(grni.quantity_received) as total_received FROM goods_received_note_items grni JOIN goods_received_notes grn ON grni.grn_id = grn.id WHERE grn.purchase_order_id = %s", (po_id,), one=True)
                        total_received = grn_items_total['total_received'] if grn_items_total['total_received'] else 0

                        new_po_status = 'Partially Fulfilled'
                        if total_received >= total_ordered:
                            new_po_status = 'Fulfilled'
                        
                        query_db("UPDATE purchase_orders SET status = %s WHERE id = %s", (new_po_status, po_id), commit=True)

                        log_audit_action(f"Created GRN ID: {grn_id}", f"PO: {po_id}, New PO Status: {new_po_status}")
                        flash('Goods Received Note created successfully and stock updated!', 'success')
                        return redirect(url_for('grns.list_grns'))
                    else:
                        flash('Failed to create GRN record.', 'danger')

            except ValueError as ve:
                flash(f'Invalid date or quantity format: {str(ve)}', 'danger')
            except Exception as e:
                current_app.logger.error(f"Error creating GRN for PO {po_id} by {current_user.username}: {str(e)}")
                flash(f'Error creating GRN: {str(e)}', 'danger')
        
        return render_template('grns/grn_form.html', 
                               purchase_order=purchase_order, 
                               po_items=po_items,
                               locations=locations,
                               form_data=request.form, 
                               form_action="Create GRN")

@bp.route('/<int:grn_id>')
@login_required
def view_grn(grn_id):
    grn_data = query_db("""
        SELECT grn.*, po.id as purchase_order_number, s.name as supplier_name, u.full_name as received_by_user_name
        FROM goods_received_notes grn
        JOIN purchase_orders po ON grn.purchase_order_id = po.id
        JOIN suppliers s ON po.supplier_id = s.id
        JOIN users u ON grn.received_by_user_id = u.id
        WHERE grn.id = %s
    """, (grn_id,), one=True)

    if not grn_data:
        flash('Goods Received Note not found.', 'danger')
        return redirect(url_for('grns.list_grns'))

    grn_items_data = query_db("""
        SELECT grni.*, i.name as item_name, i.sku as item_sku, i.unit_of_measure as item_unit
        FROM goods_received_note_items grni
        JOIN items i ON grni.item_id = i.id
        WHERE grni.grn_id = %s
    """, (grn_id,))

    return render_template('grns/view_grn.html', 
                           grn=grn_data, 
                           grn_items=grn_items_data)

@bp.route('/reports/variance')
@login_required
@roles_required(['admin', 'manager'])
def variance_report():
    variance_items_data = query_db("""
        SELECT 
            grni.id, grni.grn_id, grni.quantity_ordered, grni.quantity_received, grni.variance, grni.reason,
            grni.unit_price,
            grn.received_date, po.id as po_id, s.name as supplier_name, i.name as item_name, i.sku as item_sku
        FROM goods_received_note_items grni
        JOIN goods_received_notes grn ON grni.grn_id = grn.id
        JOIN purchase_orders po ON grn.purchase_order_id = po.id
        JOIN suppliers s ON po.supplier_id = s.id
        JOIN items i ON grni.item_id = i.id
        WHERE grni.variance != 0
        ORDER BY grn.received_date DESC
    """)
    
    variance_items = []
    for item in variance_items_data:
        item = dict(item)
        item['variance_cost'] = item['variance'] * item['unit_price']
        variance_items.append(item)

    return render_template('grns/report_variance.html', variance_items=variance_items)

@bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['GRN_UPLOAD_FOLDER'], filename)
