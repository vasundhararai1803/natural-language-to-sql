"""
SQL Safety and Validation Service.
Uses sqlglot to parse AST, enforce read-only SELECT/CTE statements, prevent multi-statement injection,
block administrative queries, ensure allowed table references, and check for disallowed functions.
"""
from typing import Tuple, List, Optional
import sqlglot
from sqlglot import exp
from backend.services.schema_service import ALLOWED_TABLES

DISALLOWED_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "ATTACH", "DETACH",
    "REINDEX", "VACUUM", "PRAGMA", "EXEC", "EXECUTE", "SYSTEM", "SHUTDOWN",
    "GRANT", "REVOKE", "TRUNCATE", "REPLACE"
}

DISALLOWED_FUNCTIONS = {
    "LOAD_EXTENSION", "CHAR", "HEX", "RANDOMBLOB"
}


class SQLValidationService:
    @staticmethod
    def validate_sql(sql: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validates SQL query.
        Returns:
            (is_valid: bool, error_message: Optional[str], referenced_tables: List[str])
        """
        if not sql or not sql.strip():
            return False, "SQL statement is empty.", []

        cleaned_sql = sql.strip().rstrip(";")
        
        # 1. Check for semicolon chaining (multiple statements)
        if ";" in cleaned_sql:
            return False, "Multiple SQL statements are strictly rejected for safety.", []

        # 2. Check forbidden keyword tokens in uppercase
        upper_tokens = set(cleaned_sql.upper().replace("(", " ").replace(")", " ").split())
        forbidden_found = upper_tokens.intersection(DISALLOWED_KEYWORDS)
        if forbidden_found:
            return False, f"Prohibited SQL statement/keyword detected: {', '.join(forbidden_found)}. Only read-only SELECT queries are permitted.", []

        # 3. Parse AST using sqlglot
        try:
            parsed_expressions = sqlglot.parse(cleaned_sql, read="sqlite")
        except Exception as e:
            return False, f"SQL syntax parsing error: {str(e)}", []

        if not parsed_expressions:
            return False, "Failed to parse any valid SQL statement.", []

        if len(parsed_expressions) > 1:
            return False, "Multiple parsed SQL statements detected. Only a single read-only statement is allowed.", []

        expression = parsed_expressions[0]

        # 4. Verify top-level node is a SELECT or CTE (WITH ... SELECT)
        if not isinstance(expression, (exp.Select, exp.Union)):
            # If it's a WITH expression, ensure query is Select
            if isinstance(expression, exp.Expression) and expression.key == "with":
                pass
            else:
                return False, f"Invalid statement type: {expression.key.upper()}. Only SELECT queries and CTEs are permitted.", []

        # 5. Extract and validate referenced tables
        referenced_tables = set()
        for table in expression.find_all(exp.Table):
            table_name = table.name.lower()
            # Ignore CTE aliases defined within query
            referenced_tables.add(table_name)

        # Check for CTE aliases
        cte_aliases = set()
        for cte in expression.find_all(exp.CTE):
            if cte.alias:
                cte_aliases.add(cte.alias.lower())

        real_tables = referenced_tables - cte_aliases

        # 6. Check tables against whitelist
        for tbl in real_tables:
            if tbl not in ALLOWED_TABLES:
                return False, f"Access to table or metadata object '{tbl}' is forbidden. Permitted tables: {', '.join(sorted(ALLOWED_TABLES))}.", []

        # 7. Disallowed functions check
        for func in expression.find_all(exp.Anonymous):
            if func.name.upper() in DISALLOWED_FUNCTIONS:
                return False, f"Use of unsafe database function '{func.name}' is prohibited.", []

        # 8. Check for comment injections or unauthorized SQLite internal tables
        for node in expression.walk():
            node_str = str(node).lower()
            if "sqlite_master" in node_str or "sqlite_schema" in node_str or "sqlite_temp_master" in node_str:
                return False, "Direct access to internal database catalogs (sqlite_master) is prohibited.", []

        return True, None, list(real_tables)
