import pymysql
from flask import current_app, g

def get_db():
    if 'db' not in g:
        try:
            g.db = pymysql.connect(
                host=current_app.config['MYSQL_HOST'],
                user=current_app.config['MYSQL_USER'],
                password=current_app.config['MYSQL_PASSWORD'],
                database=current_app.config['MYSQL_DB'],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False  # Important for manual transaction control
            )
            current_app.logger.debug("New DB connection established.")
        except pymysql.MySQLError as e:
            current_app.logger.error(f"Failed to connect to database: {e}")
            raise # Re-raise to prevent app from running without DB
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
            current_app.logger.debug("DB connection closed.")
        except Exception as ex:
            current_app.logger.error(f"Error closing database connection: {ex}")

def init_app(app):
    app.teardown_appcontext(close_db)
    # app.cli.add_command(init_db_command) # CLI command to init DB can be added later

def query_db(query, args=(), one=False, commit=False, is_insert=False):
    db = get_db()
    cursor = db.cursor()
    last_id = None
    try:
        current_app.logger.debug(f"Executing query: {query} with args: {args}")
        cursor.execute(query, args)
        if commit:
            db.commit()
            current_app.logger.debug("DB commit successful.")
            if is_insert:
                 last_id = cursor.lastrowid
            return last_id if is_insert else cursor.rowcount
        rv = cursor.fetchall()
        return (rv[0] if rv else None) if one else rv
    except pymysql.MySQLError as e:
        db.rollback()
        current_app.logger.error(f"Database query failed: {e}. Query: {query}, Args: {args}")
        raise
    finally:
        cursor.close()