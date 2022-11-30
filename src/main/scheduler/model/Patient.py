import sys
sys.path.append("../util/*")
sys.path.append("../db/*")
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import Vaccine
import pymssql

class Patient:
    def __init__(self, username, password=None, salt=None, hash=None):
        self._username = username
        self._password = password
        self._salt = salt
        self._hash = hash

    # getters -- verify patient log in
    def get(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        get_patient_details = "SELECT Salt, Hash FROM Patients WHERE Username = %s"
        try:
            cursor.execute(get_patient_details, self._username) # should return only 1 row
            for row in cursor:
                curr_salt = row['Salt']
                curr_hash = row['Hash']
                calculated_hash = Util.generate_hash(self._password, curr_salt)
                if curr_hash != calculated_hash:
                    cm.close_connection()
                    return None
                else:
                    self.salt = curr_salt
                    self.hash = calculated_hash
                    cm.close_connection()
                    return self # return this Patient object
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()
        return None
    
    def get_username(self):
        return self.username
    
    def get_salt(self):
        return self._salt
    
    def get_hash(self):
        return self._hash
    
    # save new patient info to the database
    def save_to_db(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        add_patient = "INSERT INTO PATIENTS VALUES (%s, %s, %s)"

        try:
            cursor.execute(add_patient, (self._username, self._salt, self._hash))
            conn.commit()
        except pymssql.Error as e:
            raise e
        finally:
            cm.close_connection()
    
    def reserve(self, d, vaccine_name):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        caregiver = ''

        get_availability = "SELECT TOP 1 AV.Username \
                            FROM Availabilities AV LEFT JOIN Appointments AP \
                            ON AV.Time = AP.Time AND AV.Username = AP.CaregiverID\
                            WHERE Time=%s AND AP.AppointmentID IS NULL \
                            ORDER BY AV.Username"
        make_appointment = "INSERT INTO APPOINTMENTS VALUES (%s, %s, %s, %s)"
        get_reservationID = "SELECT AppointmentID FROM Appointments WHERE CaregiverID = %s AND Time = %s"
        update_dose = "UPDATE Vaccines SET "

        # check number of doses
        try:
            vaccine = Vaccine(vaccine_name, -1).get()
            dose = int(vaccine.get_available_doses())
            if dose == 0:
                print("No dose available for your vaccine")
                return
            
            # check schedule
            cursor.execute(get_availability, d)
            if cursor.row_count > 0:
                for row in cursor:
                    caregiver = str(row['Username'])
            else:
                print('No date available')
                return
            
            # add appointment
            cursor.execute(make_appointment, (str(d), caregiver, self.get_username, vaccine))
            
            # print appointment id
            cursor.execute(get_reservationID, (caregiver, str(d)))
            for row in cursor:
                print("Your appointmentID is " + row['AppointmentID'])
            conn.commit()
        except pymssql.Error:
            raise
        finally:
            cm.close_connection()
        
        # decrease dose by 1
        vaccine.decrease_available_doses(1)

        
        
