import os
import time
import socket
import psycopg2
from psycopg2 import pool
from contextlib import asynccontextmanager
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Database Configuration via Tailscale Mesh
DB_HOST = os.getenv("DB_HOST", "100.122.119.32")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "attendance_db")
DB_USER = os.getenv("DB_USER", "sister_user")
DB_PASS = os.getenv("DB_PASS", "sister_secure_pass_2026")

FRONTEND_TAILSCALE_IP = "100.91.242.11"
NODE_NAME = "backend-ubuntu-101"

# Connection Pool
db_pool: Optional[pool.ThreadedConnectionPool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        db_pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=3
        )
        print("[LIFESPAN] Database pool initialized successfully to Tailscale IP:", DB_HOST)
    except Exception as e:
        print("[LIFESPAN ERROR] Failed to connect to DB:", e)
    yield
    if db_pool:
        db_pool.closeall()
        print("[LIFESPAN] Database pool closed.")

app = FastAPI(
    title="Sistem Absensi Terdistribusi (Sister Project)",
    description="Microservice Backend yang menghubungkan Frontend (Alpine), Backend (Ubuntu), dan Database (Debian) via Tailscale Wireguard Mesh Network.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database pool is not available. Check DB-Server node via Tailscale.")
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)

# Pydantic Schemas
class CourseCreate(BaseModel):
    code: str
    name: str
    lecturer: str
    sks: int = 3

class SessionCreate(BaseModel):
    course_id: int
    title: str
    token: str
    duration_minutes: int = 60

class AttendanceSubmit(BaseModel):
    token: str
    nim: str
    student_name: str
    status: str = "HADIR"

class StudentCreate(BaseModel):
    nim: str
    name: str
    major: str = "Teknik Informatika"

# Helper to check TCP connectivity and RTT
def measure_tcp_latency(host: str, port: int, timeout: float = 1.0) -> dict:
    start_time = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            latency_ms = (time.perf_counter() - start_time) * 1000
            return {"reachable": True, "latency_ms": round(latency_ms, 2)}
    except Exception as e:
        return {"reachable": False, "error": str(e), "latency_ms": -1}

@app.get("/")
def root_info():
    return {
        "service": "Distributed Attendance API",
        "node": NODE_NAME,
        "os": "Ubuntu 24.04 LTS (LXC 101)",
        "tailscale_ip": "100.118.230.58",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/api/health")
def healthcheck():
    db_status = {"connected": False, "latency_ms": -1, "version": None, "error": None}
    t0 = time.perf_counter()
    try:
        conn = next(get_db())
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            ver = cur.fetchone()[0]
            db_status["connected"] = True
            db_status["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            db_status["version"] = ver.split(",")[0]
    except Exception as e:
        db_status["error"] = str(e)

    # Memory usage on backend
    mem_info = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if "MemTotal" in line or "MemAvailable" in line:
                    parts = line.split()
                    mem_info[parts[0].replace(":", "")] = f"{int(parts[1]) // 1024} MB"
    except Exception:
        pass

    return {
        "status": "healthy" if db_status["connected"] else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backend_node": {
            "name": NODE_NAME,
            "ip": "100.118.230.58",
            "memory": mem_info
        },
        "database_node": {
            "name": "db-server-debian-102",
            "ip": DB_HOST,
            "port": DB_PORT,
            "health": db_status
        }
    }

@app.get("/api/cluster")
def get_cluster_status():
    """Observability endpoint: Measures Tailscale Mesh latency between all 3 nodes"""
    fe_check = measure_tcp_latency(FRONTEND_TAILSCALE_IP, 80)
    db_check = measure_tcp_latency(DB_HOST, DB_PORT)
    
    return {
        "nodes": [
            {
                "vmid": 100,
                "name": "frontend",
                "distro": "Alpine Linux (musl libc)",
                "role": "Web Interface & Reverse Proxy",
                "tailscale_ip": FRONTEND_TAILSCALE_IP,
                "service": "Nginx (Port 80)",
                "network": fe_check
            },
            {
                "vmid": 101,
                "name": "backend",
                "distro": "Ubuntu 24.04 (glibc)",
                "role": "REST API Business Logic & Dispatcher",
                "tailscale_ip": "100.118.230.58",
                "service": "FastAPI + Uvicorn (Port 8000)",
                "network": {"reachable": True, "latency_ms": 0.0}
            },
            {
                "vmid": 102,
                "name": "db-server",
                "distro": "Debian 12 (glibc)",
                "role": "Distributed Relational Storage",
                "tailscale_ip": DB_HOST,
                "service": f"PostgreSQL 15 (Port {DB_PORT})",
                "network": db_check
            }
        ],
        "distributed_features": [
            "Mesh Networking via Tailscale WireGuard",
            "LXC Multi-Distro Userland Execution (Alpine / Ubuntu / Debian)",
            "PostgreSQL Remote Listen on Tailscale Interface",
            "Distributed ACID-compliant Attendance Logging"
        ]
    }

@app.get("/api/courses")
def get_courses():
    conn = next(get_db())
    with conn.cursor() as cur:
        cur.execute("SELECT id, code, name, lecturer, sks FROM courses ORDER BY code;")
        rows = cur.fetchall()
        return [{"id": r[0], "code": r[1], "name": r[2], "lecturer": r[3], "sks": r[4]} for r in rows]

@app.post("/api/courses")
def add_course(course: CourseCreate):
    conn = next(get_db())
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO courses (code, name, lecturer, sks) VALUES (%s, %s, %s, %s) RETURNING id;",
                (course.code, course.name, course.lecturer, course.sks)
            )
            cid = cur.fetchone()[0]
            conn.commit()
            return {"message": "Course created successfully", "id": cid}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/sessions")
def get_sessions():
    conn = next(get_db())
    with conn.cursor() as cur:
        cur.execute("""
            SELECT s.id, s.title, s.token, s.is_active, s.expires_at, s.created_at,
                   c.code, c.name,
                   (SELECT COUNT(*) FROM attendances a WHERE a.session_id = s.id) as total_attendees
            FROM sessions s
            JOIN courses c ON s.course_id = c.id
            ORDER BY s.created_at DESC;
        """)
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "title": r[1],
                "token": r[2],
                "is_active": r[3] and (r[4] > datetime.now(timezone.utc)),
                "expires_at": r[4].isoformat() if r[4] else None,
                "created_at": r[5].isoformat() if r[5] else None,
                "course_code": r[6],
                "course_name": r[7],
                "total_attendees": r[8]
            }
            for r in rows
        ]

@app.post("/api/sessions")
def create_session(sess: SessionCreate):
    conn = next(get_db())
    expires = datetime.now(timezone.utc) + timedelta(minutes=sess.duration_minutes)
    token_clean = sess.token.strip().upper()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (course_id, title, token, is_active, expires_at)
                VALUES (%s, %s, %s, true, %s)
                RETURNING id;
                """,
                (sess.course_id, sess.title, token_clean, expires)
            )
            sid = cur.fetchone()[0]
            # Log action
            cur.execute(
                "INSERT INTO node_logs (node_source, action, details) VALUES (%s, %s, %s);",
                (NODE_NAME, "CREATE_SESSION", f"Created session {sid} with token {token_clean}")
            )
            conn.commit()
            return {"message": "Session created", "id": sid, "token": token_clean, "expires_at": expires.isoformat()}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create session: {str(e)}")

@app.put("/api/sessions/{session_id}/toggle")
def toggle_session(session_id: int):
    conn = next(get_db())
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE sessions SET is_active = NOT is_active WHERE id = %s RETURNING is_active;", (session_id,))
            res = cur.fetchone()
            if not res:
                raise HTTPException(status_code=404, detail="Session not found")
            conn.commit()
            return {"session_id": session_id, "is_active": res[0]}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/sessions/{session_id}")
def get_session_detail(session_id: int):
    conn = next(get_db())
    with conn.cursor() as cur:
        cur.execute("""
            SELECT s.id, s.title, s.token, s.is_active, s.expires_at, c.code, c.name
            FROM sessions s JOIN courses c ON s.course_id = c.id
            WHERE s.id = %s;
        """, (session_id,))
        s_row = cur.fetchone()
        if not s_row:
            raise HTTPException(status_code=404, detail="Session not found")
        
        cur.execute("""
            SELECT id, nim, student_name, status, client_ip, processed_by_node, created_at
            FROM attendances WHERE session_id = %s ORDER BY created_at DESC;
        """, (session_id,))
        a_rows = cur.fetchall()

        return {
            "session": {
                "id": s_row[0],
                "title": s_row[1],
                "token": s_row[2],
                "is_active": s_row[3],
                "expires_at": s_row[4].isoformat() if s_row[4] else None,
                "course_code": s_row[5],
                "course_name": s_row[6]
            },
            "attendances": [
                {
                    "id": a[0],
                    "nim": a[1],
                    "name": a[2],
                    "status": a[3],
                    "client_ip": a[4],
                    "node": a[5],
                    "time": a[6].isoformat()
                }
                for a in a_rows
            ]
        }

@app.post("/api/attend")
def submit_attendance(att: AttendanceSubmit, request: Request):
    conn = next(get_db())
    token_clean = att.token.strip().upper()
    nim_clean = att.nim.strip()
    client_host = request.client.host if request.client else "unknown"

    try:
        with conn.cursor() as cur:
            # 1. Validate Session & Token
            cur.execute(
                """
                SELECT id, title, is_active, expires_at 
                FROM sessions 
                WHERE token = %s;
                """, 
                (token_clean,)
            )
            sess = cur.fetchone()
            if not sess:
                raise HTTPException(status_code=404, detail="Token absensi tidak valid / tidak ditemukan!")
            
            sess_id, sess_title, is_active, expires_at = sess
            if not is_active:
                raise HTTPException(status_code=400, detail="Sesi absensi ini sudah ditutup oleh dosen!")
            
            if expires_at and expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=400, detail="Sesi absensi ini sudah kedaluwarsa (waktu habis)!")

            # 2. Check for duplicate attendance (Idempotency)
            cur.execute(
                "SELECT id FROM attendances WHERE session_id = %s AND nim = %s;",
                (sess_id, nim_clean)
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail=f"NIM {nim_clean} sudah tercatat hadir pada sesi ini sebelumnya!")

            # 3. Insert Attendance
            cur.execute(
                """
                INSERT INTO attendances (session_id, nim, student_name, status, client_ip, processed_by_node)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, created_at;
                """,
                (sess_id, nim_clean, att.student_name.strip(), att.status, client_host, NODE_NAME)
            )
            att_id, created_at = cur.fetchone()

            # 4. Log distributed transaction
            cur.execute(
                """
                INSERT INTO node_logs (node_source, action, details)
                VALUES (%s, %s, %s);
                """,
                (NODE_NAME, "RECORD_ATTENDANCE", f"NIM {nim_clean} recorded for session {sess_id} via {client_host}")
            )

            conn.commit()
            return {
                "success": True,
                "message": f"Presensi berhasil dicatat untuk {att.student_name} (NIM: {nim_clean})!",
                "attendance_id": att_id,
                "session_title": sess_title,
                "processed_by": NODE_NAME,
                "recorded_at": created_at.isoformat()
            }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/api/students")
def get_students():
    conn = next(get_db())
    with conn.cursor() as cur:
        cur.execute("SELECT id, nim, name, major FROM students ORDER BY nim;")
        rows = cur.fetchall()
        return [{"id": r[0], "nim": r[1], "name": r[2], "major": r[3]} for r in rows]

@app.post("/api/students")
def add_student(st: StudentCreate):
    conn = next(get_db())
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO students (nim, name, major) VALUES (%s, %s, %s) RETURNING id;",
                (st.nim.strip(), st.name.strip(), st.major.strip())
            )
            sid = cur.fetchone()[0]
            conn.commit()
            return {"message": "Student registered successfully", "id": sid}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/logs")
def get_logs(limit: int = 50):
    conn = next(get_db())
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, node_source, action, details, created_at 
            FROM node_logs 
            ORDER BY created_at DESC 
            LIMIT %s;
        """, (limit,))
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "node": r[1],
                "action": r[2],
                "details": r[3],
                "timestamp": r[4].isoformat()
            }
            for r in rows
        ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
