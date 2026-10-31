"""
Persistent SQLite-backed storage for Query History and Evaluation Benchmarks.
Prevents unbounded history growth and memory loss across server reloads.
"""
import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from backend.config import settings

STORAGE_DB_PATH = "data/querylens_storage.db"
MAX_HISTORY_ENTRIES = 100


def get_storage_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(STORAGE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(STORAGE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_storage():
    """Initializes tables for query history and benchmark caching."""
    conn = get_storage_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT UNIQUE,
            question TEXT,
            query_status TEXT,
            execution_mode TEXT,
            summary TEXT,
            sql TEXT,
            execution_time_ms REAL,
            payload_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_cache (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            summary_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_history_entry(data: Dict[str, Any]):
    """Saves a query response to persistent history, trimming old records beyond MAX_HISTORY_ENTRIES."""
    conn = get_storage_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO query_history (
                request_id, question, query_status, execution_mode, summary, sql, execution_time_ms, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("request_id"),
            data.get("question"),
            data.get("query_status"),
            data.get("execution_mode"),
            data.get("summary"),
            data.get("sql"),
            data.get("execution_time_ms", 0.0),
            json.dumps(data)
        ))
        
        # Enforce boundary: remove oldest records if over MAX_HISTORY_ENTRIES
        cursor.execute("""
            DELETE FROM query_history 
            WHERE id NOT IN (
                SELECT id FROM query_history ORDER BY id DESC LIMIT ?
            )
        """, (MAX_HISTORY_ENTRIES,))
        conn.commit()
    finally:
        conn.close()


def get_history_entries(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieves the most recent query history records."""
    conn = get_storage_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT payload_json FROM query_history ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [json.loads(row["payload_json"]) for row in rows]
    finally:
        conn.close()


def save_cached_benchmark(benchmark_dict: Dict[str, Any]):
    """Caches benchmark summary persistently."""
    conn = get_storage_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO benchmark_cache (id, summary_json, updated_at)
            VALUES (1, ?, CURRENT_TIMESTAMP)
        """, (json.dumps(benchmark_dict),))
        conn.commit()
    finally:
        conn.close()


def get_cached_benchmark() -> Optional[Dict[str, Any]]:
    """Retrieves cached benchmark summary if available."""
    conn = get_storage_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT summary_json FROM benchmark_cache WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return json.loads(row["summary_json"])
        return None
    finally:
        conn.close()
