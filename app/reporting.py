
from db import query_db
import logging
from datetime import date, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_expiring_stock():
    """
    Checks for stock items that are expiring soon (within 30, 60, 90 days)
    and logs the findings. This function is intended to be run as a scheduled job.
    """
    today = date.today()
    periods = {
        "30": today + timedelta(days=30),
        "60": today + timedelta(days=60),
        "90": today + timedelta(days=90)
    }
    
    logging.info("Scheduler: Running check for expiring stock...")
    
    expiring_items = []
    
    for period_days, end_date in periods.items():
        # We only care about items that have not yet expired but will expire by the end_date
        # It finds all batches that will expire between today and the end_date
        sql_query = """
            SELECT 
                i.name,
                i.sku,
                sm.batch_number,
                sm.expiry_date,
                sm.quantity_changed,
                il.name as location_name
            FROM stock_movements sm
            JOIN items i ON sm.item_id = i.id
            JOIN item_locations il ON sm.location_id = il.id
            WHERE sm.expiry_date IS NOT NULL
              AND sm.expiry_date BETWEEN %s AND %s
              AND sm.movement_type IN ('receipt', 'initial_stock', 'adjustment_in', 'transfer_in')
            ORDER BY sm.expiry_date ASC;
        """
        try:
            results = query_db(sql_query, (today, end_date))
            if results:
                for item in results:
                    # Simple check to avoid duplicating alerts for the same batch
                    # A more robust solution would be to aggregate stock levels first
                    identifier = (item['sku'], item['batch_number'], item['expiry_date'])
                    if identifier not in [ (i['sku'], i['batch_number'], i['expiry_date']) for i in expiring_items]:
                        expiring_items.append(item)
                        logging.warning(
                            f"EXPIRING SOON (within {period_days} days): "
                            f"Item: {item['name']} (SKU: {item['sku']}), "
                            f"Batch: {item['batch_number']}, "
                            f"Expires: {item['expiry_date']}, "
                            f"Location: {item['location_name']}"
                        )
        except Exception as e:
            logging.error(f"Scheduler: Error querying for expiring stock for {period_days}-day period: {e}")

    if not expiring_items:
        logging.info("Scheduler: No expiring stock found within the next 90 days.")
    
    return expiring_items

