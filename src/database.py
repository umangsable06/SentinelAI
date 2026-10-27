# src/database.py — Phase 6: SQLite Database
#
# PURPOSE:
#   Create and manage a local SQLite database that stores all alerts
#   permanently. Unlike a CSV file that gets overwritten, the database
#   keeps a running history of every alert ever generated.
#
#   This module provides four functions the dashboard and scripts use:
#     - init_db()         : create the tables if they don't exist yet
#     - insert_alerts()   : load alerts_with_explanations.csv into the DB
#     - fetch_alerts()    : read alerts back (with optional filters)
#     - get_stats()       : summary counts for the dashboard header
#
# RUN DIRECTLY to populate the database:
#   python src/database.py

import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import config


# ── Database schema ───────────────────────────────────────────────────────────
#
# WHY SQLITE?
#   SQLite is a file-based database — no server needed, no installation,
#   no configuration. The entire database lives in a single file:
#   data/sentinel.db. It is the most widely used database engine in the
#   world (it ships inside every Android and iOS device).
#
#   For a production system you would use PostgreSQL or MySQL.
#   For a laptop-based learning project, SQLite is perfect.

CREATE_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS alerts (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp         TEXT    NOT NULL,
    source_ip         TEXT,
    destination_ip    TEXT,
    true_label        TEXT,
    predicted_label   TEXT    NOT NULL,
    risk_score        REAL    NOT NULL,
    severity          TEXT    NOT NULL,
    if_score          REAL,
    xgb_score         REAL,
    ai_explanation    TEXT,
    created_at        TEXT    DEFAULT (datetime('now'))
);
"""

CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_severity   ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_risk_score ON alerts(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_timestamp  ON alerts(timestamp);
"""


def get_db_path() -> str:
    """Return the absolute path to the SQLite database file."""
    return config.DB_PATH


def init_db() -> sqlite3.Connection:
    """
    Create the database file and tables if they don't already exist.
    Returns an open connection so the caller can use it immediately.

    SQLite creates the file automatically when you connect to it —
    no need to create the file manually first.
    """
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row   # rows behave like dictionaries
    cursor = conn.cursor()

    # Create table
    cursor.executescript(CREATE_ALERTS_TABLE)

    # Create indexes (speeds up filtering by severity and sorting by risk)
    for statement in CREATE_INDEX.strip().split("\n"):
        if statement.strip():
            cursor.execute(statement)

    conn.commit()
    return conn


def insert_alerts(conn: sqlite3.Connection, alerts_df: pd.DataFrame) -> int:
    """
    Insert all rows from the alerts DataFrame into the database.
    Clears the table first so re-running this script doesn't create duplicates.

    Returns the number of rows inserted.

    WHY CLEAR BEFORE INSERT?
    In a real production system you would append new alerts continuously.
    For this project, we regenerate the full alert set each time we run
    the pipeline, so clearing and reinserting keeps things clean and simple.
    """
    cursor = conn.cursor()

    # Clear existing alerts (so re-running doesn't duplicate)
    cursor.execute("DELETE FROM alerts")

    # Prepare rows for insertion
    rows_to_insert = []
    now = datetime.now().isoformat()

    for _, row in alerts_df.iterrows():
        rows_to_insert.append((
            now,                                          # timestamp
            row.get("Source IP", ""),                    # source_ip
            row.get("Destination IP", ""),               # destination_ip
            row.get("True Label", ""),                   # true_label
            row.get("Predicted Label", "BENIGN"),        # predicted_label
            float(row.get("Risk Score", 0.0)),           # risk_score
            row.get("Severity", "Low"),                  # severity
            float(row.get("IF Score (0-10)", 0.0)),      # if_score
            float(row.get("XGB Score (0-10)", 0.0)),     # xgb_score
            row.get("AI Explanation", ""),               # ai_explanation
        ))

    cursor.executemany("""
        INSERT INTO alerts
            (timestamp, source_ip, destination_ip, true_label,
             predicted_label, risk_score, severity,
             if_score, xgb_score, ai_explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows_to_insert)

    conn.commit()
    return len(rows_to_insert)


def fetch_alerts(
    conn: sqlite3.Connection,
    severity: str = None,
    min_risk: float = None,
    limit: int = None,
) -> pd.DataFrame:
    """
    Read alerts from the database with optional filters.

    Parameters
    ----------
    severity  : if set, only return alerts with this severity level
    min_risk  : if set, only return alerts with risk_score >= this value
    limit     : if set, return only this many rows (highest risk first)

    Returns a pandas DataFrame so the dashboard can use it directly.
    """
    query  = "SELECT * FROM alerts WHERE 1=1"
    params = []

    if severity:
        query += " AND severity = ?"
        params.append(severity)

    if min_risk is not None:
        query += " AND risk_score >= ?"
        params.append(min_risk)

    query += " ORDER BY risk_score DESC"

    if limit:
        query += f" LIMIT {int(limit)}"

    df = pd.read_sql_query(query, conn, params=params)
    return df


def get_stats(conn: sqlite3.Connection) -> dict:
    """
    Return a summary dictionary used by the dashboard header:
      total, critical, high, medium, low, avg_risk, max_risk
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*)                              AS total,
            SUM(severity = 'Critical')            AS critical,
            SUM(severity = 'High')                AS high,
            SUM(severity = 'Medium')              AS medium,
            SUM(severity = 'Low')                 AS low,
            ROUND(AVG(risk_score), 2)             AS avg_risk,
            ROUND(MAX(risk_score), 2)             AS max_risk
        FROM alerts
    """)
    row = cursor.fetchone()
    return dict(row) if row else {}


# ── Main — populate the database ──────────────────────────────────────────────

def main():
    print("=" * 60)
    print("SentinelAI — Phase 6: Database")
    print("=" * 60)

    # Load the alerts CSV produced by Phase 5
    alerts_path = Path(config.PROCESSED_DATA_DIR) / "alerts_with_explanations.csv"

    # Fallback to Phase 4 output if Phase 5 hasn't run yet
    if not alerts_path.exists():
        alerts_path = Path(config.PROCESSED_DATA_DIR) / "alerts.csv"
        print("Note: alerts_with_explanations.csv not found — using alerts.csv (no AI explanations).")

    if not alerts_path.exists():
        raise FileNotFoundError(
            "No alerts file found. Run Phase 4 first: python scripts/risk_scoring.py"
        )

    alerts_df = pd.read_csv(alerts_path)
    print(f"Loaded {len(alerts_df):,} alerts from {alerts_path.name}")

    # Initialise database and tables
    conn = init_db()
    print(f"Database initialised: {get_db_path()}")

    # Insert alerts
    count = insert_alerts(conn, alerts_df)
    print(f"Inserted {count:,} alerts into the database.")

    # Verify by reading back and printing stats
    stats = get_stats(conn)
    print(f"\nDatabase summary:")
    print(f"  Total alerts:    {stats.get('total', 0):,}")
    print(f"  Critical:        {stats.get('critical', 0):,}")
    print(f"  High:            {stats.get('high', 0):,}")
    print(f"  Medium:          {stats.get('medium', 0):,}")
    print(f"  Low:             {stats.get('low', 0):,}")
    print(f"  Average risk:    {stats.get('avg_risk', 0)}")
    print(f"  Highest risk:    {stats.get('max_risk', 0)}")

    # Show top 5 alerts
    top5 = fetch_alerts(conn, limit=5)
    print(f"\nTop 5 highest-risk alerts in the database:")
    print(top5[["source_ip", "predicted_label", "risk_score", "severity"]].to_string(index=False))

    conn.close()

    print(f"\n" + "=" * 60)
    print("Phase 6 complete.")
    print("Run Phase 7 with: streamlit run dashboard/app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
