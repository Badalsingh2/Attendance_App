"""
Worker Attendance & Payroll Management System
Premium Edition — Streamlit + Supabase (PostgreSQL) + Pandas

WAGE LOGIC:
  daily_wage    = fixed pay for one 8-hr day
  per_hr        = daily_wage / 8  (auto-derived)
  overtime_pay  = OT_hrs × per_hr
  gross_salary  = (present_days × daily_wage) + overtime_pay
  money_given   = sunday_cash_given + advances_given + canteen_total
  net_salary    = gross_salary − money_given
"""

import streamlit as st
import psycopg2
import psycopg2.extras
import psycopg2.pool as pg_pool
import pandas as pd
from datetime import date
import calendar
import io
import hashlib

# ──────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PayRoll Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# PREMIUM CSS
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700;900&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    -webkit-font-smoothing: antialiased;
}
:root {
    --bg:         #080b10;
    --surface:    #0d1117;
    --surface2:   #141922;
    --surface3:   #1c2433;
    --border:     #1f2d3d;
    --border2:    #2a3a4f;
    --gold:       #c8963e;
    --gold-light: #e8b96a;
    --gold-dim:   #c8963e33;
    --text:       #dde4f0;
    --text-muted: #6b7a91;
    --text-faint: #3d4f62;
    --green:      #3ecf8e;
    --red:        #f05060;
    --blue:       #4a9eff;
    --orange:     #ff8c42;
    --teal:       #2eccc0;
    --radius:     10px;
    --radius-lg:  16px;
}
.stApp {
    background: var(--bg) !important;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, #1a2a1a18 0%, transparent 70%),
        radial-gradient(ellipse 60% 40% at 90% 100%, #c8963e08 0%, transparent 60%);
    color: var(--text);
}
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    padding-top: 0 !important;
}
section[data-testid="stSidebar"] > div { padding: 0 !important; }
section[data-testid="stSidebar"] * { color: var(--text) !important; }
h1 { font-family: 'Playfair Display', serif !important; font-size: 2.4rem !important;
     font-weight: 900 !important; color: var(--text) !important; letter-spacing: -1px; line-height: 1.1; }
h2 { font-family: 'Playfair Display', serif !important; font-size: 1.5rem !important;
     font-weight: 700 !important; color: var(--text) !important; }
h3 { font-family: 'IBM Plex Sans', sans-serif !important; font-size: 1rem !important;
     font-weight: 600 !important; color: var(--text-muted) !important;
     text-transform: uppercase; letter-spacing: 2px; }
[data-testid="metric-container"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-top: 2px solid var(--gold) !important;
    border-radius: var(--radius) !important;
    padding: 18px 20px !important;
    transition: border-color 0.2s, transform 0.2s;
}
[data-testid="metric-container"]:hover {
    border-color: var(--gold-light) !important;
    transform: translateY(-2px);
}
[data-testid="metric-container"] label {
    color: var(--text-muted) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.68rem !important;
    letter-spacing: 2px;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] { font-family: 'IBM Plex Mono', monospace !important; }
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
    padding: 0 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    padding: 14px 22px !important;
    transition: color 0.2s, border-color 0.2s;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text) !important; }
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: var(--gold) !important;
    border-bottom-color: var(--gold) !important;
    font-weight: 600 !important;
}
.stButton > button {
    background: linear-gradient(135deg, var(--gold) 0%, #a87430 100%) !important;
    color: #080b10 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    border: none !important;
    border-radius: var(--radius) !important;
    padding: 12px 28px !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 15px #c8963e25 !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, var(--gold-light) 0%, var(--gold) 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px #c8963e40 !important;
}
.stButton > button:active { transform: translateY(0) !important; }
.btn-danger > button {
    background: linear-gradient(135deg, #c0392b 0%, #922b21 100%) !important;
    box-shadow: 0 4px 15px #c0392b25 !important;
    color: #fff !important;
}
.btn-danger > button:hover {
    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%) !important;
    box-shadow: 0 8px 25px #c0392b40 !important;
}
div[data-testid="stForm"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 28px !important;
}
.stTextInput input, .stNumberInput input {
    background: var(--surface3) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    padding: 12px 14px !important;
    font-size: 0.92rem !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px var(--gold-dim) !important;
    outline: none !important;
}
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stDateInput label,
.stRadio label { color: var(--text-muted) !important; font-size: 0.82rem !important; margin-bottom: 4px; }
.stSelectbox div[data-baseweb="select"] > div {
    background: var(--surface3) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
}
.stSelectbox div[data-baseweb="select"] > div:focus-within {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px var(--gold-dim) !important;
}
.stDateInput input {
    background: var(--surface3) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    padding: 10px 14px !important;
}
.stRadio div[role="radiogroup"] label {
    background: var(--surface3);
    border: 1px solid var(--border2);
    border-radius: 8px;
    padding: 8px 16px !important;
    cursor: pointer;
    transition: all 0.2s;
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
}
.stRadio div[role="radiogroup"] label:has(input:checked) {
    background: var(--gold-dim) !important;
    border-color: var(--gold) !important;
    color: var(--gold) !important;
}
.stCheckbox label { color: var(--text) !important; font-size: 0.9rem !important; }
.stCheckbox span[data-baseweb="checkbox"] { border-color: var(--border2) !important; background: var(--surface3) !important; }
.stDataFrame { border: 1px solid var(--border) !important; border-radius: var(--radius-lg) !important; overflow: hidden; }
.stDataFrame thead { background: var(--surface2) !important; }
.stSuccess { background: #0d2818 !important; border-left: 4px solid var(--green) !important; border-radius: var(--radius) !important; color: #a7f3d0 !important; }
.stError   { background: #2d0a10 !important; border-left: 4px solid var(--red) !important;   border-radius: var(--radius) !important; color: #fca5a5 !important; }
.stWarning { background: #1f1508 !important; border-left: 4px solid var(--orange) !important; border-radius: var(--radius) !important; color: #fed7aa !important; }
.stInfo    { background: #0a1628 !important; border-left: 4px solid var(--blue) !important;   border-radius: var(--radius) !important; color: #bfdbfe !important; }
.pill { display: inline-block; padding: 3px 10px; border-radius: 20px;
        font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px; }
.pill-green { background: #0d2818; color: #3ecf8e; border: 1px solid #1a5c3a; }
.pill-red   { background: #2d0a10; color: #f05060; border: 1px solid #5c1a22; }
.pill-gold  { background: #1a1205; color: #c8963e; border: 1px solid #4a3010; }
.pill-blue  { background: #0a1628; color: #4a9eff; border: 1px solid #1a3a5c; }
.pill-teal  { background: #051a1a; color: #2eccc0; border: 1px solid #0a4040; }
.stat-card { background: var(--surface2); border: 1px solid var(--border);
             border-radius: var(--radius-lg); padding: 20px 24px; margin-bottom: 12px; }
.section-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: var(--gold);
                 letter-spacing: 3px; text-transform: uppercase; margin-bottom: 20px;
                 padding-bottom: 10px; border-bottom: 1px solid var(--border); }
.formula-card { background: linear-gradient(135deg, var(--surface2) 0%, #111827 100%);
                border: 1px solid var(--border); border-left: 3px solid var(--gold);
                border-radius: var(--radius); padding: 16px 20px; margin-bottom: 20px;
                font-size: 0.82rem; color: var(--text-muted); line-height: 2; }
.formula-card .hl { color: var(--gold); font-family: 'IBM Plex Mono', monospace; font-weight: 600; }
.formula-card .title { color: var(--text); font-weight: 600; font-size: 0.85rem; margin-bottom: 6px; display: block; }
.canteen-card { background: linear-gradient(135deg, #051a1a 0%, #071f1e 100%);
                border: 1px solid #0a4040; border-left: 3px solid var(--teal);
                border-radius: var(--radius); padding: 16px 20px; margin-bottom: 20px;
                font-size: 0.82rem; color: var(--text-muted); line-height: 2; }
.canteen-card .hl { color: var(--teal); font-family: 'IBM Plex Mono', monospace; font-weight: 600; }
.canteen-card .title { color: var(--text); font-weight: 600; font-size: 0.85rem; margin-bottom: 6px; display: block; }
hr { border: none; border-top: 1px solid var(--border) !important; margin: 24px 0; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold); }
@media (max-width: 768px) {
    h1 { font-size: 1.6rem !important; }
    [data-testid="metric-container"] { min-width: unset !important; }
    .stTabs [data-baseweb="tab"] { padding: 10px 12px !important; font-size: 0.62rem !important; }
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────────────────────
PASSWORD_HASH = "aef5e8c1823370dbcf46858725571f1efcd465ae44c0cb1e6cf9d74e818dc25c"
MAX_ATTEMPTS  = 5


def _check_password(entered: str) -> bool:
    return hashlib.sha256(entered.encode()).hexdigest() == PASSWORD_HASH


def _show_login_page():
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display: none !important; }
    .block-container { max-width: 460px !important; padding-top: 8vh !important; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;margin-bottom:36px'>
        <div style='font-size:3.2rem;margin-bottom:14px'>🔐</div>
        <div style='font-family:Playfair Display,serif;font-size:2.2rem;font-weight:900;
                    color:#dde4f0;letter-spacing:-0.5px'>PayRoll Pro</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;
                    color:#c8963e;letter-spacing:3px;text-transform:uppercase;
                    margin-top:6px'>Authorised Access Only</div>
    </div>
    """, unsafe_allow_html=True)
    attempts = st.session_state.get("_login_attempts", 0)
    if attempts >= MAX_ATTEMPTS:
        st.markdown("""
        <div style='background:#2d0a10;border:1px solid #5c1a22;border-radius:12px;
                    padding:24px;text-align:center'>
            <div style='font-size:2rem;margin-bottom:8px'>🔒</div>
            <div style='color:#f05060;font-family:IBM Plex Mono,monospace;font-size:0.85rem;
                        font-weight:600'>Too many failed attempts</div>
            <div style='color:#6b7a91;font-size:0.78rem;margin-top:6px'>
                Please restart the application to try again.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    with st.form("_login_form"):
        st.markdown("""
        <div style='background:#0d1117;border:1px solid #1f2d3d;border-top:2px solid #c8963e;
                    border-radius:16px;padding:32px 28px;margin-bottom:4px'>
            <div style='font-family:IBM Plex Mono,monospace;font-size:0.65rem;
                        color:#c8963e;letter-spacing:2.5px;text-transform:uppercase;
                        margin-bottom:20px'>Password Required</div>
        """, unsafe_allow_html=True)
        pwd = st.text_input("Password", type="password", placeholder="Enter your password…",
                            label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
        if attempts > 0:
            left = MAX_ATTEMPTS - attempts
            st.markdown(f"""
            <div style='text-align:center;font-family:IBM Plex Mono,monospace;
                        font-size:0.72rem;color:#f59e0b;margin-bottom:8px'>
            ⚠️ {left} attempt(s) remaining before lockout
            </div>
            """, unsafe_allow_html=True)
        submitted = st.form_submit_button("🔓  Login", use_container_width=True)
        if submitted:
            if _check_password(pwd):
                st.session_state["_authenticated"]  = True
                st.session_state["_login_attempts"] = 0
                st.rerun()
            else:
                st.session_state["_login_attempts"] = attempts + 1
                if st.session_state["_login_attempts"] < MAX_ATTEMPTS:
                    st.error("❌ Incorrect password. Please try again.")
                else:
                    st.error("🔒 Account locked. Restart the app to try again.")
    st.markdown("""
    <div style='text-align:center;margin-top:28px;font-family:IBM Plex Mono,monospace;
                font-size:0.6rem;color:#3d4f62'>
    Built with Streamlit · Supabase
    </div>
    """, unsafe_allow_html=True)


if "_authenticated"  not in st.session_state: st.session_state["_authenticated"]  = False
if "_login_attempts" not in st.session_state: st.session_state["_login_attempts"] = 0
if not st.session_state["_authenticated"]:
    _show_login_page()
    st.stop()


# ──────────────────────────────────────────────────────────────
# DATABASE — Connection Pool (reuse SSL connections across reruns)
# ──────────────────────────────────────────────────────────────
DATABASE_URL = st.secrets["DATABASE_URL"]


@st.cache_resource
def get_pool():
    """Create a persistent connection pool shared across all Streamlit reruns."""
    return pg_pool.SimpleConnectionPool(1, 10, DATABASE_URL, sslmode="require")


def get_conn():
    return get_pool().getconn()


def release_conn(conn):
    get_pool().putconn(conn)


def init_db():
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS workers (
                id         SERIAL PRIMARY KEY,
                name       TEXT   NOT NULL UNIQUE,
                daily_wage REAL   DEFAULT 400.0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id         SERIAL PRIMARY KEY,
                worker_id  INTEGER NOT NULL,
                date       DATE    NOT NULL,
                status     TEXT    NOT NULL CHECK(status IN ('Present','Absent')),
                hours      REAL    DEFAULT 8,
                overtime   REAL    DEFAULT 0,
                sunday_pay REAL    DEFAULT 0,
                UNIQUE(worker_id, date),
                FOREIGN KEY (worker_id) REFERENCES workers(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS advances (
                id        SERIAL PRIMARY KEY,
                worker_id INTEGER NOT NULL,
                date      DATE    NOT NULL,
                amount    REAL    NOT NULL,
                reason    TEXT    DEFAULT '',
                FOREIGN KEY (worker_id) REFERENCES workers(id)
            )
        """)
        # Canteen: one row per worker per day (daily total, not per-item)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS canteen (
                id        SERIAL PRIMARY KEY,
                worker_id INTEGER NOT NULL,
                date      DATE    NOT NULL,
                amount    REAL    NOT NULL,
                UNIQUE(worker_id, date),
                FOREIGN KEY (worker_id) REFERENCES workers(id)
            )
        """)
        # Migration: drop old 'item' column if it exists (safe to run repeatedly)
        cur.execute("""
            ALTER TABLE canteen DROP COLUMN IF EXISTS item;
        """)
        conn.commit()
        cur.close()
    finally:
        release_conn(conn)


# ──────────────────────────────────────────────────────────────
# WAGE HELPERS
# ──────────────────────────────────────────────────────────────

def is_sunday(d: date) -> bool:
    return d.weekday() == 6


def calc_ot_hours(hours: float, status: str) -> float:
    if status == "Absent": return 0.0
    return max(0.0, hours - 8.0)


def calc_day_salary(hours: float, status: str, daily_wage: float) -> float:
    if status == "Absent": return 0.0
    ot = calc_ot_hours(hours, status)
    return daily_wage + ot * (daily_wage / 8.0)


def enrich_attendance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["per_hr"]      = df["daily_wage"] / 8.0
    df["day_salary"]  = df.apply(lambda r: calc_day_salary(r["hours"], r["status"], r["daily_wage"]), axis=1)
    df["gross_earned"] = df["day_salary"]
    return df


# ──────────────────────────────────────────────────────────────
# WORKER CRUD
# ──────────────────────────────────────────────────────────────

def add_worker(name: str, wage: float):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO workers (name, daily_wage) VALUES (%s, %s)", (name.strip(), wage))
        conn.commit()
        cur.close()
        return True, "Worker added."
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False, "Worker name already exists."
    finally:
        release_conn(conn)


@st.cache_data(ttl=30)
def get_workers() -> pd.DataFrame:
    conn = get_conn()
    try:
        df = pd.read_sql("SELECT * FROM workers ORDER BY name", conn)
        return df
    finally:
        release_conn(conn)


def update_wage(wid: int, wage: float):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE workers SET daily_wage=%s WHERE id=%s", (wage, wid))
        conn.commit()
        cur.close()
    finally:
        release_conn(conn)


def delete_worker(wid: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM canteen    WHERE worker_id=%s", (wid,))
        cur.execute("DELETE FROM advances   WHERE worker_id=%s", (wid,))
        cur.execute("DELETE FROM attendance WHERE worker_id=%s", (wid,))
        cur.execute("DELETE FROM workers    WHERE id=%s",        (wid,))
        conn.commit()
        cur.close()
    finally:
        release_conn(conn)


# ──────────────────────────────────────────────────────────────
# ATTENDANCE CRUD
# ──────────────────────────────────────────────────────────────

def mark_attendance(wid: int, d: date, status: str, hours: float, sunday_pay: float):
    if status == "Absent": hours = 0.0
    ot   = calc_ot_hours(hours, status)
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO attendance (worker_id, date, status, hours, overtime, sunday_pay)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (worker_id, date) DO UPDATE SET
                status=EXCLUDED.status, hours=EXCLUDED.hours,
                overtime=EXCLUDED.overtime, sunday_pay=EXCLUDED.sunday_pay
        """, (wid, d.isoformat(), status, hours, ot, sunday_pay))
        conn.commit()
        cur.close()
    finally:
        release_conn(conn)


@st.cache_data(ttl=15)
def get_attendance(wid=None, start: date=None, end: date=None) -> pd.DataFrame:
    conn = get_conn()
    try:
        q = """SELECT a.id, a.worker_id, w.name, w.daily_wage,
                      a.date, a.status, a.hours, a.overtime, a.sunday_pay
               FROM attendance a JOIN workers w ON a.worker_id=w.id WHERE 1=1"""
        p = []
        if wid:   q += " AND a.worker_id=%s"; p.append(wid)
        if start: q += " AND a.date>=%s";     p.append(start.isoformat())
        if end:   q += " AND a.date<=%s";     p.append(end.isoformat())
        q += " ORDER BY a.date, w.name"
        df = pd.read_sql(q, conn, params=p)
        return df
    finally:
        release_conn(conn)


def delete_attendance(rid: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM attendance WHERE id=%s", (rid,))
        conn.commit()
        cur.close()
    finally:
        release_conn(conn)


# ──────────────────────────────────────────────────────────────
# ADVANCE CRUD
# ──────────────────────────────────────────────────────────────

def add_advance(wid: int, d: date, amount: float, reason: str):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO advances (worker_id, date, amount, reason) VALUES (%s, %s, %s, %s)",
                    (wid, d.isoformat(), amount, reason.strip()))
        conn.commit()
        cur.close()
    finally:
        release_conn(conn)


@st.cache_data(ttl=15)
def get_advances(wid=None, start: date=None, end: date=None) -> pd.DataFrame:
    conn = get_conn()
    try:
        q = """SELECT a.id, a.worker_id, w.name, a.date, a.amount, a.reason
               FROM advances a JOIN workers w ON a.worker_id=w.id WHERE 1=1"""
        p = []
        if wid:   q += " AND a.worker_id=%s"; p.append(wid)
        if start: q += " AND a.date>=%s";     p.append(start.isoformat())
        if end:   q += " AND a.date<=%s";     p.append(end.isoformat())
        q += " ORDER BY a.date DESC, w.name"
        df = pd.read_sql(q, conn, params=p)
        return df
    finally:
        release_conn(conn)


def delete_advance(aid: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM advances WHERE id=%s", (aid,))
        conn.commit()
        cur.close()
    finally:
        release_conn(conn)


def get_advance_totals(start: date=None, end: date=None) -> pd.DataFrame:
    df = get_advances(start=start, end=end)
    if df.empty: return pd.DataFrame(columns=["worker_id","name","total_advance"])
    return df.groupby(["worker_id","name"])["amount"].sum().reset_index().rename(columns={"amount":"total_advance"})


# ──────────────────────────────────────────────────────────────
# CANTEEN CRUD — Daily total per worker (no per-item tracking)
# ──────────────────────────────────────────────────────────────

def upsert_canteen(wid: int, d: date, amount: float):
    """Set (or overwrite) the daily canteen total for a worker."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO canteen (worker_id, date, amount)
            VALUES (%s, %s, %s)
            ON CONFLICT (worker_id, date) DO UPDATE SET amount = EXCLUDED.amount
        """, (wid, d.isoformat(), amount))
        conn.commit()
        cur.close()
    finally:
        release_conn(conn)


def delete_canteen_entry(cid: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM canteen WHERE id=%s", (cid,))
        conn.commit()
        cur.close()
    finally:
        release_conn(conn)


@st.cache_data(ttl=15)
def get_canteen(wid=None, start: date=None, end: date=None) -> pd.DataFrame:
    conn = get_conn()
    try:
        q = """SELECT c.id, c.worker_id, w.name, c.date, c.amount
               FROM canteen c JOIN workers w ON c.worker_id=w.id WHERE 1=1"""
        p = []
        if wid:   q += " AND c.worker_id=%s"; p.append(wid)
        if start: q += " AND c.date>=%s";     p.append(start.isoformat())
        if end:   q += " AND c.date<=%s";     p.append(end.isoformat())
        q += " ORDER BY c.date DESC, w.name"
        df = pd.read_sql(q, conn, params=p)
        return df
    finally:
        release_conn(conn)


def get_canteen_totals(start: date=None, end: date=None) -> pd.DataFrame:
    df = get_canteen(start=start, end=end)
    if df.empty: return pd.DataFrame(columns=["worker_id","name","total_canteen"])
    return df.groupby(["worker_id","name"])["amount"].sum().reset_index().rename(columns={"amount":"total_canteen"})


# ──────────────────────────────────────────────────────────────
# MONTHLY HELPERS
# ──────────────────────────────────────────────────────────────

def get_monthly_muster(year: int, month: int):
    first = date(year, month, 1)
    last  = date(year, month, calendar.monthrange(year, month)[1])
    df    = get_attendance(start=first, end=last)
    if df.empty: return pd.DataFrame(), []
    df["day"] = pd.to_datetime(df["date"]).dt.day
    pivot = df.pivot_table(index="name", columns="day", values="status", aggfunc="first").fillna("-")
    all_days = list(range(1, last.day + 1))
    for d in all_days:
        if d not in pivot.columns: pivot[d] = "-"
    return pivot[all_days], all_days


def get_monthly_summary(year: int, month: int) -> pd.DataFrame:
    first = date(year, month, 1)
    last  = date(year, month, calendar.monthrange(year, month)[1])
    df    = get_attendance(start=first, end=last)
    if df.empty: return pd.DataFrame()
    df = enrich_attendance(df)
    s  = df.groupby(["worker_id","name","daily_wage"]).agg(
        Present_Days =("status",       lambda x: (x=="Present").sum()),
        Absent_Days  =("status",       lambda x: (x=="Absent").sum()),
        Total_Hours  =("hours",        "sum"),
        Total_OT     =("overtime",     "sum"),
        Sunday_Given =("sunday_pay",   "sum"),
        Gross_Salary =("gross_earned", "sum"),
    ).reset_index()

    adv = get_advance_totals(start=first, end=last)
    if not adv.empty:
        s = s.merge(adv[["worker_id","total_advance"]], on="worker_id", how="left")
    else:
        s["total_advance"] = 0.0
    s["total_advance"] = s["total_advance"].fillna(0.0)

    cant = get_canteen_totals(start=first, end=last)
    if not cant.empty:
        s = s.merge(cant[["worker_id","total_canteen"]], on="worker_id", how="left")
    else:
        s["total_canteen"] = 0.0
    s["total_canteen"] = s["total_canteen"].fillna(0.0)

    # s["Total_Given"] = s["Sunday_Given"] + s["total_advance"] + s["total_canteen"]
    s["Total_Given"] = s["Sunday_Given"] + s["total_advance"] 
    s["Net_Pay"]     = s["Gross_Salary"] - s["Total_Given"]

    s.rename(columns={"name":"Worker","daily_wage":"Daily Wage"}, inplace=True)
    return s


# ──────────────────────────────────────────────────────────────
# MUSTER HTML RENDERER
# ──────────────────────────────────────────────────────────────

def render_muster_html(pivot_df, year, month, days) -> str:
    sundays = {d for d in range(1, calendar.monthrange(year, month)[1]+1)
               if date(year, month, d).weekday() == 6}
    h  = "<div style='overflow-x:auto;border-radius:12px;border:1px solid #1f2d3d'>"
    h += "<table style='border-collapse:collapse;width:100%;font-family:IBM Plex Mono,monospace;font-size:0.72rem'>"
    h += ("<tr><th style='background:#0d1117;padding:12px 16px;border-right:1px solid #1f2d3d;"
          "text-align:left;color:#c8963e;font-weight:600;letter-spacing:1px;white-space:nowrap;"
          "position:sticky;left:0;z-index:2'>WORKER</th>")
    for d in days:
        is_sun = d in sundays
        bg  = "#1a0d05" if is_sun else "#0d1117"
        clr = "#c8963e" if is_sun else "#3d4f62"
        day_name = date(year, month, d).strftime("%a")[0]
        h += (f"<th style='background:{bg};padding:8px 6px;border-left:1px solid #1f2d3d;"
              f"text-align:center;min-width:36px;color:{clr};font-size:0.65rem'>"
              f"<div style=\"color:{clr};font-size:0.55rem;margin-bottom:2px\">{day_name}</div>"
              f"{d}</th>")
    h += "</tr>"
    for i, (worker, row) in enumerate(pivot_df.iterrows()):
        row_bg = "#080b10" if i % 2 == 0 else "#0a0e15"
        h += (f"<tr><td style='background:#0d1117;padding:10px 16px;border-right:1px solid #1f2d3d;"
              f"border-top:1px solid #1f2d3d;color:#dde4f0;white-space:nowrap;font-weight:500;"
              f"position:sticky;left:0;z-index:1'>{worker}</td>")
        for d in days:
            is_sun = d in sundays
            val = row.get(d, "-")
            if   val == "Present": clr="#3ecf8e"; bg="#0d2818"; lbl="P"
            elif val == "Absent":  clr="#f05060"; bg="#2d0a10"; lbl="A"
            else:                  clr="#2a3a4f"; bg="#1a0d05" if is_sun else row_bg; lbl="·"
            h += (f"<td style='background:{bg};padding:8px 4px;border-left:1px solid #1f2d3d;"
                  f"border-top:1px solid #1f2d3d;text-align:center;color:{clr};"
                  f"font-weight:700;font-size:0.8rem'>{lbl}</td>")
        h += "</tr>"
    h += "</table></div>"
    return h


# ──────────────────────────────────────────────────────────────
# INIT
# ──────────────────────────────────────────────────────────────
init_db()

# ──────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#0d1117,#141922);
                border-bottom:1px solid #1f2d3d;padding:28px 24px 20px'>
        <div style='font-family:Playfair Display,serif;font-size:1.5rem;
                    font-weight:900;color:#dde4f0;letter-spacing:-0.5px'>PayRoll</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;
                    color:#c8963e;letter-spacing:3px;text-transform:uppercase;
                    margin-top:2px'>Pro Edition</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='padding:20px 20px 0'>", unsafe_allow_html=True)
    workers_df = get_workers()
    today      = date.today()
    att_month  = get_attendance(start=today.replace(day=1), end=today)
    adv_month  = get_advances(start=today.replace(day=1), end=today)
    cant_month = get_canteen(start=today.replace(day=1), end=today)

    st.markdown("""
    <div style='margin-bottom:6px;font-family:IBM Plex Mono,monospace;font-size:0.62rem;
                color:#6b7a91;letter-spacing:2px;text-transform:uppercase'>Overview</div>
    """, unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric("Workers",    len(workers_df))
    m2.metric("Att. Recs",  len(att_month))
    m3, m4 = st.columns(2)
    m3.metric("Advances",   len(adv_month))
    m4.metric("Adv. Total", f"₹{adv_month['amount'].sum():,.0f}" if not adv_month.empty else "₹0")
    m5, m6 = st.columns(2)
    m5.metric("🍽 Canteen Days",  len(cant_month))
    m6.metric("Canteen Total", f"₹{cant_month['amount'].sum():,.0f}" if not cant_month.empty else "₹0")

    st.markdown("<hr>", unsafe_allow_html=True)
    sunday_indicator = (
        "<span class='pill pill-gold'>☀ SUNDAY</span>"
        if is_sunday(today) else
        f"<span class='pill pill-blue'>{today.strftime('%A')}</span>"
    )
    st.markdown(f"""
    <div style='font-family:IBM Plex Sans,sans-serif;font-size:0.85rem;color:#6b7a91;
                margin-bottom:4px'>Today</div>
    <div style='font-family:Playfair Display,serif;font-size:1.1rem;color:#dde4f0;
                margin-bottom:8px'>{today.strftime('%d %B %Y')}</div>
    {sunday_indicator}
    """, unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div class='formula-card'>
    <span class='title'>💡 Wage Formula</span>
    <span class='hl'>Per-hr</span> = Daily Wage ÷ 8<br>
    <span class='hl'>OT Pay</span> = OT hrs × Per-hr<br>
    <span class='hl'>Gross</span> = (Days × Wage) + OT Pay<br>
    <span class='hl'>−  Sunday Cash</span> given that day<br>
    <span class='hl'>−  Advances</span> given this month<br>
    <span class='hl'>−  Canteen Bill</span> this month<br>
    <span class='hl'>= Net Pay</span> still to be paid
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🔒 Logout", use_container_width=True, key="_logout_btn"):
        st.session_state["_authenticated"]  = False
        st.session_state["_login_attempts"] = 0
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='padding:16px 24px;border-top:1px solid #1f2d3d;
                font-family:IBM Plex Mono,monospace;font-size:0.62rem;
                color:#3d4f62;text-align:center'>
    Built with Streamlit · Supabase
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# MAIN HEADER
# ──────────────────────────────────────────────────────────────
col_title, col_date = st.columns([3, 1])
with col_title:
    st.markdown("# Worker Attendance & Payroll")
    st.markdown("<div class='section-label'>Management System — Pro Edition</div>", unsafe_allow_html=True)
with col_date:
    st.markdown(f"""
    <div style='text-align:right;padding-top:12px'>
        <div style='font-family:IBM Plex Mono,monospace;font-size:0.65rem;
                    color:#6b7a91;letter-spacing:2px;text-transform:uppercase'>Today</div>
        <div style='font-family:Playfair Display,serif;font-size:1.3rem;
                    color:#dde4f0;font-weight:700'>{today.strftime('%d %b %Y')}</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:0.75rem;
                    color:#c8963e'>{today.strftime('%A')}</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "👷 Workers",
    "✅ Attendance",
    "💸 Advances",
    "🍽️ Canteen",
    "📋 Records",
    "📊 Monthly",
    "⚙️ Settings",
])


# ════════════════════════════════════════════════════════════════
# TAB 1 — WORKERS
# ════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    c_add, c_list = st.columns([1, 2], gap="large")
    with c_add:
        st.markdown("### Add Worker")
        with st.form("add_worker_form", clear_on_submit=True):
            w_name = st.text_input("Full Name", placeholder="e.g. Ramesh Kumar")
            w_wage = st.number_input("Daily Wage (₹)", min_value=1.0, value=400.0, step=50.0)
            st.markdown(f"""
            <div class='formula-card' style='margin-top:8px;font-size:0.78rem'>
            Auto-derived &nbsp;→&nbsp;
            <span class='hl'>₹{w_wage/8:.2f}/hr</span> &nbsp;·&nbsp;
            OT rate = <span class='hl'>₹{w_wage/8:.2f}/hr</span>
            </div>
            """, unsafe_allow_html=True)
            if st.form_submit_button("＋ Add Worker", use_container_width=True):
                if w_name.strip():
                    ok, msg = add_worker(w_name, w_wage)
                    if ok:
                        st.cache_data.clear()
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.warning("Please enter a name.")
    with c_list:
        st.markdown("### Worker Directory")
        workers_df = get_workers()
        if workers_df.empty:
            st.info("No workers yet. Add your first worker.")
        else:
            disp = workers_df[["id","name","daily_wage"]].copy()
            disp["Per Hr (₹)"] = (disp["daily_wage"] / 8).round(2)
            st.dataframe(disp.rename(columns={"id":"ID","name":"Name","daily_wage":"Daily Wage (₹)"}),
                         use_container_width=True, hide_index=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Remove Worker")
            st.caption("⚠️ This deletes all attendance, advances and canteen records for this worker.")
            del_wid = st.selectbox("Select", workers_df["id"].tolist(),
                                   format_func=lambda i: workers_df.loc[workers_df["id"]==i,"name"].values[0],
                                   key="del_w")
            with st.container():
                st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                if st.button("🗑 Delete Worker", key="del_w_btn", use_container_width=True):
                    delete_worker(del_wid)
                    st.cache_data.clear()
                    st.success("Deleted.")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# TAB 2 — ATTENDANCE
# ════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    workers_df = get_workers()
    if workers_df.empty:
        st.warning("No workers found. Add workers first.")
    else:
        st.markdown("### Mark Attendance")
        with st.form("att_form"):
            ca, cb = st.columns(2)
            with ca:
                sel_wid  = st.selectbox("Worker", workers_df["id"].tolist(),
                                        format_func=lambda i: workers_df.loc[workers_df["id"]==i,"name"].values[0])
                sel_date = st.date_input("Date", value=today)
            with cb:
                sel_status = st.radio("Status", ["Present","Absent"], horizontal=True)
                sel_hours  = st.number_input("Hours Worked", 0.0, 24.0, 8.0, 0.5,
                                             disabled=(sel_status=="Absent"))
            sunday_pay_given = 0.0
            if is_sunday(sel_date):
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown("""
                <div style='font-family:IBM Plex Mono,monospace;font-size:0.72rem;
                            color:#c8963e;letter-spacing:2px;margin-bottom:8px'>
                ☀️ SUNDAY DETECTED
                </div>
                """, unsafe_allow_html=True)
                give_sunday = st.checkbox("Did you give ₹1,000 cash to this worker today?", value=False)
                sunday_pay_given = 1000.0 if give_sunday else 0.0
                if give_sunday:
                    st.markdown("<span class='pill pill-gold'>₹1,000 recorded as given — will be deducted from net salary</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='pill pill-blue'>No cash given today</span>", unsafe_allow_html=True)
            wage    = float(workers_df.loc[workers_df["id"]==sel_wid,"daily_wage"].values[0])
            eff_hrs = 0.0 if sel_status=="Absent" else sel_hours
            ot_hrs  = calc_ot_hours(eff_hrs, sel_status)
            day_sal = calc_day_salary(eff_hrs, sel_status, wage)
            st.markdown("<hr>", unsafe_allow_html=True)
            p1,p2,p3,p4 = st.columns(4)
            p1.metric("Wages Earned Today", f"₹{day_sal:,.2f}")
            p2.metric("OT Hrs",             f"{ot_hrs:.1f}")
            p3.metric("OT Pay",             f"₹{ot_hrs*(wage/8):,.2f}")
            p4.metric("Sunday Cash Given",  f"₹{sunday_pay_given:,.0f}",
                      delta=f"−₹{sunday_pay_given:,.0f} from net" if sunday_pay_given > 0 else "Not given",
                      delta_color="inverse" if sunday_pay_given > 0 else "off")
            if ot_hrs > 0:
                st.info(f"⏱ Overtime: {ot_hrs:.1f} hrs × ₹{wage/8:.2f}/hr = ₹{ot_hrs*(wage/8):.2f}")
            if sunday_pay_given > 0:
                st.warning(f"💵 ₹{sunday_pay_given:,.0f} Sunday cash recorded.")
            if st.form_submit_button("💾 Save Attendance", use_container_width=True):
                hrs_save = 0.0 if sel_status=="Absent" else sel_hours
                mark_attendance(sel_wid, sel_date, sel_status, hrs_save, sunday_pay_given)
                st.cache_data.clear()
                wname = workers_df.loc[workers_df["id"]==sel_wid,"name"].values[0]
                st.success(f"✅ Saved — {wname} | {sel_date.strftime('%d %b %Y')} | {sel_status} | Earned: ₹{day_sal:,.2f}")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### Bulk Attendance — All Workers")
        bulk_date = st.date_input("Date for Bulk Entry", value=today, key="bulk_d")
        with st.form("bulk_form"):
            bulk_data   = {}
            bulk_sunday = {}
            ncols = min(3, len(workers_df))
            cols  = st.columns(ncols)
            for idx, row in workers_df.iterrows():
                c = cols[idx % ncols]
                with c:
                    st.markdown(f"""
                    <div style='font-family:IBM Plex Mono,monospace;font-size:0.75rem;
                                color:#c8963e;margin-bottom:6px;letter-spacing:1px'>{row['name']}</div>
                    <div style='font-size:0.72rem;color:#6b7a91;margin-bottom:8px'>₹{row['daily_wage']:,.0f}/day</div>
                    """, unsafe_allow_html=True)
                    s  = st.radio("", ["Present","Absent"], key=f"bs_{row['id']}", horizontal=True)
                    h  = st.number_input("Hrs", 0.0, 24.0,
                                         value=8.0 if s=="Present" else 0.0,
                                         step=0.5, key=f"bh_{row['id']}", disabled=(s=="Absent"))
                    sp = 0.0
                    if is_sunday(bulk_date):
                        give = st.checkbox("Gave ₹1,000 cash today?", key=f"bsun_{row['id']}")
                        sp   = 1000.0 if give else 0.0
                    bulk_data[row["id"]]   = (s, h)
                    bulk_sunday[row["id"]] = sp
            if st.form_submit_button("💾 Save All", use_container_width=True):
                for wid, (s, h) in bulk_data.items():
                    mark_attendance(wid, bulk_date, s, 0.0 if s=="Absent" else h, bulk_sunday[wid])
                st.cache_data.clear()
                st.success(f"✅ Bulk attendance saved for {bulk_date.strftime('%d %b %Y')}")
                st.rerun()


# ════════════════════════════════════════════════════════════════
# TAB 3 — ADVANCES
# ════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    workers_df = get_workers()
    if workers_df.empty:
        st.warning("No workers found. Add workers first.")
    else:
        c_adv_form, c_adv_list = st.columns([1, 2], gap="large")
        with c_adv_form:
            st.markdown("### Give Advance")
            st.markdown("""
            <div class='formula-card'>
            Record emergency or requested money given to a worker.
            This amount is <span class='hl'>deducted from their net salary</span>
            in the monthly summary.
            </div>
            """, unsafe_allow_html=True)
            with st.form("advance_form", clear_on_submit=True):
                adv_wid    = st.selectbox("Worker", workers_df["id"].tolist(),
                                          format_func=lambda i: workers_df.loc[workers_df["id"]==i,"name"].values[0],
                                          key="adv_wid")
                adv_date   = st.date_input("Date", value=today, key="adv_date")
                adv_amount = st.number_input("Amount (₹)", min_value=1.0, value=500.0, step=100.0)
                adv_reason = st.text_input("Reason / Note", placeholder="e.g. Medical emergency")
                if st.form_submit_button("💰 Record Advance", use_container_width=True):
                    add_advance(adv_wid, adv_date, adv_amount, adv_reason)
                    st.cache_data.clear()
                    wname = workers_df.loc[workers_df["id"]==adv_wid,"name"].values[0]
                    st.success(f"✅ ₹{adv_amount:,.0f} advance recorded for {wname}")
                    st.rerun()
        with c_adv_list:
            st.markdown("### Advance History")
            af1, af2, af3 = st.columns(3)
            with af1:
                adv_filter_w = st.selectbox("Worker", [None]+workers_df["id"].tolist(),
                                            format_func=lambda i: "All" if i is None else
                                                workers_df.loc[workers_df["id"]==i,"name"].values[0],
                                            key="adv_fw")
            with af2:
                adv_fs = st.date_input("From", value=today.replace(day=1), key="adv_s")
            with af3:
                adv_fe = st.date_input("To",   value=today,               key="adv_e")
            advances = get_advances(wid=adv_filter_w, start=adv_fs, end=adv_fe)
            if advances.empty:
                st.info("No advance records for the selected filters.")
            else:
                adv_summary = advances.groupby("name")["amount"].agg(
                    Count="count", Total="sum"
                ).reset_index().rename(columns={"name":"Worker","Total":"Total Advance (₹)","Count":"# Advances"})
                ac1, ac2 = st.columns(2)
                ac1.metric("Total Advances", len(advances))
                ac2.metric("Total Amount",   f"₹{advances['amount'].sum():,.0f}")
                st.dataframe(adv_summary, use_container_width=True, hide_index=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("##### All Entries")
                disp_adv = advances[["id","name","date","amount","reason"]].rename(columns={
                    "id":"ID","name":"Worker","date":"Date","amount":"Amount (₹)","reason":"Reason"
                })
                st.dataframe(disp_adv, use_container_width=True, hide_index=True)
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown("#### 🗑️ Delete Advance")
                del_aid = st.number_input("Advance Record ID to delete", min_value=1, step=1, key="del_adv")
                with st.container():
                    st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                    if st.button("Delete Advance Record", key="del_adv_btn"):
                        delete_advance(int(del_aid))
                        st.cache_data.clear()
                        st.success(f"Advance #{del_aid} deleted.")
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# TAB 4 — CANTEEN (Daily bulk total entry per worker)
# ════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<br>", unsafe_allow_html=True)
    workers_df = get_workers()

    if workers_df.empty:
        st.warning("No workers found. Add workers first.")
    else:
        st.markdown("### 🍽️ Daily Canteen Bill")
        st.markdown("""
        <div class='canteen-card'>
        <span class='title'>How it works</span>
        Enter each worker's <span class='hl'>total canteen spend for the selected day</span>.
        Leave at <span class='hl'>₹0</span> to skip a worker — they won't get a record.
        Re-saving on the same day <span class='hl'>overwrites</span> the previous amount.
        The canteen total is <span class='hl'>deducted from net salary</span> each month.
        </div>
        """, unsafe_allow_html=True)

        # Date picker outside the form so pre-fill values refresh reactively
        cant_date = st.date_input("📅 Select Date", value=today, key="cant_date_bulk")

        # Load existing entries for this date to pre-fill the inputs
        existing_today = get_canteen(start=cant_date, end=cant_date)
        existing_map   = {}
        if not existing_today.empty:
            existing_map = dict(zip(existing_today["worker_id"], existing_today["amount"]))

        if existing_map:
            st.markdown(f"""
            <div style='font-family:IBM Plex Mono,monospace;font-size:0.72rem;
                        color:#2eccc0;letter-spacing:1.5px;margin-bottom:8px'>
            ✏️ Existing entries found for {cant_date.strftime('%d %b %Y')} — fields pre-filled. Save to update.
            </div>
            """, unsafe_allow_html=True)

        with st.form("canteen_bulk_form"):
            st.markdown(f"""
            <div style='font-family:IBM Plex Mono,monospace;font-size:0.72rem;
                        color:#c8963e;letter-spacing:2px;margin-bottom:16px'>
            CANTEEN BILLS FOR: {cant_date.strftime('%d %B %Y (%A)')}
            </div>
            """, unsafe_allow_html=True)

            entries = {}
            ncols = min(3, len(workers_df))
            cols  = st.columns(ncols)
            for idx, row in workers_df.iterrows():
                c = cols[idx % ncols]
                with c:
                    prefill = existing_map.get(row["id"], 0.0)
                    amt = st.number_input(
                        f"₹ {row['name']}",
                        min_value=0.0,
                        value=float(prefill),
                        step=5.0,
                        format="%.2f",
                        key=f"cant_{row['id']}"
                    )
                    if prefill > 0:
                        st.caption(f"✏️ Current saved: ₹{prefill:.0f}")
                    entries[row["id"]] = (row["name"], amt)

            # Live total preview
            total_preview = sum(v[1] for v in entries.values())
            st.markdown(f"""
            <div style='background:#051a1a;border:1px solid #0a4040;border-radius:10px;
                        padding:14px 20px;margin:16px 0;
                        display:flex;align-items:center;justify-content:space-between;
                        font-family:IBM Plex Mono,monospace'>
                <span style='color:#6b7a91;font-size:0.7rem;letter-spacing:2px;text-transform:uppercase'>
                    Total canteen for the day
                </span>
                <span style='color:#2eccc0;font-size:1.6rem;font-weight:700'>
                    ₹{total_preview:,.2f}
                </span>
            </div>
            """, unsafe_allow_html=True)

            if st.form_submit_button("💾 Save All Canteen Bills", use_container_width=True):
                saved = 0
                for wid, (name, amt) in entries.items():
                    if amt > 0:
                        upsert_canteen(wid, cant_date, amt)
                        saved += 1
                st.cache_data.clear()
                if saved:
                    st.success(f"✅ Saved canteen bills for {saved} worker(s) on {cant_date.strftime('%d %b %Y')}")
                else:
                    st.warning("All amounts were ₹0 — nothing saved.")
                st.rerun()

        # ── Quick today's glance ─────────────────────────────────
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("#### Today's Canteen at a Glance")
        today_cant = get_canteen(start=today, end=today)
        if today_cant.empty:
            st.info("No canteen entries for today yet.")
        else:
            daily_cols = st.columns(len(today_cant) if len(today_cant) <= 4 else 4)
            for i, row in today_cant.iterrows():
                daily_cols[i % 4].metric(row["name"], f"₹{row['amount']:,.2f}")
            st.metric("Total Canteen Spend Today", f"₹{today_cant['amount'].sum():,.2f}")

        # ── History ─────────────────────────────────────────────
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### Canteen History")

        cf1, cf2, cf3 = st.columns(3)
        with cf1:
            cant_filter_w = st.selectbox(
                "Worker", [None]+workers_df["id"].tolist(),
                format_func=lambda i: "All" if i is None else
                    workers_df.loc[workers_df["id"]==i,"name"].values[0],
                key="cant_fw"
            )
        with cf2:
            cant_fs = st.date_input("From", value=today.replace(day=1), key="cant_s")
        with cf3:
            cant_fe = st.date_input("To", value=today, key="cant_e")

        canteen_records = get_canteen(wid=cant_filter_w, start=cant_fs, end=cant_fe)

        if canteen_records.empty:
            st.info("No canteen records for the selected filters.")
        else:
            cm1, cm2 = st.columns(2)
            cm1.metric("Days Recorded",    len(canteen_records))
            cm2.metric("Total Canteen Bill", f"₹{canteen_records['amount'].sum():,.2f}")

            # Per-worker summary
            cant_summary = canteen_records.groupby("name")["amount"].agg(
                Days="count", Total="sum"
            ).reset_index().rename(columns={
                "name":"Worker", "Days":"Days", "Total":"Total Bill (₹)"
            })
            st.dataframe(cant_summary, use_container_width=True, hide_index=True)

            # Full records table
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### All Records")
            disp_cant = canteen_records[["id","name","date","amount"]].rename(columns={
                "id":"ID","name":"Worker","date":"Date","amount":"Daily Bill (₹)"
            })
            st.dataframe(disp_cant, use_container_width=True, hide_index=True)

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("#### 🗑️ Delete Entry")
            st.caption("Use the ID from the table above.")
            del_cid = st.number_input("Canteen Entry ID to delete", min_value=1, step=1, key="del_cant")
            with st.container():
                st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                if st.button("Delete Canteen Entry", key="del_cant_btn"):
                    delete_canteen_entry(int(del_cid))
                    st.cache_data.clear()
                    st.success(f"Entry #{del_cid} deleted.")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<hr>", unsafe_allow_html=True)
            buf_c = io.StringIO()
            disp_cant.to_csv(buf_c, index=False)
            st.download_button(
                "📥 Download Canteen CSV", buf_c.getvalue(),
                f"canteen_{cant_fs}_{cant_fe}.csv", "text/csv",
                use_container_width=True
            )


# ════════════════════════════════════════════════════════════════
# TAB 5 — VIEW ATTENDANCE RECORDS
# ════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("<br>", unsafe_allow_html=True)
    workers_df = get_workers()
    rf1, rf2, rf3 = st.columns(3)
    with rf1:
        r_worker = st.selectbox("Worker", [None]+workers_df["id"].tolist(),
                                format_func=lambda i: "All Workers" if i is None else
                                    workers_df.loc[workers_df["id"]==i,"name"].values[0],
                                key="r_w")
    with rf2:
        r_start = st.date_input("From", value=today.replace(day=1), key="r_s")
    with rf3:
        r_end   = st.date_input("To",   value=today,               key="r_e")
    records = get_attendance(wid=r_worker, start=r_start, end=r_end)
    if records.empty:
        st.info("No records for the selected filters.")
    else:
        records = enrich_attendance(records)
        disp = records[[
            "id","name","date","status","hours","overtime",
            "daily_wage","per_hr","day_salary","sunday_pay","gross_earned"
        ]].rename(columns={
            "id":"ID","name":"Worker","date":"Date","status":"Status",
            "hours":"Hours","overtime":"OT Hrs","daily_wage":"Daily Wage (₹)",
            "per_hr":"Per Hr (₹)","day_salary":"Day Earned (₹)",
            "sunday_pay":"Sunday Cash Given (₹)","gross_earned":"Gross Earned (₹)",
        })
        st.dataframe(disp, use_container_width=True, hide_index=True)
        m1,m2,m3,m4,m5 = st.columns(5)
        m1.metric("Records",           len(records))
        m2.metric("Total Hrs",         f"{records['hours'].sum():.1f}")
        m3.metric("OT Hrs",            f"{records['overtime'].sum():.1f}")
        m4.metric("Sunday Cash Given", f"₹{records['sunday_pay'].sum():,.0f}")
        m5.metric("Gross Earned",      f"₹{records['gross_earned'].sum():,.0f}")
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("#### Delete Record")
        del_rid = st.number_input("Record ID", min_value=1, step=1, key="del_r")
        with st.container():
            st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
            if st.button("Delete Record", key="del_r_btn"):
                delete_attendance(int(del_rid))
                st.cache_data.clear()
                st.success(f"Record #{del_rid} deleted.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        buf = io.StringIO(); disp.to_csv(buf, index=False)
        st.download_button("📥 Download CSV", buf.getvalue(),
                           f"attendance_{r_start}_{r_end}.csv", "text/csv",
                           use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 6 — MONTHLY SUMMARY
# ════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("<br>", unsafe_allow_html=True)
    my1, my2 = st.columns(2)
    with my1:
        year_opts = list(range(2023, today.year+2))
        sel_year  = st.selectbox("Year", year_opts, index=year_opts.index(today.year))
    with my2:
        sel_month = st.selectbox("Month", range(1,13), index=today.month-1,
                                 format_func=lambda m: calendar.month_name[m])
    st.markdown("#### 📋 Muster Sheet")
    pivot, all_days = get_monthly_muster(sel_year, sel_month)
    if isinstance(pivot, pd.DataFrame) and not pivot.empty:
        st.markdown(render_muster_html(pivot, sel_year, sel_month, all_days), unsafe_allow_html=True)
        st.markdown("""
        <div style='margin-top:10px;font-family:IBM Plex Mono,monospace;font-size:0.68rem;color:#6b7a91'>
        <span style='color:#3ecf8e'>P</span> = Present &nbsp;·&nbsp;
        <span style='color:#f05060'>A</span> = Absent &nbsp;·&nbsp;
        Shaded columns = Sundays
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No attendance data for this month.")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("#### 📊 Worker-wise Salary Breakdown")
    summary = get_monthly_summary(sel_year, sel_month)
    if not summary.empty:
        summary["OT Pay (₹)"] = (summary["Total_OT"] * summary["Daily Wage"] / 8).round(2)
        disp_s = summary[[
            "Worker","Daily Wage","Present_Days","Absent_Days",
            "Total_Hours","Total_OT","OT Pay (₹)",
            "Gross_Salary","Sunday_Given","total_advance","total_canteen","Total_Given","Net_Pay"
        ]].rename(columns={
            "Daily Wage":    "Daily Wage (₹)",
            "Present_Days":  "Present",
            "Absent_Days":   "Absent",
            "Total_Hours":   "Hrs",
            "Total_OT":      "OT Hrs",
            "Gross_Salary":  "Gross Earned (₹)",
            "Sunday_Given":  "Sunday Cash Given (₹)",
            "total_advance": "Advances Given (₹)",
            "total_canteen": "Canteen Bill (₹)",
            "Total_Given":   "Total Given (₹)",
            "Net_Pay":       "Net to Pay (₹)",
        })
        st.dataframe(disp_s, use_container_width=True, hide_index=True)
        st.markdown("""
        <div class='formula-card' style='margin-top:16px;font-size:0.8rem'>
        <span class='title'>📐 How Net Salary is Calculated</span>
        <span class='hl'>Gross Earned</span> = (Present Days × Daily Wage) + (OT Hrs × Daily Wage ÷ 8)<br>
        <span class='hl'>Total Given</span> = Sunday Cash + Advances + Canteen Bill &nbsp;← already deducted<br>
        <span class='hl'>Net to Pay</span> = Gross Earned − Total Given &nbsp;← amount you still owe
        </div>
        """, unsafe_allow_html=True)
        gm1,gm2,gm3,gm4,gm5,gm6,gm7 = st.columns(7)
        gm1.metric("Workers",         len(summary))
        gm2.metric("Gross Earned",    f"₹{summary['Gross_Salary'].sum():,.0f}")
        gm3.metric("Sunday Cash",     f"₹{summary['Sunday_Given'].sum():,.0f}")
        gm4.metric("Advances",        f"₹{summary['total_advance'].sum():,.0f}")
        gm5.metric("Canteen Bill",    f"₹{summary['total_canteen'].sum():,.0f}")
        gm6.metric("Total Given Out", f"₹{summary['Total_Given'].sum():,.0f}")
        gm7.metric("Net to Pay",      f"₹{summary['Net_Pay'].sum():,.0f}")
        buf2 = io.StringIO(); disp_s.to_csv(buf2, index=False)
        st.download_button("📥 Download Monthly Report (CSV)", buf2.getvalue(),
                           f"payroll_{calendar.month_name[sel_month]}_{sel_year}.csv",
                           "text/csv", use_container_width=True)
    else:
        st.info("No data for this month yet.")


# ════════════════════════════════════════════════════════════════
# TAB 7 — SETTINGS
# ════════════════════════════════════════════════════════════════
with tab7:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Daily Wage Settings")
    workers_df = get_workers()
    if workers_df.empty:
        st.info("No workers to configure.")
    else:
        st.markdown("""
        <div class='formula-card'>
        Set each worker's <span class='hl'>Daily Wage</span> — the fixed pay for one full 8-hour day.<br>
        Per-hour rate and overtime rate are <span class='hl'>auto-derived as Daily Wage ÷ 8</span>.
        </div>
        """, unsafe_allow_html=True)
        with st.form("wage_form"):
            updates = {}
            for _, row in workers_df.iterrows():
                wc1, wc2, wc3 = st.columns([2, 2, 3])
                with wc1:
                    new_w = st.number_input(f"{row['name']}", min_value=1.0,
                                            value=float(row["daily_wage"]), step=50.0, key=f"w_{row['id']}")
                with wc2:
                    st.markdown(f"""
                    <div style='padding-top:28px;font-family:IBM Plex Mono,monospace;
                                font-size:0.75rem;color:#c8963e'>₹{new_w/8:.2f}/hr</div>
                    """, unsafe_allow_html=True)
                with wc3:
                    st.markdown(f"""
                    <div style='padding-top:24px;font-family:IBM Plex Sans,sans-serif;
                                font-size:0.8rem;color:#6b7a91'>
                    OT = ₹{new_w/8:.2f} × overtime hours</div>
                    """, unsafe_allow_html=True)
                updates[row["id"]] = new_w
            if st.form_submit_button("💾 Save All Wages", use_container_width=True):
                for wid, wage in updates.items():
                    update_wage(wid, wage)
                st.cache_data.clear()
                st.success("✅ Wages updated.")
                st.rerun()
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 🗄️ Database Info")
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM attendance"); att_c  = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM advances");   adv_c  = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM canteen");    cant_c = cur.fetchone()[0]
        cur.close()
    finally:
        release_conn(conn)
    di1,di2,di3,di4 = st.columns(4)
    di1.metric("Workers",         len(workers_df))
    di2.metric("Att. Records",    att_c)
    di3.metric("Adv. Records",    adv_c)
    di4.metric("Canteen Entries", cant_c)
    st.markdown(f"**Database:** Supabase (PostgreSQL)")