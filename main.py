import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="ISSTA HMC Secure Academic & Biometric Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Keeps it open for high-speed local and cloud lookups
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "issta_college.db"

def init_enterprise_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            semester TEXT NOT NULL,
            type TEXT NOT NULL,
            periods_per_week INTEGER NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faculty (
            faculty_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            designation TEXT NOT NULL,
            department TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester TEXT NOT NULL,
            day_of_week TEXT NOT NULL,
            slot_time TEXT NOT NULL,
            subject_code TEXT NOT NULL,
            faculty_assignment TEXT NOT NULL,
            room_log TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS biometric_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            roll_no TEXT NOT NULL,
            name TEXT NOT NULL,
            auth_method TEXT CHECK(auth_method IN ('FACE_RECOG', 'THUMB_SCAN')),
            status TEXT DEFAULT 'SUCCESS'
        )
    """)
    
    # Force clean and pre-load authentic syllabus rows from your handbook
    cursor.execute("DELETE FROM subjects")
    parsed_curriculum = [
        ("BHMT 101", "Fundamentals of Food Production", "Sem I", "Theory", 3),
        ("BHMT 102", "Introduction to Food & Beverage", "Sem I", "Theory", 2),
        ("BHMT 103", "Accommodation Operations - I", "Sem I", "Theory", 2),
        ("BHMT 104", "Introduction to Front Office", "Sem I", "Theory", 2),
        ("BHMP 1108", "Basic Training Kitchen-Indian & Bakery Lab-I", "Sem I", "Practical", 8),
        ("BHMT 2.101", "Indian Regional Cuisine", "Sem III", "Theory", 3),
        ("BHMT 2.102", "Beverages Service", "Sem III", "Theory", 3),
        ("BHMT 2.103", "Linen & Laundry Operations", "Sem III", "Theory", 2),
        ("BHMP 2.108", "Quantity Training Kitchen", "Sem III", "Practical", 8),
        ("BHMT 501", "Advanced Food Production", "Sem V", "Theory", 3),
        ("BHMT 502", "Advanced Food & Beverage Service", "Sem V", "Theory", 3),
        ("BHMT 506", "Hotel A/c & Financial Mgt.", "Sem V", "Theory", 3),
        ("BHMP 508", "Advanced Training Kitchen", "Sem V", "Practical", 8),
        ("BHMT 601", "Larder & Kitchen Management", "Sem VI", "Theory", 3),
        ("BHMT 602", "Food & Beverage Service Management", "Sem VI", "Theory", 3),
        ("BHMP 607", "Larder Kitchen Lab", "Sem VI", "Practical", 8)
    ]
    cursor.executemany("INSERT INTO subjects VALUES (?,?,?,?,?)", parsed_curriculum)
    
    conn.commit()
    conn.close()

init_enterprise_db()

class FacultySchema(BaseModel):
    faculty_id: str
    name: str
    designation: str
    department: str

class SubjectSchema(BaseModel):
    code: str
    name: str
    semester: str
    type: str
    periods_per_week: int

class TimetableSchema(BaseModel):
    semester: str
    day_of_week: str
    slot_time: str
    subject_code: str
    faculty_assignment: str
    room_log: str

class BiometricLog(BaseModel):
    roll_no: str
    name: str
    auth_method: str
    timestamp: str

@app.get("/curriculum/view")
def view_curriculum(semester: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if semester == "All":
        cursor.execute("SELECT code, name, semester, type, periods_per_week FROM subjects")
        rows = cursor.fetchall()
        conn.close()
        # FIXED: Explicit tuple index extraction mapping for full ledger views
        return [{"code": r[0], "name": r[1], "semester": r[2], "type": r[3], "periods": r[4]} for r in rows]
    else:
        cursor.execute("SELECT code, name, type, periods_per_week FROM subjects WHERE semester = ?", (semester,))
        rows = cursor.fetchall()
        conn.close()
        # FIXED: Explicit tuple index extraction mapping for filtered semester grids
        return [{"code": r[0], "name": r[1], "type": r[2], "periods": r[3]} for r in rows]

@app.post("/syllabus/save")
def save_subject(data: SubjectSchema):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO subjects (code, name, semester, type, periods_per_week)
        VALUES (?, ?, ?, ?, ?)
    """, (data.code, data.name, data.semester, data.type, data.periods_per_week))
    conn.commit()
    conn.close()
    return {"message": "Subject updated successfully."}

@app.delete("/syllabus/delete/{code}")
def delete_subject(code: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subjects WHERE code = ?", (code,))
    conn.commit()
    conn.close()
    return {"message": "Subject purged successfully."}

@app.get("/faculty")
def get_faculty():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT faculty_id, name, designation, department FROM faculty")
    rows = cursor.fetchall()
    conn.close()
    # FIXED: Explicit tuple index extraction mapping for faculty listings
    return [{"faculty_id": r[0], "name": r[1], "designation": r[2], "department": r[3]} for r in rows]

@app.post("/faculty/save")
def save_faculty(data: FacultySchema):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO faculty (faculty_id, name, designation, department)
        VALUES (?, ?, ?, ?)
    """, (data.faculty_id, data.name, data.designation, data.department))
    conn.commit()
    conn.close()
    return {"message": "Faculty card saved successfully."}

@app.get("/timetable/weekly")
def view_weekly_schedule(semester: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT day_of_week, slot_time, subject_code, faculty_assignment, room_log FROM daily_schedule WHERE semester = ?", (semester,))
    rows = cursor.fetchall()
    conn.close()
    # FIXED: Explicit tuple index extraction mapping for timetable slots
    return [{"day": r[0], "time": r[1], "code": r[2], "faculty": r[3], "room": r[4]} for r in rows]

@app.post("/biometric/register-pass")
def log_biometric_pass(data: BiometricLog):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO biometric_records (timestamp, roll_no, name, auth_method) VALUES (?,?,?,?)",
                   (data.timestamp, data.roll_no, data.name, data.auth_method))
    conn.commit()
    conn.close()
    return {"status": "SUCCESS"}

@app.get("/biometric/logs")
def get_biometric_logs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, roll_no, name, auth_method, status FROM biometric_records ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    # FIXED: Explicit tuple index extraction mapping for biometric stream records
    return [{"timestamp": r[0], "roll_no": r[1], "name": r[2], "method": r[3], "status": r[4]} for r in rows]
