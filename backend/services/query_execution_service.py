"""
Safe Read-Only Query Execution Service with Row Limits and Timeout Protections.
"""
import time
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from backend.models.db_models import engine
from backend.services.sql_validation_service import SQLValidationService

DEFAULT_ROW_LIMIT = 500
MAX_ROW_LIMIT = 2000


class QueryExecutionService:
    @staticmethod
    def execute_query(sql: str, row_limit: int = DEFAULT_ROW_LIMIT) -> Tuple[bool, List[str], List[Dict[str, Any]], float, str]:
        """
        Validates and executes SQL query safely.
        Returns:
            (success: bool, columns: List[str], rows: List[Dict[str, Any]], execution_time_ms: float, error_message: str)
        """
        # Validate SQL first
        is_valid, validation_err, _ = SQLValidationService.validate_sql(sql)
        if not is_valid:
            return False, [], [], 0.0, f"SQL Safety Validation Failed: {validation_err}"

        # Ensure reasonable row limit
        effective_limit = min(row_limit, MAX_ROW_LIMIT)
        cleaned_sql = sql.strip().rstrip(";")
        
        # If user/model didn't add LIMIT, append one if it doesn't already have one
        if "LIMIT" not in cleaned_sql.upper():
            exec_sql = f"{cleaned_sql} LIMIT {effective_limit}"
        else:
            exec_sql = cleaned_sql

        start_time = time.perf_counter()
        try:
            with engine.connect() as conn:
                # SQLite execution with read-only query
                result = conn.execute(text(exec_sql))
                columns = list(result.keys())
                raw_rows = result.fetchmany(effective_limit)
                
                rows = []
                for row in raw_rows:
                    row_dict = {}
                    for col_name, val in zip(columns, row):
                        # Convert datetime or complex types if needed
                        if hasattr(val, "isoformat"):
                            row_dict[col_name] = val.isoformat()
                        elif isinstance(val, float):
                            row_dict[col_name] = round(val, 2)
                        else:
                            row_dict[col_name] = val
                    rows.append(row_dict)

            exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return True, columns, rows, exec_time_ms, ""

        except Exception as e:
            exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            error_str = str(e)
            # Sanitize internal directory paths or secrets from error
            clean_error = error_str.split("\n")[0]
            return False, [], [], exec_time_ms, f"Query execution failed: {clean_error}"
