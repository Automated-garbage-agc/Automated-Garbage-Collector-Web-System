from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime

DB_NAME = "agc_system.db"



app = Flask(__name__)
CORS(app)  # allow calls from HTML/JS frontend
init_default_users()


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_default_users():
    """
    Insert one admin and one resident if users table is empty.
    This is just for testing/demo.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM users")
    row = cur.fetchone()
    if row["cnt"] == 0:
        # default admin
        cur.execute("""
            INSERT INTO users (name, house_number, username, password, role)
            VALUES (?, ?, ?, ?, ?)
        """, ("Admin User", "-", "admin", "admin123", "admin"))
        # default resident
        cur.execute("""
            INSERT INTO users (name, house_number, username, password, role)
            VALUES (?, ?, ?, ?, ?)
        """, ("Resident One", "H-101", "user1", "user123", "resident"))
        conn.commit()
        print("Inserted default admin and resident users.")
    conn.close()


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "AGC API is running"}), 200


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, name, house_number, role
        FROM users
        WHERE username = ? AND password = ?
    """, (username, password))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

    user = {
        "user_id": row["user_id"],
        "name": row["name"],
        "house_number": row["house_number"],
        "role": row["role"]
    }

    return jsonify({"success": True, "user": user}), 200


@app.route("/api/request-pickup", methods=["POST"])
def request_pickup():
    data = request.json
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"success": False, "message": "user_id is required"}), 400

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pickup_requests (user_id, timestamp, status)
        VALUES (?, ?, 'PENDING')
    """, (user_id, ts))
    conn.commit()
    request_id = cur.lastrowid
    conn.close()

    return jsonify({
        "success": True,
        "message": "Pickup request created",
        "request_id": request_id,
        "timestamp": ts,
        "status": "PENDING"
    }), 201


@app.route("/api/my-requests", methods=["GET"])
def my_requests():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "user_id is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT request_id, timestamp, status
        FROM pickup_requests
        WHERE user_id = ?
        ORDER BY request_id DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()

    requests_list = []
    for r in rows:
        requests_list.append({
            "request_id": r["request_id"],
            "timestamp": r["timestamp"],
            "status": r["status"]
        })

    return jsonify({"success": True, "requests": requests_list}), 200


@app.route("/api/all-requests", methods=["GET"])
def all_requests():
    """
    Admin view: see all pickup requests.
    (In real app, you'd check if user is admin, but for fresher level we keep it simple.)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT pr.request_id, pr.timestamp, pr.status,
               u.name, u.house_number
        FROM pickup_requests pr
        JOIN users u ON pr.user_id = u.user_id
        ORDER BY pr.request_id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    requests_list = []
    for r in rows:
        requests_list.append({
            "request_id": r["request_id"],
            "timestamp": r["timestamp"],
            "status": r["status"],
            "resident_name": r["name"],
            "house_number": r["house_number"]
        })

    return jsonify({"success": True, "requests": requests_list}), 200


@app.route("/api/waste-logs", methods=["GET"])
def waste_logs():
    """
    Admin/monitor view: show what was collected (for now, demo only).
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT wl.log_id, wl.waste_type, wl.timestamp,
               pr.request_id, u.name, u.house_number
        FROM waste_logs wl
        LEFT JOIN pickup_requests pr ON wl.request_id = pr.request_id
        LEFT JOIN users u ON pr.user_id = u.user_id
        ORDER BY wl.log_id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    logs = []
    for r in rows:
        logs.append({
            "log_id": r["log_id"],
            "waste_type": r["waste_type"],
            "timestamp": r["timestamp"],
            "request_id": r["request_id"],
            "resident_name": r["name"],
            "house_number": r["house_number"]
        })

    return jsonify({"success": True, "logs": logs}), 200
@app.route("/api/update-status", methods=["POST"])
def update_status():
    data = request.json
    request_id = data.get("request_id")
    new_status = data.get("status")

    if not request_id or not new_status:
        return jsonify({"success": False, "message": "request_id and status required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE pickup_requests SET status = ? WHERE request_id = ?
    """, (new_status, request_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Status updated successfully"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


