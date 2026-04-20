import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("events.db")
cursor = conn.cursor()

# 1. USERS TABLE (Includes First/Last Name, Email, and the Force Password Change flag)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'host', 'student')),
    status TEXT DEFAULT 'active',
    must_change_password INTEGER DEFAULT 0
)
""")

# 2. LOCATIONS TABLE (Buildings/Zones)
cursor.execute("""
CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)
""")

# 3. VENUES TABLE (Rooms/Halls linked to Locations)
cursor.execute("""
CREATE TABLE IF NOT EXISTS venues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location_id INTEGER NOT NULL,
    capacity INTEGER,
    FOREIGN KEY (location_id) REFERENCES locations(id)
)
""")

# 4. EVENTS TABLE (Includes max_capacity for RSVP limits)
cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    venue_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    max_capacity INTEGER DEFAULT NULL,
    status TEXT DEFAULT 'scheduled',
    FOREIGN KEY (venue_id) REFERENCES venues(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
)
""")

# 5. EVENT REGISTRATIONS (For Student RSVPs)
cursor.execute("""
CREATE TABLE IF NOT EXISTS event_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(event_id, user_id) -- Prevents a student from double-booking the same event
)
""")

# 6. VENUE REQUESTS (For the Host-to-Host Negotiation Engine)
cursor.execute("""
CREATE TABLE IF NOT EXISTS venue_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requester_event_id INTEGER NOT NULL,
    target_event_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending', 
    FOREIGN KEY (requester_event_id) REFERENCES events(id),
    FOREIGN KEY (target_event_id) REFERENCES events(id)
)
""")

# ================= CREATE DEFAULT ADMIN =================
admin_email = "admin@campusevents.ac.ke"  # Using a Kenyan academic domain style!
admin_username = "admin"
admin_password = generate_password_hash("admin123")

cursor.execute("SELECT * FROM users WHERE username = ?", (admin_username,))
if not cursor.fetchone():
    cursor.execute(
        """INSERT INTO users (first_name, last_name, email, username, password, role) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("System", "Admin", admin_email, admin_username, admin_password, "admin")
    )
    print("✅ Default admin created: username=admin, password=admin123")

conn.commit()
conn.close()

print("🚀 Master Database successfully generated with all Enterprise features!")