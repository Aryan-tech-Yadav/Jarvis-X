import os
import logging
import logging.config
from logging.handlers import RotatingFileHandler
from config import db_config
from models import HospitalSystem
from services import ServiceManager
from typing import Dict

def init_hospital_system() -> HospitalSystem:
    """Initialize the hospital system."""
    logging.config.dictConfig(logging_config())
    os.makedirs('logs', exist_ok=True)
    db_config.connect()
    return HospitalSystem()

def run_main_loop(hospital_system: HospitalSystem) -> None:
    """Run the main loop of the hospital system."""
    while True:
        user_input = input("Enter a command: ").lower()
        if user_input == 'q':
            break
        elif user_input == 'fetch_and_display_patient_data':
            hospital_system.fetch_and_display_patient_data()
        else:
            hospital_system.handle_user_input(user_input)

def handle_user_input(hospital_system: HospitalSystem, user_input: str) -> bool:
    """Handle user input."""
    if user_input == 'q':
        return False
    elif user_input == 'fetch_and_display_patient_data':
        hospital_system.fetch_and_display_patient_data()
    else:
        hospital_system.handle_user_input(user_input)
    return True

def fetch_and_display_patient_data(hospital_system: HospitalSystem) -> None:
    """Fetch and display patient data."""
    patient_data = hospital_system.get_patient_data()
    if patient_data:
        print("Patient Data:")
        for patient in patient_data:
            print(patient)
    else:
        print("No patient data available.")

def main() -> None:
    """Main function."""
    logging_config = {
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
                'filename': '%(filename)s',
            }
        },
        'handlers': {
            'default': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs.log',
                'maxBytes': 1024 * 1024 * 10,
                'backupCount': 5,
                'formatter': 'default'
            }
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'INFO'
            }
        }
    }
    hospital_system = init_hospital_system()
    ServiceManager(hospital_system)
    run_main_loop(hospital_system)

if __name__ == "__main__":
    main()