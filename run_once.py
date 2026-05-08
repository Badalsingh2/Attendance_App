import sqlite3
import psycopg2

sqlite_conn = sqlite3.connect("payroll.db")
sqlite_cur = sqlite_conn.cursor()
DATABASE_URL = "postgresql://postgres:Lz3XtSBx6WGkh13a@db.fwwwrmkgtrskykfcucis.supabase.co:5432/postgres"

pg_conn = psycopg2.connect(DATABASE_URL)
pg_cur = pg_conn.cursor()

# Store old->new worker IDs
worker_map = {}

# Migrate workers
for row in sqlite_cur.execute(
    "SELECT id, name, daily_wage FROM workers"
).fetchall():

    old_id, name, wage = row

    pg_cur.execute("""
        INSERT INTO workers (name, daily_wage)
        VALUES (%s, %s)
        RETURNING id
    """, (name, wage))

    new_id = pg_cur.fetchone()[0]

    worker_map[old_id] = new_id

# Migrate attendance
for row in sqlite_cur.execute("""
    SELECT worker_id, date, status, hours, overtime, sunday_pay
    FROM attendance
""").fetchall():

    old_worker_id = row[0]

    if old_worker_id in worker_map:

        new_worker_id = worker_map[old_worker_id]

        pg_cur.execute("""
            INSERT INTO attendance
            (worker_id, date, status, hours, overtime, sunday_pay)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            new_worker_id,
            row[1],
            row[2],
            row[3],
            row[4],
            row[5]
        ))

# Migrate advances
for row in sqlite_cur.execute("""
    SELECT worker_id, date, amount, reason
    FROM advances
""").fetchall():

    old_worker_id = row[0]

    if old_worker_id in worker_map:

        new_worker_id = worker_map[old_worker_id]

        pg_cur.execute("""
            INSERT INTO advances
            (worker_id, date, amount, reason)
            VALUES (%s,%s,%s,%s)
        """, (
            new_worker_id,
            row[1],
            row[2],
            row[3]
        ))

pg_conn.commit()

print("Migration completed successfully!")