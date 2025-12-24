from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import os
from datetime import datetime

app = FastAPI()

# Get the directory where this file is located
DB_PATH = os.path.join(os.path.dirname(__file__), 'billing.db')

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bills 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER, amount REAL, status TEXT, date_generated TEXT)''')
    conn.commit()
    conn.close()

init_db()

class PayBillRequest(BaseModel):
    bill_id: int

@app.post("/bills/generate")
def generate_bill(patient_id: int):
    # This might be triggered by the appointment service in a real app
    # Here we simulate generating a bill
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT INTO bills (patient_id, amount, status, date_generated) VALUES (?, ?, ?, ?)", 
                  (patient_id, 150.0, "PENDING", today))
        conn.commit()
        conn.close()
        return {"message": "Bill generated"}
    except Exception as e:
        print(f"ERROR in generate_bill: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/bills/{patient_id}")
def get_bills(patient_id: int):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id, amount, status, date_generated FROM bills WHERE patient_id=?", (patient_id,))
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "amount": r[1], "status": r[2], "date": r[3]} for r in rows]
    except Exception as e:
        print(f"ERROR in get_bills: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/bills/pending/{patient_id}")
def get_pending_bills(patient_id: int):
    """Get only pending (unpaid) bills"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id, amount, status, date_generated FROM bills WHERE patient_id=? AND status='PENDING'", (patient_id,))
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "amount": r[1], "status": r[2], "date": r[3]} for r in rows]
    except Exception as e:
        print(f"ERROR in get_pending_bills: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/bills/paid/{patient_id}")
def get_paid_bills(patient_id: int):
    """Get only paid bills"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id, amount, status, date_generated FROM bills WHERE patient_id=? AND status='PAID'", (patient_id,))
        rows = c.fetchall()
        conn.close()
        return [{"id": r[0], "amount": r[1], "status": r[2], "date": r[3]} for r in rows]
    except Exception as e:
        print(f"ERROR in get_paid_bills: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/bills/pay")
def pay_bill(req: PayBillRequest):
    """Mark a bill as paid"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
        c = conn.cursor()
        c.execute("UPDATE bills SET status='PAID' WHERE id=?", (req.bill_id,))
        conn.commit()
        conn.close()
        return {"message": "Bill paid successfully"}
    except Exception as e:
        print(f"ERROR in pay_bill: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        print(f"ERROR in get_bills: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")