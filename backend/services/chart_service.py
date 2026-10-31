"""
Chart Specification Generation Service.
Generates declarative, type-safe visualization configurations based on query intent and result data shape.
Never outputs raw executable javascript; uses structured schemas consumable by Recharts in the frontend.
Safely falls back to a table specification if chart creation fails or cannot be cleanly determined.
"""
from typing import List, Dict, Any, Optional
from backend.models.api_schemas import ChartSpec, ChartSeries


class ChartService:
    @staticmethod
    def generate_chart_spec(
        intent_type: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
        title: Optional[str] = None
    ) -> Optional[ChartSpec]:
        """
        Determines the optimal visualization configuration based on columns and data.
        Falls back safely to a table view if generation fails or conditions are not met.
        """
        if not rows or not columns:
            return None

        try:
            col_lower = [c.lower() for c in columns]

            # Case 1: Time series / Daily trend (date/timestamp column present)
            date_col = next((c for c in columns if any(k in c.lower() for k in ["date", "time", "day", "month", "week"])), None)
            num_cols = [c for c in columns if c != date_col and isinstance(rows[0].get(c), (int, float))]

            if date_col and num_cols:
                series = []
                palette = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b"]
                for idx, n_col in enumerate(num_cols[:3]):
                    clean_name = n_col.replace("_", " ").title()
                    series.append(ChartSeries(data_key=n_col, name=clean_name, color=palette[idx % len(palette)]))

                return ChartSpec(
                    chart_type="line",
                    title=title or f"Trend Analysis by {date_col.replace('_', ' ').title()}",
                    x_axis_key=date_col,
                    y_axis_key=num_cols[0],
                    series=series,
                    x_label="Timeline",
                    y_label="Value",
                    highlight_anomalies=True
                )

            # Case 2: Categorical comparison (e.g. region_name, category, channel)
            cat_col = next((c for c in columns if any(k in c.lower() for k in ["region", "category", "channel", "method", "status", "product", "segment", "country", "quarter"])), None)
            if not cat_col:
                cat_col = next((c for c in columns if isinstance(rows[0].get(c), str)), columns[0])

            val_cols = [c for c in columns if c != cat_col and isinstance(rows[0].get(c), (int, float))]

            if cat_col and val_cols:
                # If multiple metric columns (e.g. baseline vs current), grouped bar
                if len(val_cols) >= 2 and any("baseline" in c.lower() or "current" in c.lower() for c in val_cols):
                    return ChartSpec(
                        chart_type="grouped_bar",
                        title=title or f"Comparison Breakdown by {cat_col.replace('_', ' ').title()}",
                        x_axis_key=cat_col,
                        y_axis_key=val_cols[0],
                        series=[
                            ChartSeries(data_key=val_cols[0], name="Baseline Period", color="#94a3b8"),
                            ChartSeries(data_key=val_cols[1], name="Current Period", color="#3b82f6"),
                        ],
                        x_label=cat_col.replace("_", " ").title(),
                        y_label="Count / Amount"
                    )

                # Single value column (or default to first metric column)
                # If small set of categories (1 to 4) and proportional metric, generate pie; otherwise bar
                is_proportional = any(k in val_cols[0].lower() for k in ["share", "pct", "rate", "percentage", "ratio"])
                if 1 <= len(rows) <= 4 and is_proportional:
                    chart_type = "pie"
                else:
                    chart_type = "bar"

                return ChartSpec(
                    chart_type=chart_type,
                    title=title or f"Distribution by {cat_col.replace('_', ' ').title()}",
                    x_axis_key=cat_col,
                    y_axis_key=val_cols[0],
                    series=[
                        ChartSeries(data_key=val_cols[0], name=val_cols[0].replace("_", " ").title(), color="#3b82f6")
                    ],
                    x_label=cat_col.replace("_", " ").title(),
                    y_label=val_cols[0].replace("_", " ").title()
                )

            # Fallback to tabular view
            return ChartSpec(
                chart_type="table",
                title=title or "Data Table View",
                x_axis_key=columns[0] if columns else "data",
                series=[]
            )

        except Exception:
            # Fallback to table specification if any error occurs
            return ChartSpec(
                chart_type="table",
                title=title or "Data Table View",
                x_axis_key=columns[0] if columns else "data",
                series=[]
            )
