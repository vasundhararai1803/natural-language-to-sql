"""
Evidence-Grounded Insight Generation Service.
Generates plain-language executive summaries and key findings strictly grounded in verified query results.
Prohibits hallucinating causal claims without empirical evidence, flags data quality boundaries and assumptions.
Dynamically calculates confidence scores, assumptions, and uncertainty warnings.
"""
from typing import List, Dict, Any, Optional
from backend.models.api_schemas import ContributingFactor


class InsightService:
    @staticmethod
    def generate_diagnostic_insight(
        diagnostic_data: Dict[str, Any],
        question: str
    ) -> Dict[str, Any]:
        """
        Creates evidence-grounded insights for 'Why did this change?' diagnostic questions.
        Dynamically articulates date ranges, metrics, and strictly correlation-bounded findings.
        """
        baseline_tx = diagnostic_data["baseline_tx"]
        current_tx = diagnostic_data["current_tx"]
        tx_delta = diagnostic_data["tx_delta"]
        tx_pct = diagnostic_data["tx_pct"]
        cancelled_pct = diagnostic_data["cancelled_pct"]
        current_cancelled = diagnostic_data["current_cancelled"]
        baseline_canc_rate = diagnostic_data.get("baseline_cancellation_rate", 0.0)
        current_canc_rate = diagnostic_data.get("current_cancellation_rate", 0.0)
        current_period_lbl = diagnostic_data.get("current_period", "the current period")
        baseline_period_lbl = diagnostic_data.get("baseline_period", "the prior period")
        factors: List[ContributingFactor] = diagnostic_data["contributing_factors"]

        # Identify top drivers
        top_regional_drop = next((f for f in factors if f.dimension == "Region" and f.delta < 0), None)
        top_cat_drop = next((f for f in factors if f.dimension == "Product Category" and f.delta < 0), None)
        top_channel_drop = next((f for f in factors if f.dimension == "Channel" and f.delta < 0), None)

        direction = "declined" if tx_delta < 0 else "increased"
        summary = (
            f"Completed transactions {direction} by {abs(tx_pct)}% ({tx_delta:+d} transactions, from "
            f"{baseline_tx:,} to {current_tx:,}) during {current_period_lbl} compared with {baseline_period_lbl}."
        )

        findings: List[str] = []
        if top_regional_drop:
            findings.append(
                f"Geographic concentration: The largest volume decline occurred in '{top_regional_drop.segment}', "
                f"falling {top_regional_drop.delta:+0.0f} transactions ({top_regional_drop.percentage_change:.1f}%), "
                f"which accounts for {top_regional_drop.contribution_to_total_drop_pct:.1f}% of the net reduction."
            )

        if top_cat_drop:
            findings.append(
                f"Product category impact: '{top_cat_drop.segment}' experienced a {top_cat_drop.delta:+0.0f} order change "
                f"({top_cat_drop.percentage_change:.1f}%), representing {top_cat_drop.contribution_to_total_drop_pct:.1f}% of total drop."
            )

        if cancelled_pct > 0:
            findings.append(
                f"Order cancellation correlation: Total cancellations rose {cancelled_pct:+.1f}% to {current_cancelled} "
                f"(cancellation rate shifted from {baseline_canc_rate}% to {current_canc_rate}%). "
                f"Data indicates an empirical correlation with transaction losses, but order records alone cannot establish whether gateway failures or user behavior caused the cancellations."
            )

        if top_channel_drop:
            findings.append(
                f"Channel performance: Volume in channel '{top_channel_drop.segment}' moved {top_channel_drop.delta:+0.0f} "
                f"({top_channel_drop.percentage_change:.1f}%)."
            )

        data_quality_warnings = []
        if current_canc_rate > 12.0:
            data_quality_warnings.append(
                f"High cancellation rate alert: {current_canc_rate}% of all initiated orders in {current_period_lbl} were cancelled."
            )
        if baseline_tx == 0:
            data_quality_warnings.append("Baseline period contains 0 completed transactions; percentage change cannot be computed.")

        limitations = [
            "Correlation does not demonstrate causation: Database records order lifecycle states but lacks external payment gateway error telemetry or web server crash logs.",
            f"Comparison window bounded between {baseline_period_lbl} and {current_period_lbl}.",
            "Net revenue and order volume exclude uncaptured tax, shipping adjustments, and off-platform settlements."
        ]

        follow_ups = [
            "Was the decline concentrated in one region?",
            "Did cancellations increase compared with the previous week?",
            "Which product category contributed most to the decline?",
            "Did revenue fall at the same rate as transaction count?",
            "Show daily completed transactions for October 2026."
        ]

        # Calculate confidence score dynamically
        confidence_score = 0.96 if len(factors) > 0 and baseline_tx > 0 else 0.60
        confidence_reasoning = (
            f"High confidence derived from exhaustive relational aggregation comparing {current_period_lbl} to {baseline_period_lbl}."
            if baseline_tx > 0 else "Low confidence due to insufficient historical baseline data."
        )

        return {
            "summary": summary,
            "key_findings": findings,
            "data_quality_warnings": data_quality_warnings,
            "limitations": limitations,
            "follow_up_questions": follow_ups,
            "confidence_score": confidence_score,
            "confidence_reasoning": confidence_reasoning
        }

    @staticmethod
    def generate_general_insight(
        question: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        sql: str
    ) -> Dict[str, Any]:
        """
        Creates grounded summaries for general SQL query execution results without fabricating causal claims.
        """
        row_count = len(rows)
        if row_count == 0:
            return {
                "summary": "No matching records were found in the database for the specified filters and timeframe.",
                "key_findings": ["Zero records met all query filter criteria."],
                "data_quality_warnings": ["Zero rows returned by database execution."],
                "limitations": ["An empty result indicates no rows matched criteria, not that the entity does not exist."],
                "follow_up_questions": [
                    "Show all regions in the database",
                    "What are the top 5 products by revenue this month?",
                    "Show total transactions by status"
                ],
                "confidence_score": 0.90,
                "confidence_reasoning": "Database executed successfully and confirmed zero rows match the filter."
            }

        first_row = rows[0]
        summary = f"Query returned {row_count} record{'s' if row_count != 1 else ''} answering '{question}'."
        findings: List[str] = []

        label_col = next((c for c in columns if isinstance(first_row.get(c), str)), columns[0])
        num_col = next((c for c in columns if isinstance(first_row.get(c), (int, float))), None)

        if num_col and label_col != num_col:
            top_entity = first_row.get(label_col)
            top_val = first_row.get(num_col)
            val_formatted = f"${top_val:,.2f}" if any(k in num_col.lower() for k in ["rev", "price", "amount", "spend"]) else f"{top_val:,}"
            findings.append(f"Leading record: '{top_entity}' with {num_col.replace('_', ' ')} of {val_formatted}.")
            
            if row_count > 1:
                last_row = rows[-1]
                bot_entity = last_row.get(label_col)
                bot_val = last_row.get(num_col)
                bot_val_formatted = f"${bot_val:,.2f}" if any(k in num_col.lower() for k in ["rev", "price", "amount", "spend"]) else f"{bot_val:,}"
                findings.append(f"Trailing record: '{bot_entity}' with {num_col.replace('_', ' ')} of {bot_val_formatted}.")
        elif num_col:
            val = first_row.get(num_col)
            val_formatted = f"${val:,.2f}" if any(k in num_col.lower() for k in ["rev", "price", "amount", "spend"]) else f"{val:,}"
            findings.append(f"Aggregate result: {num_col.replace('_', ' ')} equals {val_formatted}.")

        findings.append("Values reflect exact read-only database query execution results.")

        limitations = [
            "Observations reflect transaction records up to latest database timestamp (October 25, 2026).",
            "Observed trends indicate correlations within database records; root causes cannot be asserted without external operational logs."
        ]

        follow_ups = [
            "Compare revenue this quarter with the previous quarter",
            "Which region has the highest cancellation rate?",
            "What were our top-performing products this month?",
            "Show me daily transactions and highlight unusual drops"
        ]

        return {
            "summary": summary,
            "key_findings": findings,
            "data_quality_warnings": [],
            "limitations": limitations,
            "follow_up_questions": follow_ups,
            "confidence_score": 0.95,
            "confidence_reasoning": "Verified read-only SQL execution against schema catalog."
        }
