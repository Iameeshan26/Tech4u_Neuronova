import sqlite3
import json
import os
import time

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "neuronova.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Jobs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            status TEXT,
            city TEXT,
            payload TEXT,
            result TEXT,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Internal Distance Matrix (IDM) Table
    # Using a simple (lat1, lon1, lat2, lon2) key or a zone hash
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS idm (
            zone_from TEXT,
            zone_to TEXT,
            distance REAL,
            travel_time REAL,
            weather TEXT,
            timestamp INTEGER,
            PRIMARY KEY (zone_from, zone_to, weather)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_zone_key(lat, lon):
    """
    Simple 0.01 degree zone (approx 1km)
    """
    return f"{round(lat, 2)},{round(lon, 2)}"

def add_job(job_id, city, locations):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jobs (id, status, city, payload) VALUES (?, ?, ?, ?)",
        (job_id, "queued", city, json.dumps(locations))
    )
    conn.commit()
    conn.close()

def get_next_job():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, city, payload FROM jobs WHERE status = 'queued' ORDER BY created_at LIMIT 1")
    row = cursor.fetchone()
    if row:
        job_id = row[0]
        cursor.execute("UPDATE jobs SET status = 'processing', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (job_id,))
        conn.commit()
    conn.close()
    return row

def update_job_status(job_id, status, result=None, error=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if result:
        cursor.execute("UPDATE jobs SET status = ?, result = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, json.dumps(result), job_id))
    elif error:
        cursor.execute("UPDATE jobs SET status = ?, error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, error, job_id))
    else:
        cursor.execute("UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, job_id))
    conn.commit()
    conn.close()

def get_job(job_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status, result, error FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"status": row[0], "result": json.loads(row[1]) if row[1] else None, "error": row[2]}
    return None

def get_cached_matrix_row(from_zone, to_zones, weather):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Simplified lookup
    results = {}
    for tz in to_zones:
        cursor.execute(
            "SELECT distance, travel_time FROM idm WHERE zone_from = ? AND zone_to = ? AND weather = ? AND timestamp > ?",
            (from_zone, tz, weather, int(time.time()) - 86400) # 24h TTL
        )
        row = cursor.fetchone()
        if row:
            results[tz] = row
    conn.close()
    return results

def save_idm_entry(from_lat, from_lon, to_lat, to_lon, dist, time_val, weather):
    zone_f = get_zone_key(from_lat, from_lon)
    zone_t = get_zone_key(to_lat, to_lon)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO idm (zone_from, zone_to, distance, travel_time, weather, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (zone_f, zone_t, dist, time_val, weather, int(time.time()))
    )
    conn.commit()
    conn.close()

init_db()
