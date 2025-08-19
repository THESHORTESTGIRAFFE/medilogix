from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from werkzeug.security import check_password_hash, generate_password_hash 
from flask_login import login_user, logout_user, login_required, current_user
from db import query_db # Import from root db.py
from app.models import User # Import the User model
from app.utils import log_audit_action # Import for audit logging

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_record = query_db("SELECT * FROM users WHERE username = %s", (username,), one=True)
        
        if user_record and user_record['password_hash'] and check_password_hash(user_record['password_hash'], password):
            if bool(user_record['is_active']):
                # Update last_login_at timestamp
                try:
                    query_db("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s", (user_record['id'],), commit=True)
                except Exception as e:
                    current_app.logger.error(f"Failed to update last_login_at for user {user_record['username']}: {str(e)}")
                
                user_obj = User(id=user_record['id'], username=user_record['username'], role=user_record['role'], is_active=bool(user_record['is_active']), last_login_at=user_record.get('last_login_at')) # Pass last_login_at
                login_user(user_obj) # current_user is now set
                log_audit_action('Login Success', f"User '{username}' logged in.")
                flash('Logged in successfully!', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                current_app.logger.warning(f"Login attempt failed for inactive account: {username}, IP: {request.remote_addr}")
                log_audit_action('Login Failed - Inactive Account', f"Attempt by user: {username}", user_id=user_record['id'])
                flash('Your account is inactive. Please contact an administrator.', 'warning')
        else:
            current_app.logger.warning(f"Login attempt failed (invalid credentials) for user: {username}, IP: {request.remote_addr}")
            # user_id will be None here as we don't have a confirmed user
            log_audit_action('Login Failed - Invalid Credentials', f"Attempt by user: {username}")
            flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required # Ensures only logged-in users can access this
def logout_page():
    user_id_before_logout = current_user.id
    username_before_logout = current_user.username
    logout_user()
    log_audit_action('Logout Success', f"User '{username_before_logout}' logged out.", user_id=user_id_before_logout)
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index')) # Redirect to the landing page

@bp.route('/register', methods=['GET', 'POST'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Fetch departments for the dropdown
    departments = query_db("SELECT id, name FROM departments ORDER BY name ASC")

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        department_id = request.form.get('department_id')
        role = request.form.get('role')

        # Basic Validations
        if not all([username, password, confirm_password, full_name, email, department_id, role]):
            flash('All fields are required.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        elif role not in ['staff', 'manager', 'admin']: # Validate role
            flash('Invalid user role selected.', 'danger')
        else:
            # Check if username or email already exists
            existing_user_by_username = query_db("SELECT id FROM users WHERE username = %s", (username,), one=True)
            existing_user_by_email = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)

            if existing_user_by_username:
                flash('Username already taken. Please choose a different one.', 'warning')
            elif existing_user_by_email:
                flash('Email address already registered. Please use a different one or login.', 'warning')
            else:
                try:
                    # Ensure department_id is an integer or None
                    processed_department_id = int(department_id) if department_id else None

                    hashed_password = generate_password_hash(password, method='pbkdf2:sha256') # Use default method or pbkdf2:sha256
                    new_user_id = query_db(
                        "INSERT INTO users (username, password_hash, full_name, email, department_id, role, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (username, hashed_password, full_name, email, processed_department_id, role, True), 
                        commit=True, is_insert=True
                    )
                    if new_user_id:
                        log_audit_action('User Registered', f"New user: {username}, Email: {email}", user_id=new_user_id)
                        current_app.logger.info(f"New user ID {new_user_id} registered: {username}, Email: {email}")
                        flash('Account created successfully! Please login.', 'success')
                    else:
                        current_app.logger.error(f"User registration for {username} seemed successful but failed to get new user ID.")
                        flash('Account created, but an issue occurred logging the registration. Please contact support.', 'warning')
                    return redirect(url_for('auth.login_page'))
                except Exception as e:
                    current_app.logger.error(f"Error during registration for {username}: {str(e)}")
                    flash(f'An error occurred during registration: {str(e)}', 'danger')
        
        # If any error occurred or it's a GET request, re-render with form data
        return render_template('auth/register.html', departments=departments, form_data=request.form)

    return render_template('auth/register.html', departments=departments)