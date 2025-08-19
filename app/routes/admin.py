from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from db import query_db
from app.utils import log_audit_action, roles_required, utility_flash_messages_contain_category

bp = Blueprint('admin', __name__, url_prefix='/admin')

USER_ROLES = ['staff', 'manager', 'admin']

@bp.route('/users')
@login_required
@roles_required(['admin'])
def list_users():
    search_term = request.args.get('search', '').strip()
    query_params = []
    
    sql = """
        SELECT u.id, u.username, u.full_name, u.email, u.role, u.is_active, d.name as department_name
        FROM users u
        LEFT JOIN departments d ON u.department_id = d.id
    """
    if search_term:
        sql += " WHERE (u.username LIKE %s OR u.full_name LIKE %s OR u.email LIKE %s)"
        like_term = f"%{search_term}%"
        query_params.extend([like_term, like_term, like_term])
    
    sql += " ORDER BY u.full_name ASC"
    
    users_data = query_db(sql, tuple(query_params))
    return render_template('admin/list_users.html', users=users_data, search_term=search_term)

@bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@roles_required(['admin'])
def add_user():
    departments = query_db("SELECT id, name FROM departments ORDER BY name ASC")
    if request.method == 'POST':
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        department_id_str = request.form.get('department_id')
        is_active = 'is_active' in request.form

        if not all([username, full_name, email, password, confirm_password, role]):
            flash('All fields marked with * are required.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        elif role not in USER_ROLES:
            flash('Invalid user role selected.', 'danger')
        else:
            existing_user = query_db("SELECT id FROM users WHERE username = %s OR email = %s", (username, email), one=True)
            if existing_user:
                flash('Username or email already exists.', 'warning')
            else:
                try:
                    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                    department_id = int(department_id_str) if department_id_str else None
                    
                    new_user_id = query_db(
                        "INSERT INTO users (username, password_hash, full_name, email, role, department_id, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (username, hashed_password, full_name, email, role, department_id, is_active),
                        commit=True, is_insert=True
                    )
                    log_audit_action('User Created', f"Admin '{current_user.username}' created user '{username}' (ID: {new_user_id}).")
                    flash(f'User "{username}" created successfully!', 'success')
                    return redirect(url_for('admin.list_users'))
                except Exception as e:
                    current_app.logger.error(f"Error creating user by admin {current_user.username}: {str(e)}")
                    flash(f'Error creating user: {str(e)}', 'danger')
        
        # Preserve form data on error
        return render_template('admin/user_form.html', form_action="Add New", departments=departments, roles=USER_ROLES, form_data=request.form)

    return render_template('admin/user_form.html', form_action="Add New", departments=departments, roles=USER_ROLES)

@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required(['admin'])
def edit_user(user_id):
    user_data = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
    if not user_data:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.list_users'))

    departments = query_db("SELECT id, name FROM departments ORDER BY name ASC")

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        role = request.form.get('role')
        department_id_str = request.form.get('department_id')
        is_active = 'is_active' in request.form
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')

        if not all([full_name, email, role]):
            flash('Full Name, Email, and Role are required.', 'danger')
        elif role not in USER_ROLES:
            flash('Invalid user role selected.', 'danger')
        else:
            update_fields = ["full_name = %s", "email = %s", "role = %s", "department_id = %s", "is_active = %s"]
            department_id = int(department_id_str) if department_id_str else None
            update_values = [full_name, email, role, department_id, is_active]
            log_details_parts = [f"Full Name to '{full_name}'", f"Email to '{email}'", f"Role to '{role}'", f"Department ID to '{department_id}'", f"Active to '{is_active}'"]

            # Check email uniqueness if changed
            if email != user_data['email']:
                existing_email = query_db("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id), one=True)
                if existing_email:
                    flash('That email address is already in use by another account.', 'warning')
                    # Pass current form data back to template
                    return render_template('admin/user_form.html', user=user_data, form_action=f"Edit '{user_data['username']}'", departments=departments, roles=USER_ROLES, form_data=request.form)

            # Password update
            if new_password:
                if new_password != confirm_new_password:
                    flash('New passwords do not match.', 'danger')
                else:
                    hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                    update_fields.append("password_hash = %s")
                    update_values.append(hashed_password)
                    log_details_parts.append("Password updated")
                    flash('Password updated successfully.', 'info') # Info, as main success is for profile
            
            if not utility_flash_messages_contain_category(category_filter='danger', req=request):
                try:
                    query_str = f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
                    update_values.append(user_id)
                    query_db(query_str, tuple(update_values), commit=True)
                    
                    log_audit_action('User Updated by Admin', f"Admin '{current_user.username}' updated user '{user_data['username']}' (ID: {user_id}): {'; '.join(log_details_parts)}.")
                    flash(f'User "{user_data["username"]}" updated successfully!', 'success')
                    return redirect(url_for('admin.list_users'))
                except Exception as e:
                    current_app.logger.error(f"Error updating user ID {user_id} by admin {current_user.username}: {str(e)}")
                    flash(f'An error occurred while updating user: {str(e)}', 'danger')
        
        # Preserve form data on error
        # Create a dictionary from user_data to pass as 'user' and merge with request.form for 'form_data'
        current_form_data = dict(request.form)
        current_form_data['username'] = user_data['username'] # ensure username is present
        return render_template('admin/user_form.html', user=user_data, form_action=f"Edit '{user_data['username']}'", departments=departments, roles=USER_ROLES, form_data=current_form_data)

    # For GET request
    form_data_get = {
        'username': user_data['username'],
        'full_name': user_data['full_name'],
        'email': user_data['email'],
        'role': user_data['role'],
        'department_id': str(user_data['department_id']) if user_data['department_id'] else "",
        'is_active': user_data['is_active']
    }
    return render_template('admin/user_form.html', user=user_data, form_action=f"Edit '{user_data['username']}'", departments=departments, roles=USER_ROLES, form_data=form_data_get)

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@roles_required(['admin'])
def delete_user(user_id):
    if user_id == current_user.id:
        flash("You cannot delete your own account.", 'danger')
        return redirect(url_for('admin.list_users'))

    user_to_delete = query_db("SELECT username FROM users WHERE id = %s", (user_id,), one=True)
    if not user_to_delete:
        flash("User not found.", 'warning')
        return redirect(url_for('admin.list_users'))

    try:
        # Consider implications: what happens to audit logs, requisitions by this user?
        # For now, we'll proceed with deletion. Foreign keys might need ON DELETE SET NULL or restrict.
        # Audit logs user_id is ON DELETE SET NULL. Requisitions requester_id is ON DELETE RESTRICT.
        # This means a user cannot be deleted if they have requisitions.
        # You might want to deactivate instead, or handle this more gracefully.
        
        # Check for requisitions
        has_requisitions = query_db("SELECT id FROM requisitions WHERE requester_id = %s LIMIT 1", (user_id,), one=True)
        if has_requisitions:
            flash(f"Cannot delete user '{user_to_delete['username']}' as they have existing requisitions. Consider deactivating the user instead.", 'danger')
            return redirect(url_for('admin.list_users'))

        query_db("DELETE FROM users WHERE id = %s", (user_id,), commit=True)
        log_audit_action('User Deleted by Admin', f"Admin '{current_user.username}' deleted user '{user_to_delete['username']}' (ID: {user_id}).")
        flash(f"User '{user_to_delete['username']}' deleted successfully.", 'success')
    except Exception as e:
        current_app.logger.error(f"Error deleting user ID {user_id} by admin {current_user.username}: {str(e)}")
        flash(f"Error deleting user: {str(e)}. They might be linked to other records (e.g., requisitions).", 'danger')
    return redirect(url_for('admin.list_users'))