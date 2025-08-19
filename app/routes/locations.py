from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from db import query_db # Import from root db.py
# from app.models import Location # Optional: if you want to instantiate Location objects
from app.utils import log_audit_action

bp = Blueprint('locations', __name__, url_prefix='/locations')

# Helper function to get a location
def get_location(location_id):
    location = query_db("SELECT * FROM item_locations WHERE id = %s", (location_id,), one=True)
    return location

# List Item Locations
@bp.route('/')
@login_required
def list_locations():
    locations_data = query_db("SELECT * FROM item_locations ORDER BY name ASC")
    return render_template('locations/list_locations.html', locations=locations_data)

# Add Item Location
@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_location():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')

        if not name:
            flash('Location name is required.', 'danger')
        else:
            try:
                existing_location = query_db("SELECT id FROM item_locations WHERE name = %s", (name,), one=True)
                if existing_location:
                    flash('A location with this name already exists.', 'warning')
                else:
                    query_db("INSERT INTO item_locations (name, description) VALUES (%s, %s)",
                             (name, description), commit=True)
                    flash('Item location added successfully!', 'success')
                    log_audit_action(f"Added location: '{name}'")
                    current_app.logger.info(f"User {current_user.username} added location '{name}'.")
                    return redirect(url_for('locations.list_locations'))
            except Exception as e:
                current_app.logger.error(f"Error adding location by {current_user.username}: {str(e)}")
                flash(f'Error adding location: {str(e)}', 'danger')
    
    return render_template('locations/location_form.html', form_action='Add New')

# Edit Item Location
@bp.route('/<int:location_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_location(location_id):
    location = get_location(location_id)
    if not location:
        flash('Location not found.', 'danger')
        return redirect(url_for('locations.list_locations'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')

        if not name:
            flash('Location name is required.', 'danger')
        else:
            try:
                existing_location = query_db("SELECT id FROM item_locations WHERE name = %s AND id != %s", (name, location_id), one=True)
                if existing_location:
                    flash('Another location with this name already exists.', 'warning')
                else:
                    query_db("UPDATE item_locations SET name = %s, description = %s WHERE id = %s",
                             (name, description, location_id), commit=True)
                    flash('Item location updated successfully!', 'success')
                    log_audit_action(f"Edited location ID {location_id} to '{name}'")
                    current_app.logger.info(f"User {current_user.username} edited location ID {location_id} to '{name}'.")
                    return redirect(url_for('locations.list_locations'))
            except Exception as e:
                current_app.logger.error(f"Error editing location ID {location_id} by {current_user.username}: {str(e)}")
                flash(f'Error updating location: {str(e)}', 'danger')

    return render_template('locations/location_form.html', location=location, form_action=f"Edit '{location['name']}'")

# Delete Item Location
@bp.route('/<int:location_id>/delete', methods=['POST'])
@login_required
def delete_location(location_id):
    location = get_location(location_id)
    # Add checks here: e.g., prevent deletion if items are currently stocked at this location.
    # For now, direct delete.
    log_audit_action(f"Deleted location ID {location_id} ('{location['name'] if location else 'Unknown'}') - DELETION NEEDS CHECKS")
    query_db("DELETE FROM item_locations WHERE id = %s", (location_id,), commit=True)
    flash(f"Location '{location['name'] if location else location_id}' deleted successfully!", 'success')
    current_app.logger.info(f"User {current_user.username} deleted location ID {location_id}.")
    return redirect(url_for('locations.list_locations'))