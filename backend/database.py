import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DB_PATH = os.path.join(os.path.dirname(__file__), "surveillance.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'operator',
            status TEXT DEFAULT 'Active',
            last_active TEXT DEFAULT 'Just now'
        )
    ''')

    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT,
            event_type TEXT NOT NULL,
            risk_score REAL NOT NULL,
            risk_level TEXT DEFAULT 'low',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            camera_id TEXT,
            location TEXT DEFAULT 'Main Entrance',
            status TEXT DEFAULT 'Active'
        )
    ''')

    # Create incidents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            event_type TEXT,
            location TEXT DEFAULT 'Main Entrance',
            risk_level TEXT DEFAULT 'low',
            status TEXT DEFAULT 'open',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        )
    ''')
    
    # Seed default data if tables are empty
    _seed_data(cursor)

    conn.commit()
    conn.close()

def _seed_data(cursor):
    from werkzeug.security import generate_password_hash

    # Seed users
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        users = [
            ("admin", generate_password_hash("admin"), "admin", "Active", "5 min ago"),
            ("operator1", generate_password_hash("operator1"), "security", "Active", "12 min ago"),
            ("viewer1", generate_password_hash("viewer1"), "viewer", "Active", "1 hour ago"),
        ]
        cursor.executemany(
            'INSERT INTO users (username, password_hash, role, status, last_active) VALUES (?, ?, ?, ?, ?)',
            users
        )

    # Seed alerts
    cursor.execute('SELECT COUNT(*) FROM alerts')
    if cursor.fetchone()[0] == 0:
        alerts = [
            ("P-001", "Suspicious Behavior", 0.73, "medium", "2026-03-05 14:11:30", "CAM-01", "Main Entrance", "Active"),
            ("P-002", "Loitering Detected",  0.55, "medium", "2026-03-05 14:05:18", "CAM-01", "Main Entrance", "Under Review"),
            ("P-003", "Motion Detected",     0.20, "low",    "2026-03-05 13:58:22", "CAM-01", "Main Entrance", "Resolved"),
            ("P-004", "Person Detected",     0.15, "low",    "2026-03-05 14:18:45", "CAM-01", "Main Entrance", "Resolved"),
            ("P-005", "Motion Detected",     0.10, "low",    "2026-03-05 14:23:12", "CAM-01", "Main Entrance", "Resolved"),
        ]
        cursor.executemany(
            'INSERT INTO alerts (person_id, event_type, risk_score, risk_level, timestamp, camera_id, location, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            alerts
        )

    # Seed incidents
    cursor.execute('SELECT COUNT(*) FROM incidents')
    if cursor.fetchone()[0] == 0:
        incidents = [
            ("Unauthorized Access",  "Unauthorized person detected at main entrance", "Unauthorized Access",  "Main Entrance", "high",   "Resolved",      "2026-03-05 14:23:45", None),
            ("Suspicious Behavior",  "Unusual movement pattern in monitored zone",    "Suspicious Behavior",  "Main Entrance", "medium", "Under Review",  "2026-03-05 13:15:22", None),
            ("Loitering Detected",   "Person stayed in restricted area too long",     "Loitering Detected",   "Main Entrance", "medium", "Resolved",      "2026-03-05 12:08:11", None),
            ("Motion Detected",      "Motion detected during monitoring",             "Motion Detected",      "Main Entrance", "low",    "Resolved",      "2026-03-05 10:45:33", None),
            ("Person Detected",      "Person detected at entrance",                   "Person Detected",      "Main Entrance", "low",    "Resolved",      "2026-03-05 09:30:18", None),
            ("Motion After Hours",   "Motion detected outside operating hours",       "Motion After Hours",   "Main Entrance", "medium", "Resolved",      "2026-03-04 22:12:44", None),
            ("Suspicious Behavior",  "Suspicious activity near exit",                 "Suspicious Behavior",  "Main Entrance", "high",   "Resolved",      "2026-03-04 18:55:09", None),
            ("Aggressive Behavior",  "Aggressive movement pattern detected",          "Aggressive Behavior",  "Main Entrance", "high",   "Escalated",     "2026-03-04 16:20:55", None),
            ("Loitering Detected",   "Prolonged presence in restricted zone",         "Loitering Detected",   "Main Entrance", "medium", "False Alarm",   "2026-03-04 14:08:12", None),
            ("Person Detected",      "Person entering monitored zone",                "Person Detected",      "Main Entrance", "low",    "Resolved",      "2026-03-04 11:45:30", None),
        ]
        cursor.executemany(
            'INSERT INTO incidents (title, description, event_type, location, risk_level, status, created_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            incidents
        )

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
