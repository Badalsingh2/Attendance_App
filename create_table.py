import psycopg2

DATABASE_URL = "postgresql://postgres:Lz3XtSBx6WGkh13a@db.fwwwrmkgtrskykfcucis.supabase.co:5432/postgres"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Workers table
cur.execute("""
CREATE TABLE IF NOT EXISTS workers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    daily_wage INTEGER NOT NULL
)
""")

# Attendance table
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    worker_id INTEGER,
    date DATE,
    status TEXT,
    hours FLOAT,
    overtime FLOAT,
    sunday_pay FLOAT
)
""")

# Advances table
cur.execute("""
CREATE TABLE IF NOT EXISTS advances (
    id SERIAL PRIMARY KEY,
    worker_id INTEGER,
    date DATE,
    amount FLOAT,
    reason TEXT
)
""")

conn.commit()

cur.close()
conn.close()

print("All tables created successfully!")