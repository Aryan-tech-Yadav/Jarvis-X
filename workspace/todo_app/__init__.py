import logging
import os
import db  # Import database module
from database import db as db_module  # Import db module from database package

# Ensure logging module is properly configured
logging.basicConfig(level=logging.INFO)

def initialize_app():
    """Initialize the todo app by setting up logging and database connection."""
    logging.basicConfig(level=logging.INFO)
    return db_module.init_db()

def setup_logging(log_level=logging.INFO):
    """Set up logging with the specified log level."""
    logging.basicConfig(level=log_level)

def load_config(config_file='api_gateway/config.txt'):
    """Load configuration from the specified file."""
    try:
        with open(config_file, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"Config file '{config_file}' not found.")
        return None

def setup_database_connection(config):
    """Establish a database connection using the provided configuration."""
    try:
        return db_module.connect(config)
    except Exception as e:
        logging.error(f"Failed to connect to database: {e}")
        return None

def get_app_config():
    """Retrieve the application configuration."""
    config = load_config()
    if config:
        return config
    else:
        return None