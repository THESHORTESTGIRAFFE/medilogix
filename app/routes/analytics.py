from flask import Blueprint, render_template, current_app, jsonify
from flask_login import login_required
from db import query_db
from app.utils import roles_required, get_current_stock
import datetime

bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@bp.route('/dashboard')
@login_required
@roles_required(['admin', 'manager', 'procurement_officer'])
def dashboard():
    # 1. Calculate Consumption Rates (Past 30 Days)
    thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    
    # Get all issuance-type movements in the last 30 days
    consumption_query = """
        SELECT 
            item_id, 
            SUM(ABS(quantity_changed)) as total_consumed
        FROM stock_movements 
        WHERE movement_type IN ('issuance', 'disposal', 'transfer_out')
        AND movement_date >= %s
        GROUP BY item_id
    """
    consumption_data = query_db(consumption_query, (thirty_days_ago,))
    consumption_map = {row['item_id']: float(row['total_consumed']) / 30.0 for row in consumption_data}

    # 2. Get All Active Items and Current Stock
    items_query = """
        SELECT i.id, i.name, i.sku, i.unit_of_measure, i.reorder_threshold,
               ic.name as category_name
        FROM items i
        LEFT JOIN item_categories ic ON i.category_id = ic.id
        WHERE i.is_active = TRUE
    """
    items = query_db(items_query)
    
    forecast_data = []
    critical_items = []

    for item in items:
        current_stock = get_current_stock(item['id'])
        daily_rate = consumption_map.get(item['id'], 0.0)
        
        days_remaining = None
        if daily_rate > 0:
            days_remaining = current_stock / daily_rate
        elif current_stock > 0:
            days_remaining = 999 # "Infinite" for display if no consumption recorded recently
        else:
            days_remaining = 0
            
        item_forecast = {
            'id': item['id'],
            'name': item['name'],
            'category': item['category_name'],
            'current_stock': current_stock,
            'daily_rate': round(daily_rate, 2),
            'days_remaining': round(days_remaining, 1) if days_remaining is not None else 'N/A',
            'unit': item['unit_of_measure'],
            'is_critical': (days_remaining is not None and days_remaining <= 14) or (current_stock <= item['reorder_threshold'])
        }
        
        forecast_data.append(item_forecast)
        if item_forecast['is_critical']:
            critical_items.append(item_forecast)

    # Sort critical items by days remaining (worst first)
    critical_items = sorted([i for i in critical_items if isinstance(i['days_remaining'], (int, float))], 
                           key=lambda x: x['days_remaining'])[:10]

    # 3. Consumption Trends for Chart (Past 6 Months)
    # Grouped by month
    trends_query = """
        SELECT 
            DATE_FORMAT(movement_date, '%%Y-%%m') as month,
            SUM(ABS(quantity_changed)) as total_consumed
        FROM stock_movements
        WHERE movement_type IN ('issuance', 'disposal', 'transfer_out')
        AND movement_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY month
        ORDER BY month ASC
    """
    trends_raw = query_db(trends_query)
    trend_labels = [r['month'] for r in trends_raw]
    trend_values = [float(r['total_consumed']) for r in trends_raw]

    return render_template('analytics/dashboard.html', 
                           forecast_data=forecast_data,
                           critical_items=critical_items,
                           trend_chart_data={'labels': trend_labels, 'values': trend_values})
