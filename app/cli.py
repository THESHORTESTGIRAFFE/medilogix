import click
from flask.cli import with_appcontext
from db import query_db, execute_schema_file
from app.utils import calculate_hash
import os

@click.command('init-db-schema')
@with_appcontext
def init_db_schema_command():
    """Initializes the database with the schema."""
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'schema.sql')
    execute_schema_file(schema_path)
    click.echo('Initialized the database schema.')

@click.group()
def audit():
    """Commands for auditing the blockchain-based trails."""
    pass

@audit.command('verify-chain')
@with_appcontext
def verify_chain():
    """Verifies the integrity of the blockchain audit trails."""
    click.echo('Starting verification of audit chains...')

    record_types = ['stock_movement', 'purchase_order', 'grn']
    
    for record_type in record_types:
        click.echo(f"--- Verifying {record_type} chain ---")
        
        table_name = f'{record_type}s'
        if record_type == 'grn':
            table_name = 'goods_received_notes'

        records = query_db(f"SELECT * FROM {table_name} ORDER BY id ASC")
        
        if not records:
            click.echo(f"No records found for {record_type}. Skipping.")
            continue

        is_chain_valid = True
        for i in range(len(records)):
            record = records[i]
            
            # Re-calculate hash
            data_to_hash = record.copy()
            del data_to_hash['hash'] # Remove the stored hash from the data to be hashed
            
            recalculated_hash = calculate_hash(data_to_hash)
            
            if recalculated_hash != record['hash']:
                click.echo(f"  [INVALID] Record ID {record['id']} - Hash mismatch!")
                is_chain_valid = False
            
            # Check previous_hash link
            if i > 0:
                if record['previous_hash'] != records[i-1]['hash']:
                    click.echo(f"  [INVALID] Record ID {record['id']} - Chain broken. previous_hash does not match previous record's hash.")
                    is_chain_valid = False
        
        if is_chain_valid:
            click.echo(f"  [VALID] The {record_type} chain is intact.")
        else:
            click.echo(f"  [INVALID] The {record_type} chain has been tampered with.")

def init_app(app):
    app.cli.add_command(audit)
    app.cli.add_command(init_db_schema_command)
