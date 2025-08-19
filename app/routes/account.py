from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from db import query_db
from app.models import User
from app.utils import log_audit_action, utility_flash_messages_contain_category

bp = Blueprint('account', __name__, url_prefix='/account')

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    departments = query_db("SELECT id, name FROM departments ORDER BY name ASC")
    user_id = current_user.id

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        department_id_str = request.form.get('department_id')

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        # Fetch current user details for comparison and updates
        user_data = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
        if not user_data:
            flash('User not found. Please try logging in again.', 'danger')
            return redirect(url_for('auth.login_page'))

        update_fields = []
        update_values = []
        log_details_parts = []

        # Profile info updates
        if full_name != user_data['full_name']:
            update_fields.append("full_name = %s")
            update_values.append(full_name)
            log_details_parts.append(f"Full Name to '{full_name}'")

        if email != user_data['email']:
            # Check email uniqueness
            existing_email = query_db("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id), one=True)
            if existing_email:
                flash('That email address is already in use by another account.', 'warning')
                return render_template('account/profile.html', departments=departments, form_data=request.form)
            update_fields.append("email = %s")
            update_values.append(email)
            log_details_parts.append(f"Email to '{email}'")

        department_id = int(department_id_str) if department_id_str else None
        if department_id != user_data['department_id']:
            update_fields.append("department_id = %s")
            update_values.append(department_id)
            dept_name = next((d['name'] for d in departments if d['id'] == department_id), 'N/A') if department_id else 'None'
            log_details_parts.append(f"Department to '{dept_name}' (ID: {department_id})")

        # Password update
        if new_password:
            if not current_password:
                flash('Current password is required to set a new password.', 'danger')
            elif not check_password_hash(user_data['password_hash'], current_password):
                flash('Incorrect current password.', 'danger')
            elif new_password != confirm_new_password:
                flash('New passwords do not match.', 'danger')
            else:
                hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                update_fields.append("password_hash = %s")
                update_values.append(hashed_password)
                log_details_parts.append("Password updated")
                flash('Password updated successfully.', 'success')
        elif current_password and not new_password: # User entered current_password but not new_password
             flash('Please enter a new password if you wish to change it.', 'info')


        if not update_fields and not (new_password and utility_flash_messages_contain_category()): # No changes and no password error
            flash('No changes were made to your profile.', 'info')
            return redirect(url_for('account.profile'))
        
        if update_fields and not utility_flash_messages_contain_category(category_filter='danger'):
            try:
                query_str = f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
                update_values.append(user_id)
                query_db(query_str, tuple(update_values), commit=True)
                
                if log_details_parts:
                    log_audit_action('Profile Updated', f"User '{user_data['username']}' updated: {'; '.join(log_details_parts)}.")
                if not utility_flash_messages_contain_category(category_filter='danger') and not (new_password and not utility_flash_messages_contain_category(category_filter='success')): # Avoid double success message
                    flash('Profile updated successfully!', 'success')
                
                # Reload current_user if Flask-Login doesn't do it automatically on next request
                # For now, assume it will be reloaded or changes are minor enough not to break session immediately.
            except Exception as e:
                current_app.logger.error(f"Error updating profile for user ID {user_id}: {str(e)}")
                flash(f'An error occurred while updating your profile: {str(e)}', 'danger')

        return redirect(url_for('account.profile')) # Redirect to show updated info and flash messages

    # For GET request, pre-fill form_data from current_user
    form_data = {
        'full_name': current_user.full_name,
        'email': current_user.email,
        'department_id': str(current_user.department_id) if current_user.department_id else ""
    }
    return render_template('account/profile.html', departments=departments, form_data=form_data)