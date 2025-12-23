from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI()

# Get the directory where this file is located
DB_PATH = os.path.join(os.path.dirname(__file__), 'patients.db')

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    # Added 'password' column
    c.execute('''CREATE TABLE IF NOT EXISTS patients 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER, password TEXT)''')
    conn.commit()
    conn.close()

init_db()

class RegisterRequest(BaseModel):
    name: str
    age: int
    password: str

class LoginRequest(BaseModel):
    name: str
    password: str

@app.post("/register")
def register(req: RegisterRequest):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO patients (name, age, password) VALUES (?, ?, ?)", 
              (req.name, req.age, req.password))
    conn.commit()
    patient_id = c.lastrowid
    conn.close()
    return {"message": "Registered successfully", "id": patient_id}

@app.post("/login")
def login(req: LoginRequest):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    # Simple check (In real life, use hashing!)
    c.execute("SELECT id, name FROM patients WHERE name=? AND password=?", (req.name, req.password))
    user = c.fetchone()
    conn.close()
    
    if user:
        return {"id": user[0], "name": user[1]}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/patients/{patient_id}")
def get_patient(patient_id: int):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT id, name, age FROM patients WHERE id=?", (patient_id,))
    patient = c.fetchone()
    conn.close()
    if patient:
        return {"id": patient[0], "name": patient[1], "age": patient[2]}
    raise HTTPException(status_code=404, detail="Patient not found")