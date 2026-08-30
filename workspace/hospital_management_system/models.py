import json
from models import Patient, Doctor, Medicine, HospitalSystem
from services import Services
from db_config import DbConfig

class DbConfig:
    def __init__(self):
        self.config = {}

    def load_db_config(self):
        try:
            with open('db_config.txt', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {}

    def get_db_config_value(self, key, default=None):
        return self.config.get(key, default)

    def set_db_config_value(self, key, value):
        self.config[key] = value

db_config = DbConfig()
db_config.load_db_config()

class HospitalSystem:
    def __init__(self):
        self.patients = []
        self.doctors = []
        self.medicines = []

    def get_patient_by_id(self, patient_id):
        for patient in self.patients:
            if patient.id == patient_id:
                return patient
        return None

    def create_new_patient(self, patient):
        self.patients.append(patient)

class Patient:
    def __init__(self, id, name, age, contact_number):
        self.id = id
        self.name = name
        self.age = age
        self.contact_number = contact_number

    @classmethod
    def create_patient(cls, id, name, age, contact_number):
        return cls(id, name, age, contact_number)

class Doctor:
    def __init__(self, id, name, specialty):
        self.id = id
        self.name = name
        self.specialty = specialty

    @classmethod
    def create_doctor(cls, id, name, specialty):
        return cls(id, name, specialty)

class Medicine:
    def __init__(self, id, name, dosage):
        self.id = id
        self.name = name
        self.dosage = dosage

    @classmethod
    def create_medicine(cls, id, name, dosage):
        return cls(id, name, dosage)

class Services:
    def __init__(self, hospital_system):
        self.hospital_system = hospital_system

    def service_main(self):
        self.hospital_system.create_new_patient(Patient.create_patient(1, "John Doe", 30, "1234567890"))

if __name__ == "__main__":
    services = Services(HospitalSystem())
    services.service_main()