import sqlite3

conn = sqlite3.connect("agc_system.db")
c = conn.cursor()

# Users table (resident/admin)
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    house_number TEXT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('resident','admin')) NOT NULL
);
""")

# Pickup requests table
c.execute("""
CREATE TABLE IF NOT EXISTS pickup_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    timestamp TEXT,
    status TEXT CHECK(status IN ('PENDING','IN-PROGRESS','COMPLETED')) DEFAULT 'PENDING',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
""")

# Waste collection logs table
c.execute("""
CREATE TABLE IF NOT EXISTS waste_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER,
    waste_type TEXT,
    timestamp TEXT,
    FOREIGN KEY (request_id) REFERENCES pickup_requests(request_id)
);
""")

conn.commit()
conn.close()

print("AGC database created successfully!")
