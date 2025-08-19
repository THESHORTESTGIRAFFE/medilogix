from app import create_app
from app.reporting import check_expiring_stock
from app.utils import get_low_stock_items # Import the low stock function
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = create_app()

# --- Scheduler Setup ---
scheduler = BackgroundScheduler(daemon=True)
# Schedule job to run once a day. For testing, you might change this to 'interval' and seconds=10
scheduler.add_job(check_expiring_stock, 'interval', days=1, id='expiry_check') 

# New job for low stock alerts
def low_stock_alert_job():
    logging.info("Scheduler: Running low stock alert check...")
    low_stock_items = get_low_stock_items()
    if low_stock_items:
        for item in low_stock_items:
            logging.warning(
                f"LOW STOCK ALERT: Item: {item['name']} (SKU: {item['sku']}), "
                f"Current Stock: {item['current_stock']}, Reorder Threshold: {item['reorder_threshold']}"
            )
    else:
        logging.info("Scheduler: No low stock items found.")

scheduler.add_job(low_stock_alert_job, 'interval', days=1, id='low_stock_check')

# Start the scheduler
scheduler.start()
logging.info("Scheduler started. Expiry and Low Stock check jobs are scheduled to run daily.")

# Shut down the scheduler when the app exits
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    # Debug should be False in a production environment
    # Note: Using debug=True with a scheduler can cause the job to run twice upon startup.
    # It's recommended to set debug=False when scheduler functionality is critical.
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
