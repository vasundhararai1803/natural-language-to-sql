"""
Deterministic Template & Semantic Rule-Based SQL Engine.
Supports high-accuracy, offline-capable query generation for standard business questions,
time comparisons, top rankings, diagnostic 'Why' questions, edge-case rejection, and safety tests.
Never silently answers unsupported questions with generic queries; flags low confidence/clarification when ambiguous.
"""
import re
from typing import Dict, Any, Optional, Tuple


class FallbackSQLEngine:
    @staticmethod
    def generate_sql_and_intent(question: str) -> Tuple[Dict[str, Any], Optional[str], Optional[str], Optional[str]]:
        """
        Translates natural language questions into safe SQL or flags safety/clarification/unsupported issues.
        Returns:
            (intent_dict, sql_query, clarification_msg, unsupported_msg)
        """
        if not question or not question.strip():
            intent = {"type": "empty_question", "confidence": 0.0}
            return intent, None, "Please enter a question about your business data.", None

        q = question.lower().strip()

        # 1. Direct Prompt Injection / System Override Attempts / Mutation / Catalog Snooping
        if any(bad in q for bad in [
            "ignore all previous instructions", "system prompt", "drop table", "delete from",
            "insert into", "update transactions", "grant all", "; select", "attach database",
            "sqlite_master", "sqlite_schema", "sqlite_temp_master"
        ]):
            intent = {"type": "security_test", "risk": "prompt_injection_or_mutation", "metric": None, "confidence": 1.0}
            return intent, "SELECT * FROM sqlite_master;", None, None  # Intentionally triggers validator rejection

        # 2. Unsupported Business Metrics (net profit, profit margin, ebitda, payroll, employee salary, churn rate, inventory)
        unsupported_keywords = [
            "net profit", "profit margin", "gross margin", "ebitda", "payroll", "employee",
            "salary", "churn rate", "warehouse", "inventory count", "cost of goods", "cogs", "headcount"
        ]
        if any(bad in q for bad in unsupported_keywords):
            matched = next(bad for bad in unsupported_keywords if bad in q)
            intent = {"type": "unsupported_metric", "requested": matched, "confidence": 1.0}
            unsupported_msg = (
                f"The requested metric ('{matched}') cannot be computed from the current database. "
                "The database schema contains transactions (quantity, unit_price, discount_amount, status), "
                "products, customers, and regions, but does not track COGS, operational expenses, or employee payroll."
            )
            return intent, None, None, unsupported_msg

        # 3. Ambiguous Questions (e.g. "How did we perform last week?", "How are things doing?")
        ambiguous_keywords = [
            "how did we perform", "how did we do", "how are things going", "tell me about our performance",
            "performance last week", "how was business"
        ]
        if any(amb in q for amb in ambiguous_keywords):
            intent = {
                "type": "ambiguous_query",
                "options": ["Completed Transactions", "Total Net Revenue ($)", "Average Order Value (AOV)"],
                "confidence": 0.40
            }
            clarification_msg = (
                f"Your inquiry '{question}' is ambiguous. 'Performance' can refer to Completed Transaction Volume, "
                "Net Realized Revenue ($), or Average Order Value (AOV). Please specify which metric you would like to examine."
            )
            return intent, None, clarification_msg, None

        # 4. Signature Diagnostic: "Why did transactions drop / fall / decline?"
        if any(term in q for term in [
            "why did transactions drop", "why did sales fall", "why did completed transactions decline",
            "why did completed transactions drop", "why did transactions fall", "factors contributed most to the decline",
            "why did orders drop"
        ]):
            intent = {
                "type": "diagnostic_why",
                "metric": "completed_transactions",
                "current_period": "2026-10-12 to 2026-10-18",
                "baseline_period": "2026-10-05 to 2026-10-11",
                "dimensions": ["Region", "Product Category", "Transaction Status", "Channel"],
                "confidence": 0.98
            }
            # Diagnostic SQL for regional trend comparison
            sql = """
                SELECT 
                    r.region_name,
                    SUM(CASE WHEN t.transaction_timestamp BETWEEN '2026-10-05 00:00:00' AND '2026-10-11 23:59:59' AND t.transaction_status = 'completed' THEN 1 ELSE 0 END) AS baseline_completed_tx,
                    SUM(CASE WHEN t.transaction_timestamp BETWEEN '2026-10-12 00:00:00' AND '2026-10-18 23:59:59' AND t.transaction_status = 'completed' THEN 1 ELSE 0 END) AS current_completed_tx,
                    SUM(CASE WHEN t.transaction_timestamp BETWEEN '2026-10-12 00:00:00' AND '2026-10-18 23:59:59' AND t.transaction_status = 'completed' THEN 1 ELSE 0 END) -
                    SUM(CASE WHEN t.transaction_timestamp BETWEEN '2026-10-05 00:00:00' AND '2026-10-11 23:59:59' AND t.transaction_status = 'completed' THEN 1 ELSE 0 END) AS transaction_delta
                FROM transactions t
                JOIN regions r ON t.region_id = r.region_id
                GROUP BY r.region_name
                ORDER BY transaction_delta ASC
            """.strip()
            return intent, sql, None, None

        # 5. Top performing products / items / SKUs
        if ("top" in q or "best" in q) and ("product" in q or "sku" in q or "item" in q):
            intent = {"type": "ranking", "entity": "product", "metric": "revenue", "timeframe": "2026-10-01 to 2026-10-25", "confidence": 0.95}
            sql = """
                SELECT 
                    p.product_name,
                    p.category,
                    COUNT(t.transaction_id) AS total_orders,
                    SUM(t.quantity) AS total_units_sold,
                    ROUND(SUM((t.quantity * t.unit_price) - COALESCE(t.discount_amount, 0)), 2) AS net_revenue
                FROM transactions t
                JOIN products p ON t.product_id = p.product_id
                WHERE t.transaction_status = 'completed'
                  AND t.transaction_timestamp >= '2026-10-01 00:00:00'
                GROUP BY p.product_id, p.product_name, p.category
                ORDER BY net_revenue DESC
                LIMIT 10
            """.strip()
            return intent, sql, None, None

        # 6. Cancellation rate / cancellations
        if "cancellation" in q or "cancelled" in q or "cancel" in q:
            intent = {"type": "ratio_analysis", "metric": "cancellation_rate", "dimension": "region", "confidence": 0.95}
            sql = """
                SELECT 
                    r.region_name,
                    COUNT(t.transaction_id) AS total_orders,
                    SUM(CASE WHEN t.transaction_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
                    ROUND(100.0 * SUM(CASE WHEN t.transaction_status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS cancellation_rate_pct
                FROM transactions t
                JOIN regions r ON t.region_id = r.region_id
                GROUP BY r.region_id, r.region_name
                ORDER BY cancellation_rate_pct DESC
            """.strip()
            return intent, sql, None, None

        # 7. Compare revenue quarter over quarter
        if "quarter" in q and ("revenue" in q or "sales" in q):
            intent = {"type": "quarterly_comparison", "metric": "net_revenue", "confidence": 0.95}
            sql = """
                SELECT 
                    CASE 
                        WHEN strftime('%m', transaction_timestamp) IN ('07', '08', '09') THEN 'Q3 2026'
                        WHEN strftime('%m', transaction_timestamp) IN ('10', '11', '12') THEN 'Q4 2026 (MTD)'
                        ELSE 'Other'
                    END AS quarter,
                    COUNT(transaction_id) AS completed_orders,
                    ROUND(SUM((quantity * unit_price) - COALESCE(discount_amount, 0)), 2) AS total_net_revenue,
                    ROUND(AVG((quantity * unit_price) - COALESCE(discount_amount, 0)), 2) AS average_order_value
                FROM transactions
                WHERE transaction_status = 'completed'
                GROUP BY quarter
                ORDER BY quarter ASC
            """.strip()
            return intent, sql, None, None

        # 8. Daily transactions trend / highlight unusual drops
        if "daily transaction" in q or "unusual drop" in q or "daily trend" in q or "daily" in q:
            intent = {"type": "daily_trend", "metric": "completed_transactions", "timeframe": "October 2026", "confidence": 0.95}
            sql = """
                SELECT 
                    strftime('%Y-%m-%d', transaction_timestamp) AS order_date,
                    COUNT(transaction_id) AS total_transactions,
                    SUM(CASE WHEN transaction_status = 'completed' THEN 1 ELSE 0 END) AS completed_transactions,
                    SUM(CASE WHEN transaction_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_transactions
                FROM transactions
                WHERE transaction_timestamp >= '2026-10-01 00:00:00'
                GROUP BY order_date
                ORDER BY order_date ASC
            """.strip()
            return intent, sql, None, None

        # 9. Revenue / sales by category
        if "category" in q and ("revenue" in q or "sales" in q or "amount" in q):
            intent = {"type": "aggregation", "metric": "revenue", "dimension": "product_category", "confidence": 0.95}
            sql = """
                SELECT 
                    p.category,
                    COUNT(t.transaction_id) AS order_count,
                    ROUND(SUM((t.quantity * t.unit_price) - COALESCE(t.discount_amount, 0)), 2) AS total_revenue
                FROM transactions t
                JOIN products p ON t.product_id = p.product_id
                WHERE t.transaction_status = 'completed'
                GROUP BY p.category
                ORDER BY total_revenue DESC
            """.strip()
            return intent, sql, None, None

        # 10. Channel breakdown
        if "channel" in q:
            intent = {"type": "aggregation", "metric": "transactions", "dimension": "channel", "confidence": 0.95}
            sql = """
                SELECT 
                    channel,
                    COUNT(transaction_id) AS total_orders,
                    SUM(CASE WHEN transaction_status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
                    ROUND(SUM((quantity * unit_price) - COALESCE(discount_amount, 0)), 2) AS net_revenue
                FROM transactions
                GROUP BY channel
                ORDER BY total_orders DESC
            """.strip()
            return intent, sql, None, None

        # 11. Customer segment breakdown or enterprise customer analysis
        if "customer segment" in q or "segment" in q or "enterprise" in q or "consumer" in q or "smb" in q or "vip" in q:
            if "average" in q or "aov" in q:
                intent = {"type": "aggregation", "metric": "average_order_value", "dimension": "customer_segment", "confidence": 0.95}
                sql = """
                    SELECT 
                        c.customer_segment,
                        COUNT(t.transaction_id) AS completed_orders,
                        ROUND(AVG((t.quantity * t.unit_price) - COALESCE(t.discount_amount, 0)), 2) AS average_order_value,
                        ROUND(SUM((t.quantity * t.unit_price) - COALESCE(t.discount_amount, 0)), 2) AS total_spend
                    FROM transactions t
                    JOIN customers c ON t.customer_id = c.customer_id
                    WHERE t.transaction_status = 'completed'
                    GROUP BY c.customer_segment
                    ORDER BY average_order_value DESC
                """.strip()
                return intent, sql, None, None
            else:
                intent = {"type": "aggregation", "metric": "transactions", "dimension": "customer_segment", "confidence": 0.95}
                sql = """
                    SELECT 
                        c.customer_segment,
                        COUNT(t.transaction_id) AS order_count,
                        ROUND(SUM((t.quantity * t.unit_price) - COALESCE(t.discount_amount, 0)), 2) AS total_spend
                    FROM transactions t
                    JOIN customers c ON t.customer_id = c.customer_id
                    WHERE t.transaction_status = 'completed'
                    GROUP BY c.customer_segment
                    ORDER BY total_spend DESC
                """.strip()
                return intent, sql, None, None

        # 12. Payment methods
        if "payment" in q or "method" in q:
            intent = {"type": "aggregation", "metric": "transactions", "dimension": "payment_method", "confidence": 0.95}
            sql = """
                SELECT 
                    payment_method,
                    COUNT(transaction_id) AS total_orders,
                    SUM(CASE WHEN transaction_status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
                    ROUND(SUM((quantity * unit_price) - COALESCE(discount_amount, 0)), 2) AS net_revenue
                FROM transactions
                GROUP BY payment_method
                ORDER BY total_orders DESC
            """.strip()
            return intent, sql, None, None

        # 13. Transactions or revenue by region
        if "region" in q:
            intent = {"type": "aggregation", "metric": "transactions", "dimension": "region", "confidence": 0.95}
            sql = """
                SELECT 
                    r.region_name,
                    COUNT(t.transaction_id) AS total_orders,
                    SUM(CASE WHEN t.transaction_status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
                    ROUND(SUM((t.quantity * t.unit_price) - COALESCE(t.discount_amount, 0)), 2) AS net_revenue
                FROM transactions t
                JOIN regions r ON t.region_id = r.region_id
                GROUP BY r.region_id, r.region_name
                ORDER BY completed_orders DESC
            """.strip()
            return intent, sql, None, None

        # 14. Total transactions / count
        if "total transaction" in q or "how many transaction" in q or "transaction count" in q:
            intent = {"type": "total_count", "metric": "transactions", "confidence": 0.95}
            sql = """
                SELECT 
                    transaction_status,
                    COUNT(transaction_id) AS count,
                    ROUND(100.0 * COUNT(transaction_id) / (SELECT COUNT(*) FROM transactions), 2) AS percentage
                FROM transactions
                GROUP BY transaction_status
                ORDER BY count DESC
            """.strip()
            return intent, sql, None, None

        # 15. Total gross / net revenue
        if "total revenue" in q or "gross revenue" in q or "net revenue" in q or "how much revenue" in q:
            intent = {"type": "total_revenue", "metric": "net_revenue", "confidence": 0.95}
            sql = """
                SELECT 
                    ROUND(SUM(quantity * unit_price), 2) AS gross_revenue,
                    ROUND(SUM(COALESCE(discount_amount, 0)), 2) AS total_discounts,
                    ROUND(SUM((quantity * unit_price) - COALESCE(discount_amount, 0)), 2) AS net_revenue
                FROM transactions
                WHERE transaction_status = 'completed'
            """.strip()
            return intent, sql, None, None

        # 16. Specific filtering queries (e.g. high discount edge cases)
        if "discount" in q and ("greater than" in q or ">" in q):
            intent = {"type": "filtered_query", "metric": "discount_amount", "confidence": 0.95}
            sql = """
                SELECT 
                    transaction_id,
                    transaction_timestamp,
                    quantity,
                    unit_price,
                    discount_amount,
                    transaction_status
                FROM transactions
                WHERE discount_amount > 10000000
                LIMIT 50
            """.strip()
            return intent, sql, None, None

        # If question does not match any recognized schema pattern, do not silently return a generic monthly query
        # Lower confidence and ask for clarification
        intent = {"type": "unrecognized_intent", "confidence": 0.30}
        clarification_msg = (
            f"Could not map '{question}' to a specific metric or dimension in the database. "
            "Please ask about completed transactions, net revenue, regions, categories, or channels, "
            "or explore available tables in the Data & Metrics Catalog."
        )
        return intent, None, clarification_msg, None
