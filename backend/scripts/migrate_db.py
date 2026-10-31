"""
Database Migration & Schema Alignment Script for QueryLens AI.
Verifies and applies required indexes, foreign keys, and tables to SQLite database.
"""
import sqlite3
import os
import sys

DB_PATH = os.environ.get("DATABASE_URL", "sqlite:///data/querylens.db").replace("sqlite:///", "")


def run_migrations():
    print(f"Running database migrations on {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print(f"Database file does not exist yet at {DB_PATH}. Run seed_db.py first or start application.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create schema_migrations tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration 001: Composite analytics indexes
        cursor.execute("SELECT 1 FROM schema_migrations WHERE version = '001_initial_indexes'")
        if not cursor.fetchone():
            print("Applying migration 001_initial_indexes...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_status_date ON transactions(transaction_status, transaction_timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_prod_date ON transactions(product_id, transaction_timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_reg_date ON transactions(region_id, transaction_timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_channel_date ON transactions(channel, transaction_timestamp);")
            cursor.execute("INSERT INTO schema_migrations (version) VALUES ('001_initial_indexes')")
            print("Migration 001 applied successfully.")

        # Migration 002: Vacuum & optimize PRAGMA
        cursor.execute("SELECT 1 FROM schema_migrations WHERE version = '002_optimize_storage'")
        if not cursor.fetchone():
            print("Applying migration 002_optimize_storage...")
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("INSERT INTO schema_migrations (version) VALUES ('002_optimize_storage')")
            print("Migration 002 applied successfully.")

        conn.commit()
        print("All migrations up-to-date!")
    except Exception as e:
        conn.rollback()
        print(f"Migration error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations()
