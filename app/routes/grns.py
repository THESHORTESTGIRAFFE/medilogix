from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from db import query_db
from app.utils import log_audit_action, roles_required
from app.models import GoodsReceivedNote # Import the GoodsReceivedNote model
import datetime

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

    if request.method == 'POST':
        received_date_str = request.form.get('received_date')
        delivery_note_number = request.form.get('delivery_note_number')
        notes = request.form.get('notes')

        if not received_date_str:
            flash('Received Date is required.', 'danger')
        else:
            try:
                received_date = datetime.datetime.strptime(received_date_str, '%Y-%m-%d').date()

                grn_items_data = []
                i = 0
                while True:
                    item_id = request.form.get(f'item_id_{i}')
                    quantity_received = request.form.get(f'quantity_received_{i}')
                    batch_number = request.form.get(f'batch_number_{i}')
                    expiry_date = request.form.get(f'expiry_date_{i}')
                    unit_price = request.form.get(f'unit_price_{i}')

                    if item_id and quantity_received:
                        try:
                            qty_rec = float(quantity_received)
                            grn_items_data.append({
                                'item_id': int(item_id),
                                'quantity_received': qty_rec,
                                'batch_number': batch_number if batch_number else None,
                                'expiry_date': datetime.datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None,
                                'unit_price': float(unit_price) if unit_price else 0.00
                            })
                        except ValueError:
                            flash('Invalid quantity, batch, or expiry date format for one or more items.', 'danger')
                            return render_template('grns/grn_form.html', 
                                                   purchase_order=purchase_order, 
                                                   po_items=po_items, 
                                                   form_data=request.form, 
                                                   form_action="Create GRN")
                    elif i > 0 and not item_id and not quantity_received: 
                        break
                    elif i == 0 and not item_id and not quantity_received: 
                        flash('At least one item must be received.', 'danger')
                        return render_template('grns/grn_form.html', 
                                               purchase_order=purchase_order, 
                                               po_items=po_items, 
                                               form_data=request.form, 
                                               form_action="Create GRN")
                    i += 1
                
                if not grn_items_data:
                    flash('At least one item must be received.', 'danger')
                else:
                    grn_id = query_db("""
                        INSERT INTO goods_received_notes 
                        (purchase_order_id, received_date, received_by_user_id, delivery_note_number, notes)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        po_id, received_date, current_user.id, delivery_note_number, notes
                    ), commit=True, is_insert=True)

                    if grn_id:
                        for item_data in grn_items_data:
                            # Insert into goods_received_note_items
                            query_db("""
                                INSERT INTO goods_received_note_items 
                                (grn_id, item_id, quantity_received, batch_number, expiry_date, unit_price)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                grn_id, item_data['item_id'], item_data['quantity_received'], 
                                item_data['batch_number'], item_data['expiry_date'], item_data['unit_price']
                            ), commit=True)

                            # Create stock_movement for receipt
                            query_db("""
                                INSERT INTO stock_movements 
                                (item_id, location_id, quantity_changed, movement_type, movement_date, user_id, 
                                 batch_number, expiry_date, cost_per_unit, related_purchase_order_id, notes)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                item_data['item_id'], 
                                # Assuming a default receiving location for now, or add to form
                                # For simplicity, let's use the destination location of the PO if available, or a default
                                # For now, we'll assume the PO's supplier_id is linked to a location, or use a fixed one.
                                # This needs to be refined. For now, let's use a dummy location_id=1
                                1, # TODO: Make this dynamic based on user's location or PO's destination
                                item_data['quantity_received'], 'receipt', 
                                datetime.datetime.now(), current_user.id, 
                                item_data['batch_number'], item_data['expiry_date'], 
                                item_data['unit_price'], po_id, f"GRN #{grn_id} from PO #{po_id}"
                            ), commit=True)
                        
                        # Update PO status if all items are received (simple check for now)
                        # This logic can be more complex for partial receipts
                        query_db("UPDATE purchase_orders SET status = %s WHERE id = %s", ('Fulfilled', po_id), commit=True)

                        log_audit_action(f"Created GRN ID: {grn_id}", f"PO: {po_id}")
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
                               form_data=request.form, 
                               form_action="Create GRN")

    return render_template('grns/grn_form.html', 
                           purchase_order=purchase_order, 
                           po_items=po_items, 
                           form_action="Create GRN",
                           current_date=datetime.date.today().strftime('%Y-%m-%d'))

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
