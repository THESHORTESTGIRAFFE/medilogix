import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "MYSQL_DB": "medilogix_db" # Use the existing database
    })

    with app.app_context():
        # Initialize the schema for the test database
        from db import execute_schema_file
        import os
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'medilogix_db.sql')
        execute_schema_file(schema_path)

        from werkzeug.security import generate_password_hash
        from db import query_db

        # Check if user exists
        user = query_db("SELECT * FROM users WHERE username = %s", ('testuser',), one=True)
        if not user:
            # Create a test user
            query_db(
                "INSERT INTO users (username, password_hash, role, is_active) VALUES (%s, %s, %s, %s)",
                ('testuser', generate_password_hash('password'), 'admin', True),
                commit=True
            )

    yield app

@pytest.fixture
def client(app):
    return app.test_client()