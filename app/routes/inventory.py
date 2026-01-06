from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, Response
from flask_login import login_required, current_user
from db import query_db # Import from root db.py
from app.models import Item # Import the Item model
from app.utils import log_audit_action, get_current_stock, get_item_stock_by_location, get_item_stock_movements, get_low_stock_items, roles_required, get_aging_stock_items, generate_barcode_image
from weasyprint import HTML, CSS # For PDF generation
import datetime
bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# Helper function to get a category (could be moved to a models/services layer later)
def get_category(category_id):
    category = query_db("SELECT * FROM item_categories WHERE id = %s", (category_id,), one=True)
    return category

# Item Categories List
@bp.route('/categories')
@login_required
def list_categories():
    # Add search/pagination later
    categories = query_db("SELECT * FROM item_categories ORDER BY name ASC")
    return render_template('inventory/list_categories.html', categories=categories)

# Add Item Category
@bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '') # Optional

        if not name:
            flash('Category name is required.', 'danger')
        else:
            try:
                # Check if category name already exists
                existing_category = query_db("SELECT id FROM item_categories WHERE name = %s", (name,), one=True)
                if existing_category:
                    flash('A category with this name already exists.', 'warning')
                else:
                    query_db("INSERT INTO item_categories (name, description) VALUES (%s, %s)",
                             (name, description), commit=True)
                    flash('Item category added successfully!', 'success')
                    log_audit_action(f"Added item category: '{name}'")
                    current_app.logger.info(f"User {current_user.username} added category '{name}'.")                    
                    return redirect(url_for('inventory.list_categories'))
            except Exception as e:
                current_app.logger.error(f"Error adding category by {current_user.username}: {str(e)}")
                flash(f'Error adding category: {str(e)}', 'danger')
    
    return render_template('inventory/category_form.html', form_action='Add New')

# Edit Item Category
@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = get_category(category_id)
    if not category:
        flash('Category not found.', 'danger')
        return redirect(url_for('inventory.list_categories'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')

        if not name:
            flash('Category name is required.', 'danger')
        else:
            try:
                # Check if new name conflicts with another existing category
                existing_category = query_db("SELECT id FROM item_categories WHERE name = %s AND id != %s", (name, category_id), one=True)
                if existing_category:
                    flash('Another category with this name already exists.', 'warning')
                else:
                    query_db("UPDATE item_categories SET name = %s, description = %s WHERE id = %s",
                             (name, description, category_id), commit=True)
                    flash('Item category updated successfully!', 'success')
                    log_audit_action(f"Edited item category ID {category_id} to '{name}'")
                    current_app.logger.info(f"User {current_user.username} edited category ID {category_id} to '{name}'.")                    
                    return redirect(url_for('inventory.list_categories'))
            except Exception as e:
                current_app.logger.error(f"Error editing category ID {category_id} by {current_user.username}: {str(e)}")
                flash(f'Error updating category: {str(e)}', 'danger')

    return render_template('inventory/category_form.html', category=category, form_action=f"Edit '{category['name']}'")

# Delete Item Category (Consider soft delete or checking for associated items first)
@bp.route('/categories/<int:category_id>/delete', methods=['POST']) # POST for destructive actions
@login_required
def delete_category(category_id):
    # Implementation for delete_category will be added in the next step,
    # including checks for associated items.
    # For now, let's redirect back with a message.
    category = get_category(category_id) # To get name for logging
    # Actual deletion logic will be more complex (check dependencies)
    log_audit_action(f"Attempted delete for category ID {category_id} ('{category['name'] if category else 'Unknown'}') - DELETION NEEDS CHECKS")
    flash(f"Deletion for category '{category['name'] if category else category_id}' needs to be fully implemented with checks.", 'info')
    current_app.logger.info(f"User {current_user.username} attempted to delete category ID {category_id}.")
    return redirect(url_for('inventory.list_categories'))

# Items List
@bp.route('/items')
@login_required
def list_items():
    search_term = request.args.get('search', '').strip()
    query_params = []

    sql = """
        SELECT i.*, ic.name as category_name 
        FROM items i
        LEFT JOIN item_categories ic ON i.category_id = ic.id
    """
    if search_term:
        sql += " WHERE (i.name LIKE %s OR i.sku LIKE %s OR i.description LIKE %s)"
        like_term = f"%{search_term}%"
        query_params.extend([like_term, like_term, like_term])

    sql += " ORDER BY i.name ASC"

    items_data = query_db(sql, tuple(query_params))
    
    items_with_stock = []
    if items_data:
        for item_dict in items_data:
            item_dict['current_stock'] = get_current_stock(item_dict['id'])
            items_with_stock.append(item_dict)
            
    return render_template('inventory/list_items.html', items=items_with_stock, search_term=search_term)

# Add New Item
@bp.route('/items/add', methods=['GET', 'POST'])
@login_required
def add_item():
    # Fetch categories for the dropdown
    categories = query_db("SELECT id, name FROM item_categories ORDER BY name ASC")

    if request.method == 'POST':
        name = request.form.get('name')
        sku = request.form.get('sku', None) # Optional
        description = request.form.get('description', '')
        category_id = request.form.get('category_id')
        unit_of_measure = request.form.get('unit_of_measure')
        reorder_threshold_str = request.form.get('reorder_threshold', '0.00')
        notes = request.form.get('notes', '')
        is_active = 'is_active' in request.form # Checkbox value

        # Basic Validations
        if not name or not category_id or not unit_of_measure:
            flash('Item Name, Category, and Unit of Measure are required.', 'danger')
        else:
            try:
                reorder_threshold = float(reorder_threshold_str) if reorder_threshold_str else 0.00
                processed_category_id = int(category_id) if category_id else None

                # Check if SKU already exists (if provided)
                if sku:
                    existing_item_sku = query_db("SELECT id FROM items WHERE sku = %s", (sku,), one=True)
                    if existing_item_sku:
                        flash(f'An item with SKU "{sku}" already exists.', 'warning')
                        return render_template('inventory/item_form.html', categories=categories, form_action='Add New', form_data=request.form)
                
                query_db("""
                    INSERT INTO items (name, sku, description, category_id, unit_of_measure, reorder_threshold, notes, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (name, sku if sku else None, description, processed_category_id, unit_of_measure, reorder_threshold, notes, is_active), 
                    commit=True, is_insert=True) # is_insert to potentially get lastrowid if needed
                log_audit_action(f"Added item: '{name}' (SKU: {sku or 'N/A'})")
                flash('Item added successfully!', 'success')
                current_app.logger.info(f"User {current_user.username} added item '{name}'.")
                return redirect(url_for('inventory.list_items'))
            except ValueError:
                flash('Invalid reorder threshold. Please enter a valid number.', 'danger')
            except Exception as e:
                current_app.logger.error(f"Error adding item by {current_user.username}: {str(e)}")
                flash(f'Error adding item: {str(e)}', 'danger')
        return render_template('inventory/item_form.html', categories=categories, form_action='Add New', form_data=request.form)

    return render_template('inventory/item_form.html', categories=categories, form_action='Add New')

# View Single Item
@bp.route('/items/<int:item_id>/view')
@login_required
def view_item(item_id):
    item_data = query_db("""
        SELECT i.*, ic.name as category_name
        FROM items i
        LEFT JOIN item_categories ic ON i.category_id = ic.id
        WHERE i.id = %s
    """, (item_id,), one=True)

    if not item_data:
        flash('Item not found.', 'danger')
        return redirect(url_for('inventory.list_items'))

    # Instantiate the Item model
    item_obj = Item(**item_data)
    total_stock = get_current_stock(item_id)
    stock_by_location = get_item_stock_by_location(item_id)
    movements = get_item_stock_movements(item_id)

    # Generate barcode
    barcode_data = item_obj.sku if item_obj.sku else str(item_obj.id)
    barcode_filename = f"item_{item_obj.id}_barcode"
    barcode_path = generate_barcode_image(barcode_data, barcode_filename)

    return render_template('inventory/view_item.html', item=item_obj, total_stock=total_stock, stock_by_location=stock_by_location, movements=movements, barcode_path=barcode_path)

# Edit Item
@bp.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item_data = query_db("SELECT * FROM items WHERE id = %s", (item_id,), one=True)
    if not item_data:
        flash('Item not found.', 'danger')
        return redirect(url_for('inventory.list_items'))

    item_obj = Item(**item_data) 
    categories = query_db("SELECT id, name FROM item_categories ORDER BY name ASC")

    if request.method == 'POST':
        name = request.form.get('name')
        sku = request.form.get('sku', None)
        description = request.form.get('description', '')
        category_id = request.form.get('category_id')
        unit_of_measure = request.form.get('unit_of_measure')
        reorder_threshold_str = request.form.get('reorder_threshold', '0.00')
        notes = request.form.get('notes', '')
        is_active = 'is_active' in request.form

        if not name or not category_id or not unit_of_measure:
            flash('Item Name, Category, and Unit of Measure are required.', 'danger')
        else:
            try:
                reorder_threshold = float(reorder_threshold_str) if reorder_threshold_str else 0.00
                processed_category_id = int(category_id) if category_id else None

                if sku and sku != item_obj.sku:
                    existing_item_sku = query_db("SELECT id FROM items WHERE sku = %s AND id != %s", (sku, item_id), one=True)
                    if existing_item_sku:
                        flash(f'Another item with SKU "{sku}" already exists.', 'warning')
                        return render_template('inventory/item_form.html', item=item_obj, categories=categories, form_action=f"Edit '{item_obj.name}'", form_data=request.form)
                
                query_db("""
                    UPDATE items SET name=%s, sku=%s, description=%s, category_id=%s, 
                                     unit_of_measure=%s, reorder_threshold=%s, notes=%s, is_active=%s
                    WHERE id=%s
                    """, (name, sku if sku else None, description, processed_category_id, 
                          unit_of_measure, reorder_threshold, notes, is_active, item_id), 
                    commit=True)
                
                flash('Item updated successfully!', 'success')
                log_audit_action(f"Updated item ID {item_id}: '{name}'")
                return redirect(url_for('inventory.view_item', item_id=item_id))
            except ValueError:
                flash('Invalid reorder threshold. Please enter a valid number.', 'danger')
            except Exception as e:
                current_app.logger.error(f"Error updating item ID {item_id} by {current_user.username}: {str(e)}")
                flash(f'Error updating item: {str(e)}', 'danger')
        return render_template('inventory/item_form.html', item=item_obj, categories=categories, form_action=f"Edit '{item_obj.name}'", form_data=request.form)

    return render_template('inventory/item_form.html', item=item_obj, categories=categories, form_action=f"Edit '{item_obj.name}'")

# Delete Item
@bp.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item_to_delete = query_db("SELECT name FROM items WHERE id = %s", (item_id,), one=True)

    if not item_to_delete:
        flash('Item not found or already deleted.', 'warning')
        return redirect(url_for('inventory.list_items'))

    try:
        query_db("DELETE FROM items WHERE id = %s", (item_id,), commit=True)
        log_audit_action(f"Deleted item ID {item_id}: '{item_to_delete['name']}'")
        flash(f"Item '{item_to_delete['name']}' deleted successfully!", 'success')
        current_app.logger.info(f"User {current_user.username} deleted item ID {item_id} ('{item_to_delete['name']}').")
    except Exception as e:
        current_app.logger.error(f"Error deleting item ID {item_id} by {current_user.username}: {str(e)}")
        flash(f"Error deleting item: {str(e)}", 'danger')
    return redirect(url_for('inventory.list_items'))

# Reports
@bp.route('/reports/low-stock')
@login_required
@roles_required(['admin', 'manager']) # Example: Only admins and managers
def report_low_stock():
    low_stock_data = get_low_stock_items()
    return render_template('inventory/report_low_stock.html', items=low_stock_data, title="Low Stock Report")

@bp.route('/reports/aging-stock')
@login_required
@roles_required(['admin', 'manager'])
def report_aging_stock():
    days_threshold = request.args.get('days', 90, type=int) # Allow customizing via query param
    aging_stock_data = get_aging_stock_items(days_inactive_threshold=days_threshold)
    return render_template('inventory/report_aging_stock.html', 
                           items=aging_stock_data, 
                           title=f"Aging Stock Report (No outward movement in {days_threshold} days)",
                           days_threshold=days_threshold)

@bp.route('/reports/low-stock/pdf')
@login_required
@roles_required(['admin', 'manager'])
def report_low_stock_pdf():
    low_stock_data = get_low_stock_items()
    title = "Low Stock Report"
    generation_time = datetime.datetime.now()

    html_out = render_template('inventory/report_low_stock_pdf.html', 
                               items=low_stock_data, 
                               title=title,
                               generation_time=generation_time)
    
    pdf_bytes = HTML(string=html_out, base_url=request.url_root).write_pdf()

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment;filename=low_stock_report_{generation_time.strftime('%Y%m%d_%H%M%S')}.pdf"}
    )