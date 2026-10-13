
import pymysql
import os

# Database connection details from config.py (or environment variables)
db_host = os.environ.get('MYSQL_HOST', 'localhost')
db_user = os.environ.get('MYSQL_USER', 'root')
db_password = os.environ.get('MYSQL_PASSWORD', '')
db_name = os.environ.get('MYSQL_DB', 'medilogix_db')

# Path to the medilogix_db.sql file
schema_file = os.path.join(os.path.dirname(__file__), 'medilogix_db.sql')

def apply_schema():
    try:
        # Establish a database connection
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True  # Autocommit for schema changes
        )
        print("Successfully connected to the database.")

        with connection.cursor() as cursor:
            # Read the schema.sql file
            with open(schema_file, 'r') as f:
                sql_commands = f.read()

            # Split the file content into individual SQL statements
            sql_statements = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]

            # Execute each SQL statement
            for statement in sql_statements:
                try:
                    print(f"Executing: {statement[:100]}...") # Print first 100 chars
                    cursor.execute(statement)
                    print("...success.")
                except pymysql.MySQLError as e:
                    print(f"Error executing statement: {statement}\n{e}")
                    # Decide if you want to stop on error or continue
                    # For schema changes, it's often better to stop
                    raise

        print("Schema applied successfully.")

    except pymysql.MySQLError as e:
        print(f"Database connection failed: {e}")
    except FileNotFoundError:
        print(f"Error: {schema_file} not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    apply_schema()
