from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user # Import timedelta
from app.utils import get_low_stock_items # Import the utility
from flask import Blueprint, render_template, g
from flask_login import login_required, current_user

from db import query_db # Import query_db

bp = Blueprint('main', __name__)
from datetime import datetime, timedelta

@bp.route('/dashboard')
@login_required
def dashboard():
    low_stock_summary = get_low_stock_items()
    num_low_stock_items = len(low_stock_summary)    
    total_items_data = query_db("SELECT COUNT(*) as count FROM items", one=True)    
    active_items_data = query_db("SELECT COUNT(*) as count FROM items WHERE is_active = TRUE", one=True)    
    total_categories_data = query_db("SELECT COUNT(*) as count FROM item_categories", one=True)    
    total_locations_data = query_db("SELECT COUNT(*) as count FROM item_locations", one=True)    
    pending_requisitions_data = query_db("SELECT COUNT(*) as count FROM requisitions WHERE status = 'Pending'", one=True)    
    stock_levels = query_db("SELECT i.name, SUM(s.quantity_changed) as total_quantity FROM items i LEFT JOIN stock_movements s ON i.id = s.item_id GROUP BY i.name ORDER BY i.name")
    stock_chart_data = {'labels': [item['name'] for item in stock_levels], 'quantities': [item['total_quantity'] if item['total_quantity'] else 0 for item in stock_levels]}

    # --- Data for Recent Stock Movements Line Chart (Last 7 Days) ---
    end_date_dt = datetime.now()
    start_date_dt = end_date_dt - timedelta(days=6) # 7 days including today

    # Generate all date labels for the last 7 days to ensure all are present in the chart
    date_labels_for_line_chart = [(start_date_dt + timedelta(days=i)) for i in range(7)]
    formatted_date_labels = [dt.strftime('%Y-%m-%d') for dt in date_labels_for_line_chart]
    movements_counts_by_day = {label: 0 for label in formatted_date_labels}

    # Define the query period
    query_start_date = start_date_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    query_end_date = end_date_dt # Current time on the last day

    query_recent_movements = """
        SELECT
            DATE_FORMAT(movement_date, '%%Y-%%m-%%d') as day,
            COUNT(id) as count
        FROM stock_movements
        WHERE movement_date >= %s AND movement_date <= %s
        GROUP BY day
        ORDER BY day ASC;
    """
    recent_movements_raw = query_db(query_recent_movements, (query_start_date, query_end_date))

    if recent_movements_raw:
        for row in recent_movements_raw:
            day_str = row['day']
            if day_str in movements_counts_by_day:
                movements_counts_by_day[day_str] = int(row['count'])

    recent_movements_chart_data = {
        'labels': formatted_date_labels,
        'data': [movements_counts_by_day[label] for label in formatted_date_labels]
    }

    stats = {
        'total_items': total_items_data['count'] if total_items_data else 0,
        'active_items': active_items_data['count'] if active_items_data else 0,
        'total_categories': total_categories_data['count'] if total_categories_data else 0,
        'total_locations': total_locations_data['count'] if total_locations_data else 0,
    }    
    if current_user.role in ['admin', 'manager']:        
        stats['pending_requisitions'] = pending_requisitions_data['count'] if pending_requisitions_data else 0
    if current_user.role == 'admin':        
        total_users_data = query_db("SELECT COUNT(*) as count FROM users", one=True)
        stats['total_users'] = total_users_data['count'] if total_users_data else 0
    return render_template('main/dashboard.html', 
                           username=current_user.username,
                           num_low_stock_items=num_low_stock_items,
                           stats=stats,
                           stock_chart_data=stock_chart_data,
                           recent_movements_chart_data=recent_movements_chart_data)