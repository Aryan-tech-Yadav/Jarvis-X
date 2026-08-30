import json
from models import Patient, Doctor, Medicine, HospitalSystem
from db_config import DbConfig
import services

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

    def get_doctor_by_id(self, doctor_id):
        for doctor in self.doctors:
            if doctor.id == doctor_id:
                return doctor
        return None

    def create_new_doctor(self, doctor):
        self.doctors.append(doctor)

    def get_medicine_by_id(self, medicine_id):
        for medicine in self.medicines:
            if medicine.id == medicine_id:
                return medicine
        return None

    def create_new_medicine(self, medicine):
        self.medicines.append(medicine)

class PatientService:
    def __init__(self, hospital_system, db_config):
        self.hospital_system = hospital_system
        self.db_config = db_config

    def get_patient_by_id(self, patient_id):
        return self.hospital_system.get_patient_by_id(patient_id)

    def create_new_patient(self, patient):
        self.hospital_system.create_new_patient(patient)

class DoctorService:
    def __init__(self, hospital_system, db_config):
        self.hospital_system = hospital_system
        self.db_config = db_config

    def get_doctor_by_id(self, doctor_id):
        return self.hospital_system.get_doctor_by_id(doctor_id)

    def create_new_doctor(self, doctor):
        self.hospital_system.create_new_doctor(doctor)

class MedicineService:
    def __init__(self, hospital_system, db_config):
        self.hospital_system = hospital_system
        self.db_config = db_config

    def get_medicine_by_id(self, medicine_id):
        return self.hospital_system.get_medicine_by_id(medicine_id)

    def create_new_medicine(self, medicine):
        self.hospital_system.create_new_medicine(medicine)

class ServiceManager:
    def __init__(self, hospital_system):
        self.hospital_system = hospital_system
        self.patient_service = PatientService(hospital_system, DbConfig())
        self.doctor_service = DoctorService(hospital_system, DbConfig())
        self.medicine_service = MedicineService(hospital_system, DbConfig())

    def run(self):
        while True:
            print("1. Get Patient by ID")
            print("2. Create New Patient")
            print("3. Get Doctor by ID")
            print("4. Create New Doctor")
            print("5. Get Medicine by ID")
            print("6. Create New Medicine")
            print("7. Quit")
            choice = input("Choose an option: ")
            if choice == "1":
                patient_id = int(input("Enter patient ID: "))
                patient = self.patient_service.get_patient_by_id(patient_id)
                if patient:
                    print(f"Patient Name: {patient.name}, Age: {patient.age}, Contact Number: {patient.contact_number}")
                else:
                    print("Patient not found")
            elif choice == "2":
                patient = Patient(1, "John Doe", 30, "1234567890")
                self.patient_service.create_new_patient(patient)
            elif choice == "3":
                doctor_id = int(input("Enter doctor ID: "))
                doctor = self.doctor_service.get_doctor_by_id(doctor_id)
                if doctor:
                    print(f"Doctor Name: {doctor.name}, Specialty: {doctor.specialty}")
                else:
                    print("Doctor not found")
            elif choice == "4":
                doctor = Doctor(1, "Jane Doe", "Cardiology")
                self.doctor_service.create_new_doctor(doctor)
            elif choice == "5":
                medicine_id = int(input("Enter medicine ID: "))
                medicine = self.medicine_service.get_medicine_by_id(medicine_id)
                if medicine:
                    print(f"Medicine Name: {medicine.name}, Dosage: {medicine.dosage}")
                else:
                    print("Medicine not found")
            elif choice == "6":
                medicine = Medicine(1, "Aspirin", "500mg")
                self.medicine_service.create_new_medicine(medicine)
            elif choice == "7":
                break
            else:
                print("Invalid choice")

def run_service_manager():
    hospital_system = HospitalSystem()
    service_manager = ServiceManager(hospital_system)
    service_manager.run()

if __name__ == "__main__":
    run_service_manager()