from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import requests
import os
from datetime import datetime

app = FastAPI()

# Make sure this matches your patient service port
PATIENT_SERVICE_URL = "http://127.0.0.1:8001/patients"
BILLING_SERVICE_URL = "http://127.0.0.1:8003"

# Get the directory where this file is located
DB_PATH = os.path.join(os.path.dirname(__file__), 'appointments.db')

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    # Added 'time_slot' column
    c.execute('''CREATE TABLE IF NOT EXISTS appointments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER, doctor TEXT, date TEXT, time_slot TEXT)''')
    conn.commit()
    conn.close()

init_db()

class AppointmentRequest(BaseModel):
    patient_id: int
    doctor: str
    date: str
    time_slot: str

@app.post("/appointments/")
def create_appointment(appt: AppointmentRequest):
    # 1. Check if Patient Exists (Microservice Communication)
    response = requests.get(f"{PATIENT_SERVICE_URL}/{appt.patient_id}")
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Patient validation failed")

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()

    # 2. Check for Conflicts (Same Doctor + Same Date + Same Time)
    c.execute("""SELECT id FROM appointments 
                 WHERE doctor=? AND date=? AND time_slot=?""", 
              (appt.doctor, appt.date, appt.time_slot))
    
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="This slot is already booked!")

    # 3. Book it
    c.execute("INSERT INTO appointments (patient_id, doctor, date, time_slot) VALUES (?, ?, ?, ?)", 
              (appt.patient_id, appt.doctor, appt.date, appt.time_slot))
    conn.commit()
    conn.close()
    
    # 4. Automatically generate a bill for this appointment
    try:
        requests.post(f"{BILLING_SERVICE_URL}/bills/generate", params={"patient_id": appt.patient_id})
    except:
        pass  # Bill generation failed but appointment was successful
    
    return {"message": "Appointment booked successfully"}

@app.get("/appointments/history/{patient_id}")
def get_history(patient_id: int):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT doctor, date, time_slot FROM appointments WHERE patient_id=?", (patient_id,))
        rows = c.fetchall()
        conn.close()
        
        # Format list of dictionaries
        return [{"doctor": r[0], "date": r[1], "time": r[2]} for r in rows]
    except Exception as e:
        print(f"ERROR in get_history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/appointments/past/{patient_id}")
def get_past_appointments(patient_id: int):
    """Get only past appointments (date < today)"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT doctor, date, time_slot FROM appointments WHERE patient_id=? AND date < ? ORDER BY date DESC", 
                  (patient_id, today))
        rows = c.fetchall()
        conn.close()
        
        return [{"doctor": r[0], "date": r[1], "time": r[2]} for r in rows]
    except Exception as e:
        print(f"ERROR in get_past_appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/appointments/upcoming/{patient_id}")
def get_upcoming_appointments(patient_id: int):
    """Get only upcoming appointments (date >= today)"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT doctor, date, time_slot FROM appointments WHERE patient_id=? AND date >= ? ORDER BY date ASC", 
                  (patient_id, today))
        rows = c.fetchall()
        conn.close()
        
        return [{"doctor": r[0], "date": r[1], "time": r[2]} for r in rows]
    except Exception as e:
        print(f"ERROR in get_upcoming_appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")