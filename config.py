import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key-that-you-should-change-in-production'
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root' # Replace with your DB user
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or '' # Replace with your DB password
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'sams_db' # Replace with your DB name
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'static', 'uploads', 'invoices')
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    # For PyMySQL, ensure autocommit is False in db.py for manual transaction control