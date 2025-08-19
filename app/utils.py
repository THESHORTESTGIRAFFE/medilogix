from flask import current_app, request as flask_request
from flask_login import current_user # Assuming db.py is at the project root
from db import query_db # Assuming db.py is at the project root
from functools import wraps
import datetime
from flask import abort

def log_audit_action(action, details=None, user_id=None):
    """Logs an action to the audit_logs table."""
    if user_id is None and current_user and current_user.is_authenticated:
        user_id = current_user.id
    
    ip_address = flask_request.remote_addr
    
    try:
        query_db(
            "INSERT INTO audit_logs (user_id, action, details, ip_address) VALUES (%s, %s, %s, %s)",
            (user_id, action, details, ip_address),
            commit=True
        )
        current_app.logger.info(f"Audit log: UserID {user_id}, Action: {action}, IP: {ip_address}, Details: {details}")
    except Exception as e:
        current_app.logger.error(f"Failed to log audit action '{action}': {str(e)}")

def get_current_stock(item_id, location_id=None):
    """Calculates current stock for an item, optionally at a specific location."""
    base_query = "SELECT SUM(quantity_changed) as stock_level FROM stock_movements WHERE item_id = %s"
    args = [item_id]
    if location_id:
        base_query += " AND location_id = %s"
        args.append(location_id)
    
    result = query_db(base_query, tuple(args), one=True)
    return result['stock_level'] if result and result['stock_level'] is not None else 0

def get_item_stock_by_location(item_id):
    """Retrieves stock levels for a given item, broken down by location."""
    query = """
        SELECT 
            l.id as location_id, 
            l.name as location_name, 
            SUM(sm.quantity_changed) as stock_level
        FROM stock_movements sm
        JOIN item_locations l ON sm.location_id = l.id
        WHERE sm.item_id = %s
        GROUP BY l.id, l.name
        HAVING SUM(sm.quantity_changed) > 0
        ORDER BY l.name;
    """
    return query_db(query, (item_id,))

def get_item_stock_movements(item_id, limit=50):
    """Retrieves the history of stock movements for a given item."""
    query = """
        SELECT sm.*, u.username as user_username, il.name as location_name
        FROM stock_movements sm
        LEFT JOIN users u ON sm.user_id = u.id
        LEFT JOIN item_locations il ON sm.location_id = il.id
        WHERE sm.item_id = %s
        ORDER BY sm.movement_date DESC, sm.id DESC
        LIMIT %s;
    """
    return query_db(query, (item_id, limit))

def get_low_stock_items(threshold_multiplier=1.0):
    """
    Retrieves items that are at or below their reorder threshold.
    A threshold_multiplier can be used to flag items nearing their reorder point
    (e.g., multiplier of 1.2 means flag if stock is <= 120% of threshold).
    """
    items_query = """
        SELECT i.id, i.name, i.sku, i.unit_of_measure, i.reorder_threshold, ic.name as category_name
        FROM items i
        LEFT JOIN item_categories ic ON i.category_id = ic.id
        WHERE i.is_active = TRUE AND i.reorder_threshold > 0;
    """
    all_items_with_threshold = query_db(items_query)

    stock_levels_query = """
        SELECT item_id, SUM(quantity_changed) as current_stock
        FROM stock_movements
        GROUP BY item_id;
    """
    all_stock_levels_raw = query_db(stock_levels_query)
    
    current_stock_map = {sl['item_id']: sl['current_stock'] for sl in all_stock_levels_raw if sl['current_stock'] is not None}

    low_stock_items = []
    for item in all_items_with_threshold:
        item_stock = current_stock_map.get(item['id'], 0)
        if item_stock <= (float(item['reorder_threshold']) * threshold_multiplier):
            item['current_stock'] = item_stock
            low_stock_items.append(item)
    return sorted(low_stock_items, key=lambda x: x['name'])

def roles_required(roles):
    """
    Decorator to ensure user has one of the specified roles.
    :param roles: A list or tuple of role names (e.g., ['admin', 'manager']).
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                # This should ideally be handled by @login_required first
                return current_app.login_manager.unauthorized() 
            if current_user.role not in roles:
                current_app.logger.warning(
                    f"User {current_user.username} (Role: {current_user.role}) "
                    f"attempted to access {flask_request.path} requiring roles: {roles}. IP: {flask_request.remote_addr}"
                )
                log_audit_action(
                    'Access Denied - Insufficient Role',
                    f"Attempted {flask_request.path}. Required: {roles}. User role: {current_user.role}"
                )
                abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_aging_stock_items(days_inactive_threshold=90):
    """
    Retrieves active items with positive stock that haven't had an outward movement
    (issuance, disposal, transfer_out, adjustment_out) for a specified number of days.
    """
    # Get all active items and their current stock
    items_with_stock_query = """
        SELECT 
            i.id, i.name, i.sku, i.unit_of_measure, ic.name as category_name,
            SUM(sm.quantity_changed) as current_stock
        FROM items i
        LEFT JOIN item_categories ic ON i.category_id = ic.id
        JOIN stock_movements sm ON i.id = sm.item_id
        WHERE i.is_active = TRUE
        GROUP BY i.id, i.name, i.sku, i.unit_of_measure, ic.name
        HAVING SUM(sm.quantity_changed) > 0;
    """
    active_items_with_stock = query_db(items_with_stock_query)

    # Get the last outward movement date for all items
    last_outward_movement_query = """
        SELECT 
            item_id, 
            MAX(movement_date) as last_outward_movement_date
        FROM stock_movements
        WHERE movement_type IN ('issuance', 'disposal', 'transfer_out', 'adjustment_out')
        GROUP BY item_id;
    """
    last_movements_raw = query_db(last_outward_movement_query)
    last_movements_map = {lm['item_id']: lm['last_outward_movement_date'] for lm in last_movements_raw}

    aging_items = []
    threshold_date = datetime.datetime.now() - datetime.timedelta(days=days_inactive_threshold)

    for item in active_items_with_stock:
        last_movement_date = last_movements_map.get(item['id'])
        if not last_movement_date or last_movement_date < threshold_date:
            item['last_outward_movement_date'] = last_movement_date # Could be None
            item['days_since_last_movement'] = (datetime.datetime.now() - last_movement_date).days if last_movement_date else None
            aging_items.append(item)
            
    return sorted(aging_items, key=lambda x: (x['last_outward_movement_date'] is None, x['last_outward_movement_date'], x['name']))

# Helper function to check for flash messages of a specific category (centralized)
def utility_flash_messages_contain_category(category_filter='danger', req=None):
    """
    Checks if flashed messages (potentially unconsumed) contain a specific category.
    Handles cases where request.session might not be initialized if req.session is accessed directly.
    Args:
        category_filter (str): The category of flash messages to check for (e.g., 'danger', 'success').
        req (flask.Request, optional): The Flask request object. Defaults to flask.request.
    Returns:
        bool: True if a flash message with the specified category exists, False otherwise.
    """
    # Use the passed request object, or default to the global flask_request
    # The alias 'flask_request' is used to avoid confusion if 'request' is a parameter name.
    effective_request = req if req is not None else flask_request

    # Check messages already processed by Flask (e.g., by get_flashed_messages() in templates)
    # These are typically in request.environ['flask.flashes'] or request._flashes
    processed_flashes = effective_request.environ.get('flask.flashes', [])
    if not processed_flashes and hasattr(effective_request, '_flashes'): # Check _flashes attribute as well
        processed_flashes = getattr(effective_request, '_flashes', [])
    if any(category == category_filter for category, _ in processed_flashes):
        return True
    # Fallback: Check raw messages directly in the session if sessions are available
    if hasattr(effective_request, 'session') and effective_request.session is not None:
        raw_flashes_in_session = effective_request.session.get('_flashes', [])
        if any(category == category_filter for category, _ in raw_flashes_in_session):
            return True
    return False