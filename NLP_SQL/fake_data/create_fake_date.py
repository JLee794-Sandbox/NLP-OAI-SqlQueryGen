import pyodbc
import os
from faker import Faker
import configparser
import random

# Read the config.ini file
script_dir = os.path.dirname(os.path.abspath(__file__))

config = configparser.ConfigParser()
config.read(os.path.join(script_dir, 'config.ini'))

# Connect to the SQL Server database
server_name = config.get('database', 'server_name')
database_name = config.get('database', 'database_name')
username = config.get('database', 'username')
password = config.get('database', 'password')

print("Server_name: " + server_name)
print('DRIVER={driver};SERVER={server_name};DATABASE={database_name};UID={username};PWD={password}'.format(driver="ODBC Driver 18 for SQL Server",server_name=server_name, database_name=database_name, username=username, password=password))
# Connect to the SQL Server database

conn_str = 'DRIVER={driver};SERVER={server_name};DATABASE={database_name};UID={username};PWD={password}'.format(driver="ODBC Driver 18 for SQL Server",server_name=server_name, database_name=database_name, username=username, password=password)
conn = pyodbc.connect(conn_str)

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

def create_fake_medical_data():
    # Create Faker object
    fake = Faker()

    # Generate and insert 10,000 fake records
    for i in range(10000):
        patient_name = fake.name()
        patient_age = fake.random_int(min=18, max=80)
        patient_gender = random.choice(['Male', 'Female'])
        visit_date = fake.date_between(start_date='-1y', end_date='today')
        visit_type = random.choice(['Initial Consultation', 'Follow-up Visit'])
        visit_notes = fake.paragraph(nb_sentences=5)

        # Insert record into the MedicalData table
        cursor.execute("INSERT INTO MedicalData (PatientName, PatientAge, PatientGender, VisitDate, VisitType, VisitNotes) VALUES (?, ?, ?, ?, ?, ?)",
                       patient_name, patient_age, patient_gender, visit_date, visit_type, visit_notes)

        print(f"Record {i+1} added to the database.")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


# # Generate and insert 10,000 fake records
# for id in range(10000):
#     well_id = id + 1
#     well_name = fake.word() + ' Well'
#     location = fake.city() + ', ' + fake.country()
#     production_date = fake.date_between(start_date='-1y', end_date='today')
#     production_volume = fake.pydecimal(left_digits=6, right_digits=2, positive=True)
#     operator = fake.company()
#     field_name = fake.word() + ' Field'
#     reservoir = fake.word() + ' Reservoir'
#     depth = fake.pydecimal(left_digits=5, right_digits=2, positive=True)
#     api_gravity = fake.pydecimal(left_digits=2, right_digits=2, positive=True)
#     water_cut = fake.pydecimal(left_digits=2, right_digits=2)
#     gas_oil_ratio = fake.pydecimal(left_digits=4, right_digits=2)
#     print(well_name + " added to the database.")
#     # Insert record into the ExplorationProduction table
#     cursor.execute("INSERT INTO ExplorationProduction (WellID, WellName, Location, ProductionDate, ProductionVolume, Operator, FieldName, Reservoir, Depth, APIGravity, WaterCut, GasOilRatio) VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
#                    well_id,well_name, location, production_date, production_volume, operator, field_name, reservoir, depth, api_gravity, water_cut, gas_oil_ratio)


# Commit the changes and close the connection

if __name__ == '__main__':
    create_fake_medical_data()