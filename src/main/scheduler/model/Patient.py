import sys
sys.path.append("../util/*")
sys.path.append("../db/*")
from util.Util import Util
from db.ConnectionManager import ConnectionManager
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