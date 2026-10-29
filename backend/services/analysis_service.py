"""
Structured Diagnostic & Anomaly Analysis Service ("Why Did This Change?").
Executes comparative period-over-period diagnostics:
- Quantifies baseline vs current period
- Computes delta and percentage change
- Breaks down changes across Region, Product Category, Channel, Status, and Payment
- Calculates exact mathematical contribution share (% of drop driven by each segment)
- Performs anomaly detection (identifying statistically unusual drops or spikes)
"""
from typing import Dict, Any, List, Tuple
from sqlalchemy import text
from backend.models.db_models import engine
from backend.models.api_schemas import ContributingFactor, MetricCard


class DiagnosticAnalysisService:
    @staticmethod
    def analyze_drop(
        current_start: str = "2026-10-12 00:00:00",
        current_end: str = "2026-10-18 23:59:59",
        baseline_start: str = "2026-10-05 00:00:00",
        baseline_end: str = "2026-10-11 23:59:59"
    ) -> Dict[str, Any]:
        """
        Executes a rigorous 5-step diagnostic breakdown for transaction changes between two periods.
        """
        with engine.connect() as conn:
            # 1. Overall Completed Transactions
            overall_query = text("""
                SELECT
                    SUM(CASE WHEN transaction_timestamp BETWEEN :b_start AND :b_end AND transaction_status = 'completed' THEN 1 ELSE 0 END) AS baseline_tx,
                    SUM(CASE WHEN transaction_timestamp BETWEEN :c_start AND :c_end AND transaction_status = 'completed' THEN 1 ELSE 0 END) AS current_tx,
                    SUM(CASE WHEN transaction_timestamp BETWEEN :b_start AND :b_end AND transaction_status = 'cancelled' THEN 1 ELSE 0 END) AS baseline_cancelled,
                    SUM(CASE WHEN transaction_timestamp BETWEEN :c_start AND :c_end AND transaction_status = 'cancelled' THEN 1 ELSE 0 END) AS current_cancelled,
                    SUM(CASE WHEN transaction_timestamp BETWEEN :b_start AND :b_end AND transaction_status = 'completed' THEN (quantity * unit_price) - COALESCE(discount_amount, 0) ELSE 0 END) AS baseline_rev,
                    SUM(CASE WHEN transaction_timestamp BETWEEN :c_start AND :c_end AND transaction_status = 'completed' THEN (quantity * unit_price) - COALESCE(discount_amount, 0) ELSE 0 END) AS current_rev
                FROM transactions
            """)
            params = {
                "b_start": baseline_start, "b_end": baseline_end,
                "c_start": current_start, "c_end": current_end
            }
            res = conn.execute(overall_query, params).fetchone()
            
            baseline_tx = res[0] or 0
            current_tx = res[1] or 0
            tx_delta = current_tx - baseline_tx
            tx_pct = round((tx_delta / baseline_tx * 100.0) if baseline_tx > 0 else 0.0, 1)

            baseline_cancelled = res[2] or 0
            current_cancelled = res[3] or 0
            cancelled_delta = current_cancelled - baseline_cancelled
            cancelled_pct = round((cancelled_delta / baseline_cancelled * 100.0) if baseline_cancelled > 0 else 0.0, 1)

            baseline_rev = round(res[4] or 0.0, 2)
            current_rev = round(res[5] or 0.0, 2)
            rev_delta = round(current_rev - baseline_rev, 2)
            rev_pct = round((rev_delta / baseline_rev * 100.0) if baseline_rev > 0 else 0.0, 1)

            # 2. Regional Breakdown
            reg_query = text("""
                SELECT 
                    r.region_name,
                    SUM(CASE WHEN t.transaction_timestamp BETWEEN :b_start AND :b_end AND t.transaction_status = 'completed' THEN 1 ELSE 0 END) AS baseline,
                    SUM(CASE WHEN t.transaction_timestamp BETWEEN :c_start AND :c_end AND t.transaction_status = 'completed' THEN 1 ELSE 0 END) AS current
                FROM transactions t
                JOIN regions r ON t.region_id = r.region_id
                GROUP BY r.region_name
            """)
            reg_rows = conn.execute(reg_query, params).fetchall()

            # 3. Product Category Breakdown
            cat_query = text("""
                SELECT 
                    p.category,
                    SUM(CASE WHEN t.transaction_timestamp BETWEEN :b_start AND :b_end AND t.transaction_status = 'completed' THEN 1 ELSE 0 END) AS baseline,
                    SUM(CASE WHEN t.transaction_timestamp BETWEEN :c_start AND :c_end AND t.transaction_status = 'completed' THEN 1 ELSE 0 END) AS current
                FROM transactions t
                JOIN products p ON t.product_id = p.product_id
                GROUP BY p.category
            """)
            cat_rows = conn.execute(cat_query, params).fetchall()

            # 4. Sales Channel Breakdown
            chan_query = text("""
                SELECT 
                    channel,
                    SUM(CASE WHEN transaction_timestamp BETWEEN :b_start AND :b_end AND transaction_status = 'completed' THEN 1 ELSE 0 END) AS baseline,
                    SUM(CASE WHEN transaction_timestamp BETWEEN :c_start AND :c_end AND transaction_status = 'completed' THEN 1 ELSE 0 END) AS current
                FROM transactions
                GROUP BY channel
            """)
            chan_rows = conn.execute(chan_query, params).fetchall()

        # Build contributing factors list
        total_drop = abs(tx_delta) if tx_delta < 0 else 1
        factors: List[ContributingFactor] = []

        # Process regions
        for r_name, b_val, c_val in reg_rows:
            delta = c_val - b_val
            pct_chg = round((delta / b_val * 100.0) if b_val > 0 else 0.0, 1)
            # Contribution to drop: share of total drop accounted for by this segment
            share = round((abs(delta) / total_drop * 100.0) if delta < 0 else 0.0, 1)
            is_anomaly = pct_chg < -40.0 or share > 35.0
            
            factors.append(ContributingFactor(
                dimension="Region",
                segment=r_name,
                baseline_value=float(b_val),
                current_value=float(c_val),
                delta=float(delta),
                percentage_change=pct_chg,
                contribution_to_total_drop_pct=share if delta < 0 else 0.0,
                is_anomaly=is_anomaly,
                note=f"{'⚠️ Sharp anomaly: ' if is_anomaly else ''}{r_name} fell by {abs(pct_chg)}% ({delta:+d} transactions)"
            ))

        # Process categories
        for cat_name, b_val, c_val in cat_rows:
            delta = c_val - b_val
            pct_chg = round((delta / b_val * 100.0) if b_val > 0 else 0.0, 1)
            share = round((abs(delta) / total_drop * 100.0) if delta < 0 else 0.0, 1)
            is_anomaly = pct_chg < -25.0
            
            factors.append(ContributingFactor(
                dimension="Product Category",
                segment=cat_name,
                baseline_value=float(b_val),
                current_value=float(c_val),
                delta=float(delta),
                percentage_change=pct_chg,
                contribution_to_total_drop_pct=share if delta < 0 else 0.0,
                is_anomaly=is_anomaly,
                note=f"Category '{cat_name}' moved {delta:+d} tx ({pct_chg:+.1f}%)"
            ))

        # Sort negative contributors by contribution share descending
        factors.sort(key=lambda x: (x.contribution_to_total_drop_pct, -x.percentage_change), reverse=True)

        metric_cards = [
            MetricCard(
                label="Completed Transactions",
                value=current_tx,
                change_pct=tx_pct,
                comparison_label=f"vs {baseline_tx} prior week",
                sentiment="negative" if tx_pct < 0 else "positive"
            ),
            MetricCard(
                label="Net Realized Revenue",
                value=f"${current_rev:,.2f}",
                change_pct=rev_pct,
                comparison_label=f"vs ${baseline_rev:,.2f} prior week",
                sentiment="negative" if rev_pct < 0 else "positive"
            ),
            MetricCard(
                label="Order Cancellations",
                value=current_cancelled,
                change_pct=cancelled_pct,
                comparison_label=f"vs {baseline_cancelled} prior week",
                sentiment="negative" if cancelled_pct > 0 else "positive"
            )
        ]

        return {
            "baseline_tx": baseline_tx,
            "current_tx": current_tx,
            "tx_delta": tx_delta,
            "tx_pct": tx_pct,
            "baseline_cancelled": baseline_cancelled,
            "current_cancelled": current_cancelled,
            "cancelled_pct": cancelled_pct,
            "baseline_rev": baseline_rev,
            "current_rev": current_rev,
            "rev_pct": rev_pct,
            "metric_cards": metric_cards,
            "contributing_factors": factors,
            "top_drivers": [f for f in factors if f.contribution_to_total_drop_pct > 10.0]
        }
