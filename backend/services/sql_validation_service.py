"""
SQL Safety and Validation Service.
Uses sqlglot to parse AST, enforce read-only SELECT/CTE statements, prevent multi-statement injection,
block administrative queries, ensure allowed table references, validate column references, and preserve
legitimate SQL functions (like REPLACE, CHAR, SUBSTR, ROUND, etc.).
"""
from typing import Tuple, List, Optional, Set
import sqlglot
from sqlglot import exp
from backend.services.schema_service import ALLOWED_TABLES, SCHEMA_COLUMNS_BY_TABLE

# Strictly disallowed administrative or dangerous SQLite extension/system functions
DANGEROUS_FUNCTIONS: Set[str] = {
    "LOAD_EXTENSION", "LOAD_EXT", "RANDOMBLOB"
}

# Forbidden table/schema objects
FORBIDDEN_CATALOG_OBJECTS: Set[str] = {
    "sqlite_master", "sqlite_schema", "sqlite_temp_master", "sqlite_temp_schema", "sqlite_sequence"
}


class SQLValidationService:
    @staticmethod
    def validate_sql(sql: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validates SQL query using AST inspection.
        Returns:
            (is_valid: bool, error_message: Optional[str], referenced_tables: List[str])
        """
        if not sql or not sql.strip():
            return False, "SQL statement is empty.", []

        cleaned_sql = sql.strip().rstrip(";")
        
        # 1. Reject multiple statements separated by semicolons
        if ";" in cleaned_sql:
            return False, "Multiple SQL statements are strictly rejected for safety.", []

        # 2. Parse AST using sqlglot for SQLite dialect
        try:
            parsed_expressions = sqlglot.parse(cleaned_sql, read="sqlite")
        except Exception as e:
            return False, f"SQL syntax parsing error: {str(e)}", []

        if not parsed_expressions:
            return False, "Failed to parse any valid SQL statement.", []

        if len(parsed_expressions) > 1:
            return False, "Multiple parsed SQL statements detected. Only a single read-only statement is allowed.", []

        expression = parsed_expressions[0]

        # 3. Check for explicitly rejected AST nodes (destructive DDL/DML/Commands)
        disallowed_types = (
            exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter,
            exp.Create, exp.Command, exp.Pragma, exp.Commit, exp.Rollback
        )
        if isinstance(expression, disallowed_types):
            return False, f"Prohibited operation '{type(expression).__name__}'. Only read-only SELECT queries and CTEs are permitted.", []

        # 4. Verify statement is a Select or Union or CTE
        is_select_type = isinstance(expression, (exp.Select, exp.Union))
        is_cte_with = isinstance(expression, exp.Expression) and expression.key == "with"
        if not (is_select_type or is_cte_with):
            return False, f"Invalid statement type: {expression.key.upper()}. Only SELECT queries and CTEs are permitted.", []

        # Ensure no nested mutating expressions exist inside the AST
        for node in expression.walk():
            if isinstance(node, disallowed_types):
                return False, f"Prohibited nested operation '{type(node).__name__}'. Only read-only operations are permitted.", []

        # 5. Extract and validate referenced tables and CTE aliases
        cte_aliases: Set[str] = set()
        for cte in expression.find_all(exp.CTE):
            if cte.alias:
                cte_aliases.add(cte.alias.lower())

        referenced_tables: Set[str] = set()
        for table in expression.find_all(exp.Table):
            t_name = table.name.lower()
            if t_name not in cte_aliases:
                referenced_tables.add(t_name)

        # 6. Check tables against whitelist and forbidden catalogs
        for tbl in referenced_tables:
            if tbl in FORBIDDEN_CATALOG_OBJECTS:
                return False, f"Direct access to internal database catalogs ('{tbl}') is prohibited.", []
            if tbl not in ALLOWED_TABLES:
                return False, f"Access to table or metadata object '{tbl}' is forbidden. Permitted tables: {', '.join(sorted(ALLOWED_TABLES))}.", []

        # 7. Check for forbidden functions (e.g. LOAD_EXTENSION)
        for func in expression.find_all(exp.Anonymous):
            func_name = func.name.upper()
            if func_name in DANGEROUS_FUNCTIONS:
                return False, f"Use of unsafe database function '{func.name}' is prohibited.", []

        # 8. Check for catalog probing in raw string literals / column names
        for node in expression.walk():
            node_str = str(node).lower()
            for forbidden in FORBIDDEN_CATALOG_OBJECTS:
                if forbidden in node_str and not isinstance(node, exp.Literal):
                    return False, f"Direct access to internal database catalogs ('{forbidden}') is prohibited.", []

        # 9. Validate column references against schema catalog
        # When explicit table qualifier matches an allowed table, verify column exists
        for col in expression.find_all(exp.Column):
            col_name = col.name.lower()
            table_qualifier = col.table.lower() if col.table else None
            
            # If qualified with a real table
            if table_qualifier and table_qualifier in ALLOWED_TABLES:
                valid_cols = SCHEMA_COLUMNS_BY_TABLE.get(table_qualifier, set())
                if col_name != "*" and col_name not in valid_cols:
                    return False, f"Column '{col.name}' does not exist on table '{table_qualifier}'.", []

        return True, None, list(referenced_tables)

    @staticmethod
    def enforce_row_limit(sql: str, max_limit: int = 500) -> str:
        """
        Rewrites SQL query through AST parsing to enforce a safe row LIMIT.
        If a LIMIT already exists and is <= max_limit, preserves it; otherwise clamps/appends max_limit.
        """
        try:
            parsed = sqlglot.parse_one(sql.strip().rstrip(";"), read="sqlite")
            limit_node = parsed.args.get("limit")
            if limit_node and limit_node.expression:
                try:
                    curr_limit = int(str(limit_node.expression))
                    if curr_limit > max_limit:
                        limit_node.set("expression", exp.Literal.number(max_limit))
                except (ValueError, TypeError):
                    limit_node.set("expression", exp.Literal.number(max_limit))
            else:
                parsed = parsed.limit(max_limit)
            return parsed.sql(dialect="sqlite")
        except Exception:
            # Fallback string append if AST rewrite fails
            cleaned = sql.strip().rstrip(";")
            if "LIMIT" not in cleaned.upper():
                return f"{cleaned} LIMIT {max_limit}"
            return cleaned
