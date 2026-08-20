import os
import json
import sqlite3
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Body, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wfm_one.db")
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="WFM-One Enterprise Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Database Initialization & Seeding ---
def init_db():
    conn = get_db()
    c = conn.cursor()

    # 1. Accounts Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            created TEXT NOT NULL,
            lastLogin TEXT NOT NULL
        )
    """)

    # 2. Agents Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            vendor TEXT,
            brand TEXT NOT NULL,
            program TEXT,
            team TEXT NOT NULL,
            supervisor TEXT,
            opsManager TEXT,
            location TEXT,
            employmentType TEXT,
            status TEXT NOT NULL,
            hireDate TEXT,
            primarySkill TEXT NOT NULL,
            secondarySkill TEXT,
            skillGroup TEXT,
            proficiency INTEGER DEFAULT 90,
            targetIph INTEGER DEFAULT 10,
            targetOccupancy INTEGER DEFAULT 85,
            attendanceGoal INTEGER DEFAULT 95,
            preferredShift TEXT,
            defaultShift TEXT,
            maxDailyHours INTEGER DEFAULT 8,
            maxWeeklyHours INTEGER DEFAULT 40,
            overtimeEligible BOOLEAN DEFAULT 1,
            workRules TEXT,
            availability TEXT,
            actualOnline TEXT DEFAULT 'Online',
            actualState TEXT DEFAULT 'Voice'
        )
    """)

    # 3. HOOPs Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS hoops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            channel TEXT NOT NULL,
            startTime TEXT NOT NULL,
            endTime TEXT NOT NULL,
            days TEXT NOT NULL,
            timezone TEXT NOT NULL,
            interval INTEGER DEFAULT 30,
            special TEXT DEFAULT 'None'
        )
    """)

    # 4. Time Off Requests Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS time_off_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empId TEXT NOT NULL,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            type TEXT NOT NULL,
            date TEXT NOT NULL,
            duration TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # 5. Active Forecasts Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS active_forecasts (
            brand TEXT NOT NULL,
            channel TEXT NOT NULL,
            volume INTEGER NOT NULL,
            aht INTEGER NOT NULL,
            PRIMARY KEY (brand, channel)
        )
    """)

    # 6. Historical Data Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS historical_data (
            brand TEXT NOT NULL,
            channel TEXT NOT NULL,
            volumes_json TEXT NOT NULL,
            ahts_json TEXT NOT NULL,
            PRIMARY KEY (brand, channel)
        )
    """)

    # 7. Global Settings Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL
        )
    """)

    # 8. Schedule Overrides Table (Manual Adjustments)
    c.execute("""
        CREATE TABLE IF NOT EXISTS schedule_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            date TEXT NOT NULL,
            shift_start TEXT,
            shift_end TEXT,
            is_week_off BOOLEAN DEFAULT 0,
            leave_type TEXT,
            leave_start TEXT,
            leave_end TEXT,
            activities_json TEXT DEFAULT '[]',
            notes TEXT,
            modified_by TEXT,
            modified_at TEXT,
            reason TEXT,
            UNIQUE(agent_id, date)
        )
    """)

    # 9. Schedule Audit Log Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS schedule_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            date_affected TEXT NOT NULL,
            change_type TEXT NOT NULL,
            original_value TEXT NOT NULL,
            new_value TEXT NOT NULL,
            reason TEXT NOT NULL,
            comments TEXT,
            changed_by TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # 10. Schedule 2-Stage Workflow Requests Table (Agent -> TL -> WFM -> Applied)
    c.execute("""
        CREATE TABLE IF NOT EXISTS schedule_workflow_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            request_type TEXT NOT NULL,
            dates_json TEXT NOT NULL,
            details_json TEXT NOT NULL,
            reason TEXT NOT NULL,
            comments TEXT,
            status TEXT NOT NULL DEFAULT 'pending_tl',
            tl_status TEXT DEFAULT 'pending',
            tl_name TEXT,
            tl_comments TEXT,
            tl_action_at TEXT,
            wfm_status TEXT DEFAULT 'pending',
            wfm_name TEXT,
            wfm_comments TEXT,
            wfm_action_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    conn.commit()

    # --- Seeding default workflow requests if empty ---
    c.execute("SELECT COUNT(*) FROM schedule_workflow_requests")
    if c.fetchone()[0] == 0:
        default_wf_requests = [
            ("10001", "John Smith", "leave", json.dumps(["2026-08-25"]), json.dumps({"leave_type": "PTO", "start_time": "08:00", "end_time": "17:00"}), "Family Emergency", "Visiting hometown", "pending_tl", "pending", None, None, None, "pending", None, None, None, "2026-08-19 09:30:00", "2026-08-19 09:30:00"),
            ("10001", "John Smith", "activity", json.dumps(["2026-08-21"]), json.dumps({"activity_name": "Coaching", "start_time": "14:00", "end_time": "15:00", "duration_minutes": 60}), "Skill Upgrade", "1-on-1 performance review", "pending_wfm", "approved", "Marcus Brody", "Approved for coaching hour", "2026-08-19 11:00:00", "pending", None, None, None, "2026-08-19 10:15:00", "2026-08-19 11:00:00"),
            ("10002", "Maria Garcia", "week_off", json.dumps(["2026-08-22"]), json.dumps({"action": "swap", "target_date": "2026-08-24"}), "Personal Shift Swap", "Swap Saturday with Monday off", "approved", "approved", "Marcus Brody", "Swap verified", "2026-08-19 08:30:00", "approved", "Animesh Dubey", "Applied to roster", "2026-08-19 09:15:00", "2026-08-19 08:00:00", "2026-08-19 09:15:00")
        ]
        c.executemany("""
            INSERT INTO schedule_workflow_requests (
                agent_id, agent_name, request_type, dates_json, details_json,
                reason, comments, status, tl_status, tl_name, tl_comments, tl_action_at,
                wfm_status, wfm_name, wfm_comments, wfm_action_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, default_wf_requests)

    conn.commit()

    # --- Seeding default accounts if empty ---
    c.execute("SELECT COUNT(*) FROM accounts")
    if c.fetchone()[0] == 0:
        default_accounts = [
            ("admin@houseofbrands.com", "admin", "WFM Admin", "Animesh Dubey", "Active", "2026-06-25", "Never"),
            ("tl@houseofbrands.com", "leader", "Team Leader", "Marcus Brody", "Active", "2026-06-25", "Never"),
            ("agent@houseofbrands.com", "agent", "Agent", "John Smith", "Active", "2026-06-25", "Never")
        ]
        c.executemany("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?)", default_accounts)

    # --- Seeding default hoops if empty ---
    c.execute("SELECT COUNT(*) FROM hoops")
    if c.fetchone()[0] == 0:
        default_hoops = [
            (1, "Rugs USA", "Voice", "08:00", "22:00", "Mon-Sun", "EST", 30, "None"),
            (2, "Anne Selke", "Chat", "09:00", "18:00", "Mon-Fri", "EST", 30, "None"),
            (3, "Nuloom", "Email", "00:00", "23:59", "Mon-Sun", "GMT", 60, "24/7 Operations")
        ]
        c.executemany("INSERT INTO hoops VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", default_hoops)

    # --- Seeding default requests if empty ---
    c.execute("SELECT COUNT(*) FROM time_off_requests")
    if c.fetchone()[0] == 0:
        default_requests = [
            (1, "EMP1001", "Emily Williams", "Rugs USA", "PTO Vacation", "2026-07-02", "8 Hours", "Family vacation trip", "Pending"),
            (2, "EMP1003", "Sarah Davis", "Anne Selke", "Medical Leave", "2026-06-29", "4 Hours", "Dental appointment checkup", "Pending"),
            (3, "EMP1004", "David Miller", "Nuloom", "Schedule Exception", "2026-06-28", "2 Hours", "School parent teacher meeting", "Approved")
        ]
        c.executemany("INSERT INTO time_off_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", default_requests)

    # --- Seeding default active forecasts if empty ---
    c.execute("SELECT COUNT(*) FROM active_forecasts")
    if c.fetchone()[0] == 0:
        default_forecasts = [
            ("Rugs USA", "Voice", 480, 280),
            ("Rugs USA", "Chat", 320, 180),
            ("Rugs USA", "Email", 150, 450),
            ("Anne Selke", "Voice", 410, 310),
            ("Anne Selke", "Chat", 250, 210),
            ("Anne Selke", "Email", 120, 400),
            ("Nuloom", "Voice", 380, 260),
            ("Nuloom", "Chat", 210, 190),
            ("Nuloom", "Email", 90, 420)
        ]
        c.executemany("INSERT INTO active_forecasts VALUES (?, ?, ?, ?)", default_forecasts)

    # --- Seeding default historical data if empty ---
    c.execute("SELECT COUNT(*) FROM historical_data")
    if c.fetchone()[0] == 0:
        default_hist = [
            ("Rugs USA", "Voice", json.dumps([420, 445, 430, 455, 460, 475]), json.dumps([290, 285, 280, 282, 278, 280])),
            ("Rugs USA", "Chat", json.dumps([290, 310, 305, 315, 320, 325]), json.dumps([190, 185, 182, 180, 185, 180])),
            ("Rugs USA", "Email", json.dumps([130, 140, 135, 145, 150, 148]), json.dumps([460, 455, 450, 448, 452, 450])),
            ("Anne Selke", "Voice", json.dumps([380, 395, 390, 410, 405, 415]), json.dumps([315, 310, 308, 312, 305, 310])),
            ("Anne Selke", "Chat", json.dumps([220, 230, 240, 235, 245, 250]), json.dumps([215, 210, 208, 212, 210, 210])),
            ("Anne Selke", "Email", json.dumps([100, 110, 105, 115, 118, 120]), json.dumps([410, 405, 400, 398, 402, 400])),
            ("Nuloom", "Voice", json.dumps([350, 365, 360, 375, 370, 380]), json.dumps([265, 260, 258, 262, 258, 260])),
            ("Nuloom", "Chat", json.dumps([180, 190, 195, 200, 205, 210]), json.dumps([195, 190, 188, 192, 190, 190])),
            ("Nuloom", "Email", json.dumps([70, 80, 75, 85, 88, 90]), json.dumps([430, 425, 420, 418, 422, 420]))
        ]
        c.executemany("INSERT INTO historical_data VALUES (?, ?, ?, ?)", default_hist)

    # --- Seeding default settings if empty ---
    c.execute("SELECT COUNT(*) FROM app_settings")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO app_settings VALUES (?, ?)", ("shrinkage", json.dumps({
            "scheduledHours": 45,
            "breaks": 7.5,
            "coaching": 0.5,
            "lateness": 0.5,
            "absence": 5.0
        })))

    # --- Seeding 150 mock agents + John Smith if empty ---
    c.execute("SELECT COUNT(*) FROM agents")
    if c.fetchone()[0] == 0:
        first_names = ['John', 'Jane', 'Michael', 'Emily', 'David', 'Sarah', 'James', 'Jessica', 'Robert', 'Ashley', 'William', 'Amanda', 'Joseph', 'Melissa', 'Chris', 'Stephanie', 'Matthew', 'Nicole', 'Daniel', 'Elizabeth']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Garcia', 'Rodriguez', 'Wilson', 'Martinez', 'Anderson', 'Taylor', 'Thomas', 'Hernandez', 'Moore', 'Martin', 'Jackson', 'Lee', 'Thompson']
        skills = ['Voice Customer Care', 'Chat Support', 'Email Billing', 'Technical Support', 'Billing & Payments', 'Retention & Sales']
        shifts = ['08:00-17:00', '09:00-18:00', '10:00-19:00', '12:00-21:00', '22:00-07:00']
        vendors = ['Everise', 'Conduent']
        brands = ['Anne Selke', 'Rugs USA', 'Nuloom']

        agents_list = []

        # 1. John Smith (EMP1000)
        agents_list.append((
            "EMP1000", "John Smith", "agent@houseofbrands.com", "+1 (555) 0199", "Everise",
            "Rugs USA", "Customer Care", "Team Alpha", "Marcus Brody", "Richard Vance",
            "Work From Home", "Full-Time", "Active", "2024-03-12", "Voice Customer Care",
            "Chat Support", "Tier-1 Support", 95, 12, 85, 95, "09:00-18:00", "09:00-18:00",
            8, 40, 1, "Standard 1hr Break Schedule", "Mon-Fri open availability", "Online", "Voice"
        ))

        # 2. 150 mock agents
        for i in range(1, 151):
            emp_id = f"EMP{1000 + i}"
            fn = first_names[i % len(first_names)]
            ln = last_names[i % len(last_names)]
            name = f"{fn} {ln}"
            email = f"{fn.lower()}.{ln.lower()}@houseofbrands.com"
            phone = f"+1 (555) 01{10 + (i % 89)}"
            vendor = vendors[i % len(vendors)]
            brand = brands[i % len(brands)]
            team = "Team Alpha" if i % 2 == 0 else "Team Bravo"
            superv = "Sarah Jenkins" if i % 2 == 0 else "Marcus Brody"
            loc = "Site Dallas" if i % 3 == 0 else "Work From Home"
            
            st = "Active"
            if i % 15 == 0: st = "Training"
            elif i % 25 == 0: st = "LOA"
            elif i % 40 == 0: st = "Inactive"
            elif i % 50 == 0: st = "Attrition"

            pskill = skills[i % len(skills)]
            sskill = skills[(i + 1) % len(skills)]
            shift = shifts[i % len(shifts)]
            actual_state = "Voice" if i % 3 == 0 else ("Chat" if i % 3 == 1 else "Email")

            agents_list.append((
                emp_id, name, email, phone, vendor, brand, "Customer Care", team, superv,
                "Richard Vance", loc, "Full-Time", st, "2024-03-12", pskill, sskill,
                "Tier-1 Support", 90, 12 if i % 2 == 0 else 8, 85, 95, shift, shift,
                8, 40, 1 if i % 3 != 0 else 0, "Standard 1hr Break Schedule",
                "Mon-Fri open availability", "Online", actual_state
            ))

        c.executemany("""
            INSERT INTO agents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, agents_list)

    conn.commit()
    conn.close()

# Execute DB Init
init_db()

# --- Pydantic Data Models ---
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str
    name: str
    secret_code: Optional[str] = None

class AgentStateUpdate(BaseModel):
    actualOnline: str
    actualState: str

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    team: Optional[str] = None
    primarySkill: Optional[str] = None
    status: Optional[str] = None
    defaultShift: Optional[str] = None
    targetIph: Optional[int] = None
    attendanceGoal: Optional[int] = None

class CreateAgentRequest(BaseModel):
    id: str
    name: str
    email: str
    brand: str
    team: str
    primarySkill: str
    status: str
    defaultShift: str
    supervisor: Optional[str] = "Marcus Brody"
    vendor: Optional[str] = "Everise"
    location: Optional[str] = "Work From Home"

class TimeOffRequestCreate(BaseModel):
    empId: str
    name: str
    brand: str
    type: str
    date: str
    duration: str
    reason: str

class StatusUpdateRequest(BaseModel):
    status: str

class HoopCreate(BaseModel):
    brand: str
    channel: str
    startTime: str
    endTime: str
    days: str
    timezone: str
    interval: int = 30
    special: str = "None"

class ForecastSaveRequest(BaseModel):
    brand: str
    channel: str
    volume: int
    aht: int

class HistorySaveRequest(BaseModel):
    brand: str
    channel: str
    volumes: List[int]
    ahts: List[int]

class BulkAgentsSync(BaseModel):
    agents: List[Dict[str, Any]]

class ScheduleOverrideSave(BaseModel):
    agent_id: str
    agent_name: str
    dates: List[str]
    shift_start: Optional[str] = None
    shift_end: Optional[str] = None
    is_week_off: Optional[bool] = False
    leave_type: Optional[str] = None
    leave_start: Optional[str] = None
    leave_end: Optional[str] = None
    activities: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    reason: str
    comments: Optional[str] = None
    changed_by: str = "WFM Admin"

class ScheduleSlideRequest(BaseModel):
    agent_id: str
    agent_name: str
    dates: List[str]
    slide_minutes: int
    reason: str
    comments: Optional[str] = None
    changed_by: str = "WFM Admin"

class ScheduleWeekOffRequest(BaseModel):
    agent_id: str
    agent_name: str
    dates: List[str]
    action: str # "set_off", "remove_off", "swap"
    target_date: Optional[str] = None
    reason: str
    comments: Optional[str] = None
    changed_by: str = "WFM Admin"

class ScheduleLeaveRequest(BaseModel):
    agent_id: str
    agent_name: str
    dates: List[str]
    leave_type: str
    leave_start: Optional[str] = None
    leave_end: Optional[str] = None
    reason: str
    comments: Optional[str] = None
    changed_by: str = "WFM Admin"

class ScheduleActivityRequest(BaseModel):
    agent_id: str
    agent_name: str
    date: str
    activity_name: str
    start_time: str
    end_time: str
    duration_minutes: int
    action: str = "add" # "add" or "remove"
    activity_id: Optional[str] = None
    reason: str
    comments: Optional[str] = None
    changed_by: str = "WFM Admin"

class ScheduleWorkflowRequestCreate(BaseModel):
    agent_id: str
    agent_name: str
    request_type: str # 'leave', 'activity', 'week_off', 'shift_change'
    dates: List[str]
    details: Dict[str, Any]
    reason: str
    comments: Optional[str] = ""
    initiator_role: Optional[str] = "Agent"
    initiator_name: Optional[str] = ""

class ScheduleWorkflowRequestAction(BaseModel):
    request_id: int
    action: str # 'approve' | 'reject'
    role: str # 'Team Leader' | 'WFM Admin'
    actor_name: str
    comments: Optional[str] = ""

# --- API Endpoints ---

# 1. Auth Routes
@app.post("/api/auth/login")
def login(req: LoginRequest):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM accounts WHERE LOWER(email) = ?", (req.email.lower().strip(),))
    row = c.fetchone()
    if not row or row["password"].strip() != req.password.strip():
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid email or password. Please check your credentials.")
    
    # Auto-activate account if it was in Pending status
    if row["status"] == "Pending Approval":
        c.execute("UPDATE accounts SET status = 'Active' WHERE email = ?", (row["email"],))
        conn.commit()
    
    c.execute("UPDATE accounts SET lastLogin = datetime('now') WHERE email = ?", (row["email"],))
    conn.commit()
    
    user_data = {
        "email": row["email"],
        "role": row["role"],
        "name": row["name"],
        "status": "Active",
        "created": row["created"],
        "lastLogin": row["lastLogin"]
    }
    conn.close()
    return {"success": True, "user": user_data}

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM accounts WHERE LOWER(email) = ?", (req.email.lower().strip(),))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="This email is already registered. You can log in directly.")

    is_wfm_role = req.role in ['WFM Admin', 'WFM Analyst', 'WFM Manager', 'Executive Viewer']
    if is_wfm_role and req.secret_code:
        if req.secret_code.strip() != "WFMONE2026":
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid WFM registration secret code. Use WFMONE2026.")

    acc_status = "Active"
    c.execute(
        "INSERT INTO accounts VALUES (?, ?, ?, ?, ?, date('now'), 'Never')",
        (req.email.lower().strip(), req.password.strip(), req.role, req.name.strip(), acc_status)
    )
    conn.commit()
    conn.close()
    return {"success": True, "status": acc_status}

@app.get("/api/accounts")
def get_accounts():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT email, role, name, status, created, lastLogin FROM accounts")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.put("/api/accounts/{email}/status")
def update_account_status(email: str, req: StatusUpdateRequest):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE accounts SET status = ? WHERE LOWER(email) = ?", (req.status, email.lower()))
    conn.commit()
    conn.close()
    return {"success": True}

# 2. Agents Routes
@app.get("/api/agents")
def get_agents(brand: Optional[str] = None, team: Optional[str] = None, status: Optional[str] = None):
    conn = get_db()
    c = conn.cursor()
    query = "SELECT * FROM agents WHERE 1=1"
    params = []
    if brand and brand != "All":
        query += " AND brand = ?"
        params.append(brand)
    if team and team != "All":
        query += " AND team = ?"
        params.append(team)
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.get("/api/agents/{agent_id}")
def get_agent(agent_id: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    return dict(row)

@app.post("/api/agents")
def create_agent(req: CreateAgentRequest):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM agents WHERE id = ?", (req.id,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Agent ID already exists")

    c.execute("""
        INSERT INTO agents (id, name, email, brand, team, primarySkill, status, defaultShift, supervisor, vendor, location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (req.id, req.name, req.email, req.brand, req.team, req.primarySkill, req.status, req.defaultShift, req.supervisor, req.vendor, req.location))
    conn.commit()
    conn.close()
    return {"success": True}

@app.put("/api/agents/{agent_id}/state")
def update_agent_state(agent_id: str, req: AgentStateUpdate):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE agents SET actualOnline = ?, actualState = ? WHERE id = ? OR name = ?", (req.actualOnline, req.actualState, agent_id, agent_id))
    conn.commit()
    conn.close()
    return {"success": True}

@app.put("/api/agents/{agent_id}")
def update_agent(agent_id: str, req: AgentUpdate):
    conn = get_db()
    c = conn.cursor()
    fields = []
    params = []
    for k, v in req.dict(exclude_unset=True).items():
        fields.append(f"{k} = ?")
        params.append(v)
    if not fields:
        conn.close()
        return {"success": True}

    params.append(agent_id)
    c.execute(f"UPDATE agents SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/agents/bulk-sync")
def bulk_sync_agents(req: BulkAgentsSync):
    conn = get_db()
    c = conn.cursor()
    for a in req.agents:
        c.execute("UPDATE agents SET actualOnline = ?, actualState = ? WHERE id = ?", (a.get("actualOnline", "Online"), a.get("actualState", "Voice"), a["id"]))
    conn.commit()
    conn.close()
    return {"success": True}

# 3. HOOP Routes
@app.get("/api/hoops")
def get_hoops():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM hoops ORDER BY id ASC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.post("/api/hoops")
def create_hoop(req: HoopCreate):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO hoops (brand, channel, startTime, endTime, days, timezone, interval, special)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (req.brand, req.channel, req.startTime, req.endTime, req.days, req.timezone, req.interval, req.special))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return {"success": True, "id": new_id}

@app.delete("/api/hoops/{hoop_id}")
def delete_hoop(hoop_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM hoops WHERE id = ?", (hoop_id,))
    conn.commit()
    conn.close()
    return {"success": True}

# 4. Exception / Time-Off Requests
@app.get("/api/requests")
def get_requests():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM time_off_requests ORDER BY id DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.post("/api/requests")
def create_request(req: TimeOffRequestCreate):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO time_off_requests (empId, name, brand, type, date, duration, reason, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
    """, (req.empId, req.name, req.brand, req.type, req.date, req.duration, req.reason))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return {"success": True, "id": new_id}

@app.put("/api/requests/{req_id}/status")
def update_request_status(req_id: int, req: StatusUpdateRequest):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE time_off_requests SET status = ? WHERE id = ?", (req.status, req_id))
    conn.commit()
    conn.close()
    return {"success": True}

# 5. Forecast & Historical Data
@app.get("/api/forecast/active")
def get_active_forecasts():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM active_forecasts")
    rows = c.fetchall()
    res = {}
    for r in rows:
        b = r["brand"]
        ch = r["channel"]
        if b not in res:
            res[b] = {}
        res[b][ch] = {"volume": r["volume"], "aht": r["aht"]}
    conn.close()
    return res

@app.put("/api/forecast/active")
def save_active_forecast(req: ForecastSaveRequest):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO active_forecasts (brand, channel, volume, aht)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(brand, channel) DO UPDATE SET volume = excluded.volume, aht = excluded.aht
    """, (req.brand, req.channel, req.volume, req.aht))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/api/forecast/history")
def get_historical_data():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM historical_data")
    rows = c.fetchall()
    res = {}
    for r in rows:
        b = r["brand"]
        ch = r["channel"]
        if b not in res:
            res[b] = {}
        res[b][ch] = {
            "volumes": json.loads(r["volumes_json"]),
            "ahts": json.loads(r["ahts_json"])
        }
    conn.close()
    return res

@app.put("/api/forecast/history")
def save_historical_data(req: HistorySaveRequest):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO historical_data (brand, channel, volumes_json, ahts_json)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(brand, channel) DO UPDATE SET volumes_json = excluded.volumes_json, ahts_json = excluded.ahts_json
    """, (req.brand, req.channel, json.dumps(req.volumes), json.dumps(req.ahts)))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/api/settings/{key}")
def get_setting(key: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value_json FROM app_settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Setting not found")
    return json.loads(row["value_json"])

@app.put("/api/settings/{key}")
def save_setting(key: str, val: Dict[str, Any] = Body(...)):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO app_settings (key, value_json) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json
    """, (key, json.dumps(val)))
    conn.commit()
    conn.close()
    return {"success": True}

# --- Schedule Management & Intraday API ---

def add_minutes_to_time(time_str: str, minutes: int) -> str:
    try:
        parts = time_str.strip().split(":")
        h, m = int(parts[0]), int(parts[1])
        total_m = (h * 60 + m + minutes) % (24 * 60)
        if total_m < 0:
            total_m += 24 * 60
        return f"{total_m // 60:02d}:{total_m % 60:02d}"
    except Exception:
        return time_str

@app.get("/api/schedule/config")
def get_schedule_config():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT value_json FROM app_settings WHERE key = 'schedule_config'")
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row["value_json"])
    return {
        "activityTypes": ["Coaching", "Lateness", "AWOL", "Absent", "Sickness", "PTO", "Training", "Meeting", "Break", "Lunch", "System Issue", "Technical Issue", "Other"],
        "leaveTypes": ["PTO", "Sick Leave", "Emergency Leave", "Unplanned Leave", "Other Leave"],
        "changeReasons": ["Coverage Requirement", "Business Requirement", "Agent Request", "TL Request", "Emergency", "Absence", "Sickness", "PTO", "Operational Requirement", "Other"],
        "durations": [15, 30, 45, 60, 90, 120]
    }

@app.put("/api/schedule/config")
def save_schedule_config(val: Dict[str, Any] = Body(...)):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO app_settings (key, value_json) VALUES ('schedule_config', ?)
        ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json
    """, (json.dumps(val),))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/api/schedule/overrides")
def get_schedule_overrides(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    agent_id: Optional[str] = None
):
    conn = get_db()
    c = conn.cursor()
    query = "SELECT * FROM schedule_overrides WHERE 1=1"
    params = []
    if agent_id and agent_id != 'All':
        query += " AND agent_id = ?"
        params.append(agent_id)
    if start_date and end_date:
        query += " AND date >= ? AND date <= ?"
        params.extend([start_date, end_date])
    elif start_date:
        query += " AND date >= ?"
        params.append(start_date)

    c.execute(query, params)
    rows = c.fetchall()
    result = []
    for r in rows:
        item = dict(r)
        try:
            item["activities"] = json.loads(item.get("activities_json") or "[]")
        except Exception:
            item["activities"] = []
        result.append(item)
    conn.close()
    return result

@app.post("/api/schedule/override")
def save_schedule_override(req: ScheduleOverrideSave):
    conn = get_db()
    c = conn.cursor()
    
    for dt in req.dates:
        # Check existing override
        c.execute("SELECT * FROM schedule_overrides WHERE agent_id = ? AND date = ?", (req.agent_id, dt))
        existing = c.fetchone()
        
        orig_val = "Default Baseline"
        if existing:
            orig_val = f"Shift: {existing['shift_start']}-{existing['shift_end']}, Off: {existing['is_week_off']}, Leave: {existing['leave_type']}"
        
        new_val = f"Shift: {req.shift_start}-{req.shift_end}, Off: {1 if req.is_week_off else 0}, Leave: {req.leave_type or 'None'}"
        act_json = json.dumps(req.activities if req.activities is not None else [])
        
        c.execute("""
            INSERT INTO schedule_overrides (
                agent_id, agent_name, date, shift_start, shift_end, is_week_off,
                leave_type, leave_start, leave_end, activities_json, notes,
                modified_by, modified_at, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            ON CONFLICT(agent_id, date) DO UPDATE SET
                agent_name = excluded.agent_name,
                shift_start = excluded.shift_start,
                shift_end = excluded.shift_end,
                is_week_off = excluded.is_week_off,
                leave_type = excluded.leave_type,
                leave_start = excluded.leave_start,
                leave_end = excluded.leave_end,
                activities_json = excluded.activities_json,
                notes = excluded.notes,
                modified_by = excluded.modified_by,
                modified_at = datetime('now'),
                reason = excluded.reason
        """, (
            req.agent_id, req.agent_name, dt, req.shift_start, req.shift_end,
            1 if req.is_week_off else 0, req.leave_type, req.leave_start, req.leave_end,
            act_json, req.notes, req.changed_by, req.reason
        ))

        # Log audit
        c.execute("""
            INSERT INTO schedule_audit_log (
                agent_id, agent_name, date_affected, change_type, original_value,
                new_value, reason, comments, changed_by, timestamp
            ) VALUES (?, ?, ?, 'Manual Schedule Override', ?, ?, ?, ?, ?, datetime('now'))
        """, (req.agent_id, req.agent_name, dt, orig_val, new_val, req.reason, req.comments or "", req.changed_by))

    conn.commit()
    conn.close()
    return {"success": True, "count": len(req.dates)}

@app.post("/api/schedule/slide")
def slide_schedule(req: ScheduleSlideRequest):
    conn = get_db()
    c = conn.cursor()
    
    # Get agent default shift if override does not exist
    c.execute("SELECT defaultShift FROM agents WHERE id = ?", (req.agent_id,))
    ag_row = c.fetchone()
    def_shift = ag_row["defaultShift"] if ag_row and ag_row["defaultShift"] else "09:00-18:00"
    def_parts = def_shift.replace(" ", "").split("-")
    def_start = def_parts[0] if len(def_parts) > 0 else "09:00"
    def_end = def_parts[1] if len(def_parts) > 1 else "18:00"

    for dt in req.dates:
        c.execute("SELECT * FROM schedule_overrides WHERE agent_id = ? AND date = ?", (req.agent_id, dt))
        existing = c.fetchone()
        
        cur_start = existing["shift_start"] if (existing and existing["shift_start"]) else def_start
        cur_end = existing["shift_end"] if (existing and existing["shift_end"]) else def_end
        
        new_start = add_minutes_to_time(cur_start, req.slide_minutes)
        new_end = add_minutes_to_time(cur_end, req.slide_minutes)
        
        # Slide activities as well
        cur_acts = []
        if existing and existing["activities_json"]:
            try:
                cur_acts = json.loads(existing["activities_json"])
            except Exception:
                cur_acts = []
        
        slid_acts = []
        for act in cur_acts:
            a_copy = dict(act)
            if "start" in a_copy:
                a_copy["start"] = add_minutes_to_time(a_copy["start"], req.slide_minutes)
            if "end" in a_copy:
                a_copy["end"] = add_minutes_to_time(a_copy["end"], req.slide_minutes)
            slid_acts.append(a_copy)

        is_off = existing["is_week_off"] if existing else 0
        leave_t = existing["leave_type"] if existing else None
        leave_s = existing["leave_start"] if existing else None
        leave_e = existing["leave_end"] if existing else None
        notes = existing["notes"] if existing else None

        c.execute("""
            INSERT INTO schedule_overrides (
                agent_id, agent_name, date, shift_start, shift_end, is_week_off,
                leave_type, leave_start, leave_end, activities_json, notes,
                modified_by, modified_at, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            ON CONFLICT(agent_id, date) DO UPDATE SET
                shift_start = excluded.shift_start,
                shift_end = excluded.shift_end,
                activities_json = excluded.activities_json,
                modified_by = excluded.modified_by,
                modified_at = datetime('now'),
                reason = excluded.reason
        """, (
            req.agent_id, req.agent_name, dt, new_start, new_end, is_off,
            leave_t, leave_s, leave_e, json.dumps(slid_acts), notes, req.changed_by, req.reason
        ))

        # Audit
        c.execute("""
            INSERT INTO schedule_audit_log (
                agent_id, agent_name, date_affected, change_type, original_value,
                new_value, reason, comments, changed_by, timestamp
            ) VALUES (?, ?, ?, 'Slide Shift', ?, ?, ?, ?, ?, datetime('now'))
        """, (
            req.agent_id, req.agent_name, dt,
            f"{cur_start}-{cur_end}",
            f"{new_start}-{new_end} (Slide {req.slide_minutes:+d}m)",
            req.reason, req.comments or "", req.changed_by
        ))

    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/schedule/week-off")
def update_week_off(req: ScheduleWeekOffRequest):
    conn = get_db()
    c = conn.cursor()
    
    if req.action == "swap" and req.target_date and len(req.dates) > 0:
        d1 = req.dates[0]
        d2 = req.target_date
        
        # d1 becomes working (is_week_off = 0), d2 becomes week off (is_week_off = 1)
        for dt, is_off in [(d1, 0), (d2, 1)]:
            c.execute("""
                INSERT INTO schedule_overrides (agent_id, agent_name, date, is_week_off, modified_by, modified_at, reason)
                VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
                ON CONFLICT(agent_id, date) DO UPDATE SET
                    is_week_off = excluded.is_week_off,
                    modified_by = excluded.modified_by,
                    modified_at = datetime('now'),
                    reason = excluded.reason
            """, (req.agent_id, req.agent_name, dt, is_off, req.changed_by, req.reason))
            
            c.execute("""
                INSERT INTO schedule_audit_log (
                    agent_id, agent_name, date_affected, change_type, original_value,
                    new_value, reason, comments, changed_by, timestamp
                ) VALUES (?, ?, ?, 'Swap Week-Off', ?, ?, ?, ?, ?, datetime('now'))
            """, (req.agent_id, req.agent_name, dt, f"Week-off Swap between {d1} and {d2}", f"is_week_off: {is_off}", req.reason, req.comments or "", req.changed_by))
    else:
        is_off_val = 1 if req.action in ["set_off", "add"] else 0
        for dt in req.dates:
            c.execute("""
                INSERT INTO schedule_overrides (agent_id, agent_name, date, is_week_off, modified_by, modified_at, reason)
                VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
                ON CONFLICT(agent_id, date) DO UPDATE SET
                    is_week_off = excluded.is_week_off,
                    modified_by = excluded.modified_by,
                    modified_at = datetime('now'),
                    reason = excluded.reason
            """, (req.agent_id, req.agent_name, dt, is_off_val, req.changed_by, req.reason))

            c.execute("""
                INSERT INTO schedule_audit_log (
                    agent_id, agent_name, date_affected, change_type, original_value,
                    new_value, reason, comments, changed_by, timestamp
                ) VALUES (?, ?, ?, 'Change Week-Off', 'Previous', ?, ?, ?, ?, datetime('now'))
            """, (req.agent_id, req.agent_name, dt, f"is_week_off: {is_off_val}", req.reason, req.comments or "", req.changed_by))

    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/schedule/leave")
def add_schedule_leave(req: ScheduleLeaveRequest):
    conn = get_db()
    c = conn.cursor()
    
    for dt in req.dates:
        c.execute("""
            INSERT INTO schedule_overrides (
                agent_id, agent_name, date, leave_type, leave_start, leave_end,
                modified_by, modified_at, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            ON CONFLICT(agent_id, date) DO UPDATE SET
                leave_type = excluded.leave_type,
                leave_start = excluded.leave_start,
                leave_end = excluded.leave_end,
                modified_by = excluded.modified_by,
                modified_at = datetime('now'),
                reason = excluded.reason
        """, (req.agent_id, req.agent_name, dt, req.leave_type, req.leave_start, req.leave_end, req.changed_by, req.reason))

        c.execute("""
            INSERT INTO schedule_audit_log (
                agent_id, agent_name, date_affected, change_type, original_value,
                new_value, reason, comments, changed_by, timestamp
            ) VALUES (?, ?, ?, 'Add Leave', 'Working', ?, ?, ?, ?, datetime('now'))
        """, (
            req.agent_id, req.agent_name, dt,
            f"{req.leave_type} ({req.leave_start or 'Full Day'}{f'-{req.leave_end}' if req.leave_end else ''})",
            req.reason, req.comments or "", req.changed_by
        ))

    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/schedule/activity")
def manage_schedule_activity(req: ScheduleActivityRequest):
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM schedule_overrides WHERE agent_id = ? AND date = ?", (req.agent_id, req.date))
    existing = c.fetchone()
    
    acts = []
    if existing and existing["activities_json"]:
        try:
            acts = json.loads(existing["activities_json"])
        except Exception:
            acts = []

    if req.action == "remove" and req.activity_id:
        acts = [a for a in acts if str(a.get("id")) != str(req.activity_id)]
    else:
        new_act = {
            "id": req.activity_id or f"ACT_{int(os.urandom(4).hex(), 16)}",
            "name": req.activity_name,
            "start": req.start_time,
            "end": req.end_time,
            "duration": req.duration_minutes
        }
        acts.append(new_act)

    c.execute("""
        INSERT INTO schedule_overrides (
            agent_id, agent_name, date, activities_json, modified_by, modified_at, reason
        ) VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
        ON CONFLICT(agent_id, date) DO UPDATE SET
            activities_json = excluded.activities_json,
            modified_by = excluded.modified_by,
            modified_at = datetime('now'),
            reason = excluded.reason
    """, (req.agent_id, req.agent_name, req.date, json.dumps(acts), req.changed_by, req.reason))

    c.execute("""
        INSERT INTO schedule_audit_log (
            agent_id, agent_name, date_affected, change_type, original_value,
            new_value, reason, comments, changed_by, timestamp
        ) VALUES (?, ?, ?, 'Activity Overlay', 'Previous Activities', ?, ?, ?, ?, datetime('now'))
    """, (
        req.agent_id, req.agent_name, req.date,
        f"{req.action.capitalize()} {req.activity_name} ({req.start_time}-{req.end_time})",
        req.reason, req.comments or "", req.changed_by
    ))

    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/api/schedule/audit-logs")
def get_audit_logs(
    agent_id: Optional[str] = None,
    date: Optional[str] = None,
    limit: int = 50
):
    conn = get_db()
    c = conn.cursor()
    query = "SELECT * FROM schedule_audit_log WHERE 1=1"
    params = []
    if agent_id and agent_id != 'All':
        query += " AND agent_id = ?"
        params.append(agent_id)
    if date:
        query += " AND date_affected = ?"
        params.append(date)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

# --- 2-Stage Schedule Workflow Requests API (Agent -> TL -> WFM -> Applied) ---

@app.get("/api/schedule/requests")
def get_schedule_workflow_requests(
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    stage: Optional[str] = None
):
    conn = get_db()
    c = conn.cursor()
    query = "SELECT * FROM schedule_workflow_requests WHERE 1=1"
    params = []

    if agent_id and agent_id != 'All':
        query += " AND agent_id = ?"
        params.append(agent_id)
    if status and status != 'all':
        query += " AND status = ?"
        params.append(status)
    if stage == 'tl':
        query += " AND status = 'pending_tl'"
    elif stage == 'wfm':
        query += " AND status = 'pending_wfm'"

    query += " ORDER BY id DESC"
    c.execute(query, params)
    rows = c.fetchall()
    result = []
    for r in rows:
        item = dict(r)
        try:
            item["dates"] = json.loads(item.get("dates_json") or "[]")
        except Exception:
            item["dates"] = []
        try:
            item["details"] = json.loads(item.get("details_json") or "{}")
        except Exception:
            item["details"] = {}
        result.append(item)
    conn.close()
    return result

@app.post("/api/schedule/requests")
def create_schedule_workflow_request(req: ScheduleWorkflowRequestCreate):
    conn = get_db()
    c = conn.cursor()
    
    is_tl = req.initiator_role in ["Team Leader", "TL", "Leader"]
    if is_tl:
        c.execute("""
            INSERT INTO schedule_workflow_requests (
                agent_id, agent_name, request_type, dates_json, details_json,
                reason, comments, status, tl_status, tl_name, tl_comments, tl_action_at,
                wfm_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_wfm', 'approved', ?, 'Requested by Team Leader', datetime('now'), 'pending', datetime('now'), datetime('now'))
        """, (
            req.agent_id, req.agent_name, req.request_type,
            json.dumps(req.dates), json.dumps(req.details),
            req.reason, req.comments or "",
            req.initiator_name or "Marcus Brody (TL)"
        ))
    else:
        c.execute("""
            INSERT INTO schedule_workflow_requests (
                agent_id, agent_name, request_type, dates_json, details_json,
                reason, comments, status, tl_status, wfm_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_tl', 'pending', 'pending', datetime('now'), datetime('now'))
        """, (
            req.agent_id, req.agent_name, req.request_type,
            json.dumps(req.dates), json.dumps(req.details),
            req.reason, req.comments or ""
        ))
    
    req_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "request_id": req_id}

@app.post("/api/schedule/requests/action")
def action_schedule_workflow_request(action: ScheduleWorkflowRequestAction):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM schedule_workflow_requests WHERE id = ?", (action.request_id,))
    req = c.fetchone()
    if not req:
        conn.close()
        raise HTTPException(status_code=404, detail="Request not found")

    is_tl = "Leader" in action.role or "TL" in action.role or action.role == "Team Leader"
    is_wfm = "WFM" in action.role or "Admin" in action.role or "Manager" in action.role or "Analyst" in action.role

    if is_tl and req["status"] == "pending_tl":
        if action.action == "approve":
            c.execute("""
                UPDATE schedule_workflow_requests SET
                    tl_status = 'approved',
                    status = 'pending_wfm',
                    tl_name = ?,
                    tl_comments = ?,
                    tl_action_at = datetime('now'),
                    updated_at = datetime('now')
                WHERE id = ?
            """, (action.actor_name, action.comments or "Approved by TL", action.request_id))
        else:
            c.execute("""
                UPDATE schedule_workflow_requests SET
                    tl_status = 'rejected',
                    status = 'rejected',
                    tl_name = ?,
                    tl_comments = ?,
                    tl_action_at = datetime('now'),
                    updated_at = datetime('now')
                WHERE id = ?
            """, (action.actor_name, action.comments or "Rejected by TL", action.request_id))
    
    elif (is_wfm or is_tl) and req["status"] in ["pending_wfm", "pending_tl"]:
        if action.action == "approve":
            c.execute("""
                UPDATE schedule_workflow_requests SET
                    wfm_status = 'approved',
                    status = 'approved',
                    wfm_name = ?,
                    wfm_comments = ?,
                    wfm_action_at = datetime('now'),
                    updated_at = datetime('now')
                WHERE id = ?
            """, (action.actor_name, action.comments or "Approved and applied by WFM", action.request_id))

            # Auto-Apply changes to schedule_overrides and audit log
            try:
                dates = json.loads(req["dates_json"] or "[]")
                details = json.loads(req["details_json"] or "{}")
                r_type = req["request_type"]
                a_id = req["agent_id"]
                a_name = req["agent_name"]

                if r_type == "leave":
                    l_type = details.get("leave_type") or "PTO"
                    l_start = details.get("start_time")
                    l_end = details.get("end_time")
                    for dt in dates:
                        c.execute("""
                            INSERT INTO schedule_overrides (agent_id, agent_name, date, leave_type, leave_start, leave_end, modified_by, modified_at, reason)
                            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
                            ON CONFLICT(agent_id, date) DO UPDATE SET
                                leave_type = excluded.leave_type,
                                leave_start = excluded.leave_start,
                                leave_end = excluded.leave_end,
                                modified_by = excluded.modified_by,
                                modified_at = datetime('now'),
                                reason = excluded.reason
                        """, (a_id, a_name, dt, l_type, l_start, l_end, action.actor_name, f"Workflow Approved: {req['reason']}"))

                        c.execute("""
                            INSERT INTO schedule_audit_log (agent_id, agent_name, date_affected, change_type, original_value, new_value, reason, comments, changed_by, timestamp)
                            VALUES (?, ?, ?, 'Workflow Leave Approved', 'Working', ?, ?, ?, ?, datetime('now'))
                        """, (a_id, a_name, dt, f"{l_type} ({l_start or 'Full Day'}-{l_end or ''})", req["reason"], action.comments or "Workflow Auto-Applied", action.actor_name))

                elif r_type == "activity":
                    act_name = details.get("activity_name") or "Coaching"
                    s_time = details.get("start_time") or "14:00"
                    e_time = details.get("end_time") or "15:00"
                    dur = details.get("duration_minutes") or 60
                    for dt in dates:
                        c.execute("SELECT activities_json FROM schedule_overrides WHERE agent_id = ? AND date = ?", (a_id, dt))
                        ex = c.fetchone()
                        acts = []
                        if ex and ex["activities_json"]:
                            try: acts = json.loads(ex["activities_json"])
                            except: acts = []
                        acts.append({"id": f"ACT_{int(os.urandom(3).hex(), 16)}", "name": act_name, "start": s_time, "end": e_time, "duration": dur})

                        c.execute("""
                            INSERT INTO schedule_overrides (agent_id, agent_name, date, activities_json, modified_by, modified_at, reason)
                            VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
                            ON CONFLICT(agent_id, date) DO UPDATE SET
                                activities_json = excluded.activities_json,
                                modified_by = excluded.modified_by,
                                modified_at = datetime('now'),
                                reason = excluded.reason
                        """, (a_id, a_name, dt, json.dumps(acts), action.actor_name, f"Workflow Approved: {req['reason']}"))

                        c.execute("""
                            INSERT INTO schedule_audit_log (agent_id, agent_name, date_affected, change_type, original_value, new_value, reason, comments, changed_by, timestamp)
                            VALUES (?, ?, ?, 'Workflow Activity Approved', 'Previous', ?, ?, ?, ?, datetime('now'))
                        """, (a_id, a_name, dt, f"{act_name} ({s_time}-{e_time})", req["reason"], action.comments or "Workflow Auto-Applied", action.actor_name))

                elif r_type == "week_off":
                    is_off_val = 1
                    for dt in dates:
                        c.execute("""
                            INSERT INTO schedule_overrides (agent_id, agent_name, date, is_week_off, modified_by, modified_at, reason)
                            VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
                            ON CONFLICT(agent_id, date) DO UPDATE SET
                                is_week_off = excluded.is_week_off,
                                modified_by = excluded.modified_by,
                                modified_at = datetime('now'),
                                reason = excluded.reason
                        """, (a_id, a_name, dt, is_off_val, action.actor_name, f"Workflow Approved: {req['reason']}"))

                        c.execute("""
                            INSERT INTO schedule_audit_log (agent_id, agent_name, date_affected, change_type, original_value, new_value, reason, comments, changed_by, timestamp)
                            VALUES (?, ?, ?, 'Workflow Week-Off Approved', 'Working', 'is_week_off: 1', ?, ?, ?, datetime('now'))
                        """, (a_id, a_name, dt, req["reason"], action.comments or "Workflow Auto-Applied", action.actor_name))
            except Exception as e:
                print(f"Error auto-applying schedule: {e}")
        else:
            c.execute("""
                UPDATE schedule_workflow_requests SET
                    wfm_status = 'rejected',
                    status = 'rejected',
                    wfm_name = ?,
                    wfm_comments = ?,
                    wfm_action_at = datetime('now'),
                    updated_at = datetime('now')
                WHERE id = ?
            """, (action.actor_name, action.comments or "Rejected by WFM", action.request_id))

    conn.commit()
    conn.close()
    return {"success": True}

# --- Static Frontend File Serving ---
@app.get("/")
def serve_root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/index.html")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/styles.css")
def serve_styles():
    return FileResponse(os.path.join(STATIC_DIR, "styles.css"))

@app.get("/app.js")
def serve_app_js():
    return FileResponse(os.path.join(STATIC_DIR, "app.js"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
