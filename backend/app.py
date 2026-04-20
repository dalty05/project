from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt
from flask_mail import Mail, Message
import secrets
import threading  # ✨ NEW: For background tasks!

import sqlite3

from database import get_db_connection

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "super-secret-campus-events-key-2026!!" 
jwt = JWTManager(app)

# ✨ REAL EMAIL CONFIGURATION
# ✨ REAL EMAIL CONFIGURATION (Upgraded to Port 465 SSL)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465                 # <-- Changed from 587 to 465
app.config['MAIL_USE_TLS'] = False            # <-- Changed to False
app.config['MAIL_USE_SSL'] = True             # <-- Added this line (Set to True)
app.config['MAIL_USERNAME'] = 'oyigodalton@gmail.com'
app.config['MAIL_PASSWORD'] = 'rggn vymi qepv itbt'
app.config['MAIL_DEFAULT_SENDER'] = 'oyigodalton@gmail.com'
mail = Mail(app)


# ✨ THE ASYNC EMAIL ENGINE
def send_async_email(app_context, msg):
    """Sends email in the background without freezing the server"""
    with app_context:
        try:
            mail.send(msg)
            print(f"✅ Background Email successfully sent to: {msg.recipients}")
        except Exception as e:
            print(f"❌ Background Email failed: {e}")

def send_email_background(subject, recipients, body):
    """Helper function to trigger the background thread"""
    msg = Message(subject, recipients=recipients, body=body)
    # We must pass the app context to the thread so Flask-Mail works outside the main request
    app_context = app.app_context()
    thread = threading.Thread(target=send_async_email, args=(app_context, msg))
    thread.start()



# ----------------- HOME ----------------
@app.route("/")
def home():
    return jsonify({"message": "API is securely running..."})

# ----------------- LOGIN (PUBLIC) -----------------

# ----------------- LOGIN (PUBLIC) -----------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"message": "Invalid username or password"}), 401

    if user["status"] == "inactive":
        return jsonify({"message": "Your account has been deactivated. Contact Admin."}), 403

    user_info = {
        "id": user["id"],
        "username": user["username"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
        "role": user["role"],
        "must_change_password": user["must_change_password"] # ✨ NEW: Send flag to frontend
    }
    
    access_token = create_access_token(identity=str(user["username"]), additional_claims=user_info)

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": user_info
    })

# ----------------- PASSWORD RESET (EMAIL) -----------------
@app.route("/reset_password", methods=["POST"])
def reset_password():
    data = request.json
    email = data.get("email")

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({"message": "If that email exists, a reset link has been sent."}), 200 

    temp_password = secrets.token_urlsafe(6)
    hashed_password = generate_password_hash(temp_password)

    # ✨ NEW: Set must_change_password to 1 (True)
    conn.execute("UPDATE users SET password = ?, must_change_password = 1 WHERE id = ?", (hashed_password, user["id"]))
    conn.commit()
    conn.close()

    email_body = f"Hello {user['first_name']},\n\nYour password has been reset. Your temporary password is: {temp_password}\n\nPlease login. You will be required to set a new password immediately."
    send_email_background("🔒 Your Temporary Password", [email], email_body)

    return jsonify({"message": "If that email exists, a reset link has been sent."})


# ----------------- SET NEW PASSWORD (FORCE CHANGE) -----------------
@app.route("/change_password", methods=["PUT"])
@jwt_required()
def change_password():
    claims = get_jwt()
    user_id = claims.get("id")
    new_password = request.json.get("new_password")

    if not new_password:
        return jsonify({"message": "New password is required"}), 400

    hashed_password = generate_password_hash(new_password)
    
    conn = get_db_connection()
    # ✨ NEW: Update password and turn off the flag
    conn.execute("UPDATE users SET password = ?, must_change_password = 0 WHERE id = ?", (hashed_password, user_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Password updated successfully!"})


# ----------------- PUBLIC REGISTRATION (STUDENTS) -----------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")

    if not all([first_name, last_name, email, username, password]):
        return jsonify({"message": "All fields are required"}), 400

    hashed_password = generate_password_hash(password)
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (first_name, last_name, email, username, password, role) VALUES (?, ?, ?, ?, ?, ?)",
            (first_name, last_name, email, username, hashed_password, "student")
        )
        conn.commit()
        
        # ✨ SEND WELCOME EMAIL
        try:
            msg = Message(f"Welcome to Campus Events, {first_name}!", recipients=[email])
            msg.body = f"Hello {first_name} {last_name},\n\nYour student account has been created successfully. You can now login and RSVP for events!"
            mail.send(msg)
        except Exception as e:
            print("Email failed to send, but account was created. Check mail config.")

    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"message": "Username or Email already exists"}), 400

    conn.close()
    return jsonify({"message": "Registration successful! Welcome email sent."})




# ----------------- ADMIN ROUTES -----------------


# ----------------- ADMIN: HOST MANAGEMENT -----------------
@app.route("/create_host", methods=["POST"])
@jwt_required()
def create_host():
    claims = get_jwt() 
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin privileges required"}), 403

    data = request.json

    # 1. Safety Check
    required_fields = ["first_name", "last_name", "email", "username", "password"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"message": f"Missing required field: {field}"}), 400

    hashed_password = generate_password_hash(data.get("password"))
    
    # ✨ NEW: Check if the admin selected 'admin' or 'host'. Default to 'host'.
    new_role = data.get("role", "host")

    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (first_name, last_name, email, username, password, role) VALUES (?, ?, ?, ?, ?, ?)",
            (data.get("first_name"), data.get("last_name"), data.get("email"), data.get("username"), hashed_password, new_role)
        )
        conn.commit()
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        conn.close()
        return jsonify({"message": "Username or Email already exists"}), 400

    conn.close()
    return jsonify({"message": f"{new_role.capitalize()} created successfully"})

@app.route("/update_host/<int:id>", methods=["PUT"])
@jwt_required()
def update_host(id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin privileges required"}), 403

    data = request.json
    conn = get_db_connection()
    
    try:
        if data.get("password"):
            hashed = generate_password_hash(data.get("password"))
            conn.execute(
                "UPDATE users SET first_name=?, last_name=?, email=?, username=?, password=? WHERE id=?", 
                (data.get("first_name"), data.get("last_name"), data.get("email"), data.get("username"), hashed, id)
            )
        else:
            conn.execute(
                "UPDATE users SET first_name=?, last_name=?, email=?, username=? WHERE id=?", 
                (data.get("first_name"), data.get("last_name"), data.get("email"), data.get("username"), id)
            )
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"message": "Username or Email already taken"}), 400

    conn.close()
    return jsonify({"message": "Host updated successfully"})

@app.route("/hosts", methods=["GET"])
@jwt_required()
def get_hosts():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin privileges required"}), 403

    conn = get_db_connection()
    # ✨ FIX: We now select the 'role' column AND fetch both 'host' and 'admin' accounts!
    hosts = conn.execute("""
        SELECT id, first_name, last_name, email, username, role, status 
        FROM users 
        WHERE role IN ('host', 'admin')
    """).fetchall()
    conn.close()
    
    return jsonify([dict(h) for h in hosts])





@app.route("/toggle_host/<int:id>", methods=["PUT"])
@jwt_required()
def toggle_host(id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin privileges required"}), 403

    conn = get_db_connection()
    user = conn.execute("SELECT status FROM users WHERE id=?", (id,)).fetchone()
    
    if not user:
        conn.close()
        return jsonify({"message": "Host not found"}), 404

    # Toggle the status
    new_status = "inactive" if user["status"] == "active" else "active"
    conn.execute("UPDATE users SET status=? WHERE id=?", (new_status, id))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Host successfully marked as {new_status}"})












# ----------------- HOST ROUTES -----------------
# ----------------- HOST ROUTES (Upgraded Conflict Detector) -----------------
@app.route("/create_event", methods=["POST"])
@jwt_required()
def create_event():
    claims = get_jwt()
    if claims.get("role") != "host":
        return jsonify({"message": "Host privileges required"}), 403

    data = request.json
    host_id = claims.get("id") 
    conn = get_db_connection()

    # ✨ UPGRADED CONFLICT DETECTOR: Now checks for 'scheduled' or 'Ongoing' events
    conflict = conn.execute("""
        SELECT e.id, e.title, e.start_time, e.end_time, u.first_name, u.last_name 
        FROM events e
        JOIN users u ON e.created_by = u.id
        WHERE e.venue_id = ? AND e.date = ? AND e.status = 'scheduled'
        AND (? < e.end_time AND ? > e.start_time)
    """, (data.get("venue_id"), data.get("date"), data.get("start_time"), data.get("end_time"))).fetchone()

    if conflict:
        conn.close()
        error_msg = f"Room is booked for '{conflict['title']}' by {conflict['first_name']} {conflict['last_name']} ({conflict['start_time']} - {conflict['end_time']})."
        # ✨ Return the blocking_event_id so the frontend can request a swap!
        return jsonify({"message": error_msg, "blocking_event_id": conflict["id"]}), 400

    conn.execute("""
        INSERT INTO events (title, venue_id, date, start_time, end_time, created_by, max_capacity, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'scheduled')
    """, (data.get("title"), data.get("venue_id"), data.get("date"), data.get("start_time"), data.get("end_time"), host_id, data.get("max_capacity")))

    conn.commit()
    conn.close()
    return jsonify({"message": "Event created successfully"})

@app.route("/update_event/<int:id>", methods=["PUT"])
@jwt_required()
def update_event(id):
    claims = get_jwt()
    if claims.get("role") != "host":
        return jsonify({"message": "Host privileges required"}), 403

    data = request.json
    conn = get_db_connection()

    conflict = conn.execute("""
        SELECT e.title, e.start_time, e.end_time, u.first_name, u.last_name 
        FROM events e
        JOIN users u ON e.created_by = u.id
        WHERE e.venue_id = ? AND e.date = ? AND e.id != ? AND e.status = 'scheduled'
        AND (? < e.end_time AND ? > e.start_time)
    """, (data.get("venue_id"), data.get("date"), id, data.get("start_time"), data.get("end_time"))).fetchone()

    if conflict:
        conn.close()
        error_msg = f"Room is booked for '{conflict['title']}' by {conflict['first_name']} {conflict['last_name']}."
        return jsonify({"message": error_msg}), 400

    conn.execute("""
        UPDATE events SET title=?, date=?, start_time=?, end_time=?, venue_id=?, max_capacity=?, status='scheduled' WHERE id=?
    """, (data.get("title"), data.get("date"), data.get("start_time"), data.get("end_time"), data.get("venue_id"), data.get("max_capacity"), id))

    # ✨ NEW: FETCH ATTENDEES BEFORE CLOSING CONNECTION
    attendees = conn.execute("""
        SELECT u.email, u.first_name 
        FROM event_registrations er
        JOIN users u ON er.user_id = u.id
        WHERE er.event_id = ?
    """, (id,)).fetchall()

    conn.commit()
    conn.close()

    # ✨ NEW: FIRE OFF INDIVIDUAL BACKGROUND EMAILS
    if attendees:
        for attendee in attendees:
            email_body = f"Hello {attendee['first_name']},\n\nAn update has been made to the event '{data.get('title')}' that you RSVP'd for.\n\nPlease log into the Campus Events dashboard to check the latest time, date, and venue details."
            send_email_background(f"⚠️ Event Update: {data.get('title')}", [attendee["email"]], email_body)

    return jsonify({"message": "Event updated successfully and attendees notified!"})

# ----------------- VIEW ATTENDEES -----------------
@app.route("/event_attendees/<int:event_id>", methods=["GET"])
@jwt_required()
def get_event_attendees(event_id):
    claims = get_jwt()
    if claims.get("role") not in ["host", "admin"]:
        return jsonify({"message": "Unauthorized"}), 403
    
    conn = get_db_connection()
    attendees = conn.execute("""
        SELECT u.first_name, u.last_name, u.email, er.registration_date 
        FROM event_registrations er
        JOIN users u ON er.user_id = u.id
        WHERE er.event_id = ?
        ORDER BY er.registration_date DESC
    """, (event_id,)).fetchall()
    conn.close()
 
    return jsonify([dict(a) for a in attendees])


# ----------------- VENUE NEGOTIATION ENGINE (NEW!) -----------------
@app.route("/request_swap", methods=["POST"])
@jwt_required()
def request_swap():
    claims = get_jwt()
    data = request.json
    host_id = claims.get("id")
    conn = get_db_connection()

    # 1. Create the new event but set status to 'pending_request'
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (title, venue_id, date, start_time, end_time, created_by, max_capacity, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_request')
    """, (data.get("title"), data.get("venue_id"), data.get("date"), data.get("start_time"), data.get("end_time"), host_id, data.get("max_capacity")))
    
    new_event_id = cursor.lastrowid # Get the ID of the event we just created

    # 2. Log the request in venue_requests table
    cursor.execute("""
        INSERT INTO venue_requests (requester_event_id, target_event_id, status)
        VALUES (?, ?, 'pending')
    """, (new_event_id, data.get("blocking_event_id")))

    conn.commit()
    conn.close()
    return jsonify({"message": "Swap request sent to the current host!"})

@app.route("/inbox", methods=["GET"])
@jwt_required()
def get_inbox():
    claims = get_jwt()
    host_id = claims.get("id")
    conn = get_db_connection()

    # Fetch all pending requests where THIS host owns the target event
    requests = conn.execute("""
        SELECT 
            vr.id as request_id,
            req_e.title as req_title, req_e.date as req_date, req_e.start_time as req_start, req_e.end_time as req_end,
            req_u.first_name as req_first, req_u.last_name as req_last, req_u.email as req_email,
            tgt_e.title as tgt_title, tgt_e.id as tgt_event_id
        FROM venue_requests vr
        JOIN events req_e ON vr.requester_event_id = req_e.id
        JOIN users req_u ON req_e.created_by = req_u.id
        JOIN events tgt_e ON vr.target_event_id = tgt_e.id
        WHERE tgt_e.created_by = ? AND vr.status = 'pending'
    """, (host_id,)).fetchall()
    
    conn.close()
    return jsonify([dict(r) for r in requests])





@app.route("/respond_swap/<int:request_id>", methods=["POST"])
@jwt_required()
def respond_swap(request_id):
    action = request.json.get("action") # 'approve' or 'reject'
    conn = get_db_connection()

    # ✨ UPGRADE: We now JOIN the users and events tables so we can get the Requester's Email and Event Title!
    req = conn.execute("""
        SELECT vr.*, 
               req_u.email as req_email, req_u.first_name as req_first, req_e.title as req_title,
               tgt_u.first_name as tgt_first, tgt_e.title as tgt_title
        FROM venue_requests vr
        JOIN events req_e ON vr.requester_event_id = req_e.id
        JOIN users req_u ON req_e.created_by = req_u.id
        JOIN events tgt_e ON vr.target_event_id = tgt_e.id
        JOIN users tgt_u ON tgt_e.created_by = tgt_u.id
        WHERE vr.id = ?
    """, (request_id,)).fetchone()

    if not req:
        conn.close()
        return jsonify({"message": "Request not found"}), 404

    if action == "approve":
        conn.execute("UPDATE events SET status = 'scheduled' WHERE id = ?", (req["requester_event_id"],))
        conn.execute("UPDATE events SET status = 'needs_rescheduling' WHERE id = ?", (req["target_event_id"],))
        conn.execute("UPDATE venue_requests SET status = 'approved' WHERE id = ?", (request_id,))
        msg_text = "Request approved. Please pick a new time/venue for your event."
        
        # ✨ SEND BACKGROUND EMAIL (Instant UX!)
        email_body = f"Hello {req['req_first']},\n\nGreat news! {req['tgt_first']} has approved your room swap request for your event '{req['req_title']}'.\n\nThe room is now officially yours. You can view it in your Host Dashboard."
        send_email_background(f"✅ Swap Approved: {req['req_title']}", [req['req_email']], email_body)

    else:
        conn.execute("UPDATE events SET status = 'cancelled' WHERE id = ?", (req["requester_event_id"],))
        conn.execute("UPDATE venue_requests SET status = 'rejected' WHERE id = ?", (request_id,))
        msg_text = "Request rejected."
        
        # ✨ SEND BACKGROUND EMAIL (Instant UX!)
        email_body = f"Hello {req['req_first']},\n\nUnfortunately, {req['tgt_first']} has declined your room swap request for your event '{req['req_title']}'.\n\nYour event request has been cancelled. Please log in and create a new event at a different time or venue."
        send_email_background(f"❌ Swap Rejected: {req['req_title']}", [req['req_email']], email_body)

    conn.commit()
    conn.close()
    return jsonify({"message": msg_text})








@app.route("/cancel_event/<int:id>", methods=["PUT"])
@jwt_required()
def cancel_event(id):
    claims = get_jwt()
    conn = get_db_connection()

    # Get the event details first
    event = conn.execute("SELECT * FROM events WHERE id=? AND created_by=?", (id, claims.get("id"))).fetchone()
    if not event:
        conn.close()
        return jsonify({"message": "Not authorized to cancel this event"}), 403

    # ✨ NEW: Fetch all enrolled students before cancelling
    attendees = conn.execute("""
        SELECT u.email, u.first_name 
        FROM event_registrations er
        JOIN users u ON er.user_id = u.id
        WHERE er.event_id = ?
    """, (id,)).fetchall()

    conn.execute("UPDATE events SET status='cancelled' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    # ✨ NEW: Fire off cancellation emails in the background
    if attendees:
        for attendee in attendees:
            email_body = f"Hello {attendee['first_name']},\n\nWe regret to inform you that the event '{event['title']}' scheduled on {event['date']} has been cancelled by the host.\n\nWe apologize for any inconvenience."
            send_email_background(f"🚫 Event Cancelled: {event['title']}", [attendee["email"]], email_body)

    return jsonify({"message": "Event cancelled successfully. Attendees have been notified!"})










# ----------------- PUBLIC ROUTES -----------------


# ----------------- ADMIN: LOCATION & VENUE MANAGEMENT -----------------
@app.route("/add_location", methods=["POST"])
@jwt_required()
def add_location():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin privileges required"}), 403

    name = request.json.get("name")
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO locations (name) VALUES (?)", (name,))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"message": "Location already exists"}), 400

    conn.close()
    return jsonify({"message": "Location added successfully"})

@app.route("/add_venue", methods=["POST"])
@jwt_required()
def add_venue():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin privileges required"}), 403

    data = request.json
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO venues (name, location_id, capacity) VALUES (?, ?, ?)",
            (data.get("name"), data.get("location_id"), data.get("capacity"))
        )
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"message": "Error adding venue or venue already exists"}), 400

    conn.close()
    return jsonify({"message": "Venue added successfully"})


# ----------------- STUDENT: RSVP SYSTEM -----------------
@app.route("/rsvp/<int:event_id>", methods=["POST"])
@jwt_required()
def rsvp_event(event_id):
    claims = get_jwt()
    if claims.get("role") != "student":
        return jsonify({"message": "Only students can RSVP for events."}), 403

    user_id = claims.get("id")
    conn = get_db_connection()

    # Check capacity limits
    event = conn.execute("SELECT max_capacity FROM events WHERE id = ?", (event_id,)).fetchone()
    if not event:
        conn.close()
        return jsonify({"message": "Event not found"}), 404

    current_rsvps = conn.execute("SELECT COUNT(*) FROM event_registrations WHERE event_id = ?", (event_id,)).fetchone()[0]
    
    if event["max_capacity"] and current_rsvps >= event["max_capacity"]:
        conn.close()
        return jsonify({"message": "Sorry, this event is Sold Out!"}), 400

    # Attempt to register
    try:
        conn.execute("INSERT INTO event_registrations (event_id, user_id) VALUES (?, ?)", (event_id, user_id))
        conn.commit()
    except Exception as e: # Catch UNIQUE constraint failure
        conn.close()
        return jsonify({"message": "You are already registered for this event!"}), 400

    conn.close()
    return jsonify({"message": "RSVP successful! See you there."})






# ----------------- PUBLIC ROUTES -----------------
@app.route("/locations", methods=["GET"])
def get_locations():
    conn = get_db_connection()
    locations = conn.execute("SELECT * FROM locations").fetchall()
    conn.close()
    return jsonify([dict(l) for l in locations])

@app.route("/venues", methods=["GET"])
def get_venues():
    conn = get_db_connection()
    # ✨ NEW: JOIN locations so the frontend gets the Location Name, not just the ID!
    venues = conn.execute("""
        SELECT v.id, v.name, v.capacity, v.location_id, l.name as location 
        FROM venues v
        JOIN locations l ON v.location_id = l.id
    """).fetchall()
    conn.close()
    return jsonify([dict(v) for v in venues])





@app.route("/events", methods=["GET"])
def get_all_events_route():
    conn = get_db_connection()
    # ✨ NEW: We use a subquery to count the exact number of RSVPs!
    events = conn.execute("""
        SELECT 
            e.id, e.title, e.date, e.start_time, e.end_time, e.max_capacity,
            e.venue_id, e.created_by, e.status,
            v.name as venue, l.name as location, u.username as host, u.first_name, u.last_name,
            (SELECT COUNT(*) FROM event_registrations er WHERE er.event_id = e.id) as rsvp_count
        FROM events e
        JOIN venues v ON e.venue_id = v.id
        JOIN locations l ON v.location_id = l.id
        JOIN users u ON e.created_by = u.id
        ORDER BY e.date ASC, e.start_time ASC
    """).fetchall()
    conn.close()
    return jsonify([dict(e) for e in events])

@app.route("/my_rsvps", methods=["GET"])
@jwt_required()
def get_my_rsvps():
    claims = get_jwt()
    user_id = claims.get("id")
    
    conn = get_db_connection()
    # Fetch all events this specific user registered for
    events = conn.execute("""
        SELECT 
            e.id, e.title, e.date, e.start_time, e.end_time, e.status,
            v.name as venue, l.name as location, u.first_name, u.last_name
        FROM event_registrations er
        JOIN events e ON er.event_id = e.id
        JOIN venues v ON e.venue_id = v.id
        JOIN locations l ON v.location_id = l.id
        JOIN users u ON e.created_by = u.id
        WHERE er.user_id = ?
        ORDER BY e.date DESC, e.start_time DESC
    """, (user_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(e) for e in events])





# ----------------- USER PROFILE MANAGEMENT -----------------
@app.route("/update_profile", methods=["PUT"])
@jwt_required()
def update_profile():
    claims = get_jwt()
    user_id = claims.get("id")
    data = request.json
    conn = get_db_connection()
    
    try:
        # If they typed a new password, hash it and update everything
        if data.get("new_password"):
            hashed = generate_password_hash(data.get("new_password"))
            conn.execute("""
                UPDATE users SET first_name=?, last_name=?, email=?, username=?, password=? WHERE id=?
            """, (data.get("first_name"), data.get("last_name"), data.get("email"), data.get("username"), hashed, user_id))
        else:
            # Otherwise, just update their text details
            conn.execute("""
                UPDATE users SET first_name=?, last_name=?, email=?, username=? WHERE id=?
            """, (data.get("first_name"), data.get("last_name"), data.get("email"), data.get("username"), user_id))
        
        conn.commit()
        
        # Fetch the freshly updated user to return to the frontend
        updated_user = conn.execute(
            "SELECT id, username, first_name, last_name, email, role, must_change_password FROM users WHERE id=?", 
            (user_id,)
        ).fetchone()
        conn.close()
        
        return jsonify({
            "message": "Profile updated successfully!", 
            "user": dict(updated_user)
        })
        
    except Exception as e:
        conn.close()
        return jsonify({"message": "Username or Email is already taken by someone else."}), 400















# ----------------- RUN APP -----------------
if __name__ == "__main__":
    app.run(debug=True)