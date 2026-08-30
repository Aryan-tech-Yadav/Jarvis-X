import logging
import os
import db  # Import database module
from backend_services.services import Services
from database import db as db_module

# Ensure logging module is properly configured
logging.basicConfig(level=logging.INFO)

def initialize_app():
    """Initialize the todo app by setting up logging and database connection."""
    return db_module.init_db()

def get_app_config():
    """Retrieve the application configuration."""
    config = load_config()
    if config:
        os.environ["DB_CONFIG"] = config
    return config

def load_config(config_file='api_gateway/config.txt'):
    """Load configuration from the specified file."""
    try:
        with open(config_file, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"Config file '{config_file}' not found.")
        return None

def run_app_loop(app_config):
    """Run the main application loop."""
    services = Services()
    while True:
        display_menu()
        choice = input("Choose an option: ")
        if choice == "1":
            services.display_tasks()
        elif choice == "2":
            services.add_task()
        elif choice == "3":
            services.delete_task()
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")
    services.stop()

def display_menu():
    """Display the main menu to the user."""
    print("Todo App Menu:")
    print("1. Display Tasks")
    print("2. Add Task")
    print("3. Delete Task")
    print("4. Quit")

if __name__ == "__main__":
    app_config = get_app_config()
    initialize_app()
    run_app_loop(app_config)