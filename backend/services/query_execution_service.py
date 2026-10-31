"""
Safe Read-Only Query Execution Service with AST Row Limits and Timeout Protections.
Opens SQLite connections with query_only=ON and URI mode=ro to ensure absolute read-only safety.
"""
import time
import sqlite3
import os
from typing import Dict, Any, List, Tuple
from backend.config import settings
from backend.services.sql_validation_service import SQLValidationService


class QueryExecutionService:
    @staticmethod
    def _get_sqlite_path() -> str:
        db_url = settings.database_url
        if db_url.startswith("sqlite:///"):
            return db_url.replace("sqlite:///", "")
        elif db_url.startswith("sqlite://"):
            return db_url.replace("sqlite://", "")
        return "data/querylens.db"

    @classmethod
    def execute_query(
        cls,
        sql: str,
        row_limit: int = settings.default_row_limit,
        timeout_seconds: float = settings.query_timeout_seconds
    ) -> Tuple[bool, List[str], List[Dict[str, Any]], float, str]:
        """
        Validates and executes SQL query safely in read-only mode with timeout protection.
        Returns:
            (success: bool, columns: List[str], rows: List[Dict[str, Any]], execution_time_ms: float, error_message: str)
        """
        # 1. Validate SQL first via AST inspection
        is_valid, validation_err, _ = SQLValidationService.validate_sql(sql)
        if not is_valid:
            return False, [], [], 0.0, f"SQL Safety Validation Failed: {validation_err}"

        # 2. Enforce row limit via AST rewriting
        effective_limit = min(row_limit, settings.max_row_limit)
        rewritten_sql = SQLValidationService.enforce_row_limit(sql, max_limit=effective_limit)

        start_time = time.perf_counter()
        db_path = cls._get_sqlite_path()

        if not os.path.exists(db_path):
            return False, [], [], 0.0, f"Database file not found at {db_path}."

        uri = f"file:{os.path.abspath(db_path)}?mode=ro"

        conn = None
        try:
            # Open strictly in read-only URI mode
            conn = sqlite3.connect(uri, uri=True, timeout=timeout_seconds)
            # Enable query_only pragma as second line of defense
            conn.execute("PRAGMA query_only = ON;")

            # Configure progress handler for timeout enforcement
            exec_start = time.time()
            def progress_callback():
                if time.time() - exec_start > timeout_seconds:
                    return 1  # Abort query execution
                return 0

            conn.set_progress_handler(progress_callback, 1000)

            cursor = conn.cursor()
            cursor.execute(rewritten_sql)

            if cursor.description is None:
                exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return True, [], [], exec_time_ms, ""

            columns = [col[0] for col in cursor.description]
            raw_rows = cursor.fetchmany(effective_limit)

            rows: List[Dict[str, Any]] = []
            for row in raw_rows:
                row_dict = {}
                for col_name, val in zip(columns, row):
                    if hasattr(val, "isoformat"):
                        row_dict[col_name] = val.isoformat()
                    elif isinstance(val, float):
                        row_dict[col_name] = round(val, 2)
                    else:
                        row_dict[col_name] = val
                rows.append(row_dict)

            exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return True, columns, rows, exec_time_ms, ""

        except sqlite3.OperationalError as e:
            exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            err_msg = str(e)
            if "interrupted" in err_msg.lower():
                return False, [], [], exec_time_ms, f"Query exceeded maximum execution timeout ({timeout_seconds}s)."
            if "readonly" in err_msg.lower():
                return False, [], [], exec_time_ms, "Database write attempt rejected by read-only connection."
            return False, [], [], exec_time_ms, f"Database operational error: {err_msg}"

        except Exception as e:
            exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            error_str = str(e).split("\n")[0]
            return False, [], [], exec_time_ms, f"Query execution failed: {error_str}"

        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
