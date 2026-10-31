"""
Schema Discovery and Business Metric Definitions service.
Provides introspectable metadata to the AI engine and the frontend UI.
"""
from typing import List, Dict, Any
from backend.models.api_schemas import SchemaTable, SchemaColumn, MetricDefinition

ALLOWED_TABLES = {"transactions", "products", "customers", "regions"}

SCHEMA_COLUMNS_BY_TABLE: Dict[str, set] = {
    "transactions": {
        "transaction_id", "transaction_timestamp", "customer_id", "product_id",
        "region_id", "quantity", "unit_price", "discount_amount",
        "transaction_status", "payment_method", "channel"
    },
    "products": {
        "product_id", "product_name", "category", "subcategory"
    },
    "customers": {
        "customer_id", "customer_segment", "signup_date"
    },
    "regions": {
        "region_id", "region_name", "country"
    }
}

METRIC_DEFINITIONS: List[MetricDefinition] = [
    MetricDefinition(
        metric_id="completed_transactions",
        name="Completed Transactions",
        formula="COUNT(transaction_id) WHERE transaction_status = 'completed'",
        business_meaning="Number of successfully finalized customer purchase orders. Does not include cancelled, refunded, or pending orders.",
        default_table="transactions",
        default_filter="transaction_status = 'completed'"
    ),
    MetricDefinition(
        metric_id="gross_revenue",
        name="Gross Revenue ($)",
        formula="SUM(quantity * unit_price) WHERE transaction_status = 'completed'",
        business_meaning="Total monetary value of merchandise sold before applying any discounts or refunds.",
        default_table="transactions",
        default_filter="transaction_status = 'completed'"
    ),
    MetricDefinition(
        metric_id="net_revenue",
        name="Net Revenue ($)",
        formula="SUM((quantity * unit_price) - COALESCE(discount_amount, 0)) WHERE transaction_status = 'completed'",
        business_meaning="Effective revenue realized after deducting discounts for completed orders.",
        default_table="transactions",
        default_filter="transaction_status = 'completed'"
    ),
    MetricDefinition(
        metric_id="cancellation_rate",
        name="Cancellation Rate (%)",
        formula="100.0 * COUNT(CASE WHEN transaction_status = 'cancelled' THEN 1 END) / COUNT(transaction_id)",
        business_meaning="Percentage of initiated orders that were cancelled prior to fulfillment.",
        default_table="transactions"
    ),
    MetricDefinition(
        metric_id="average_order_value",
        name="Average Order Value (AOV) ($)",
        formula="AVG((quantity * unit_price) - COALESCE(discount_amount, 0)) WHERE transaction_status = 'completed'",
        business_meaning="Average net spend per completed transaction.",
        default_table="transactions",
        default_filter="transaction_status = 'completed'"
    ),
    MetricDefinition(
        metric_id="total_units_sold",
        name="Total Units Sold",
        formula="SUM(quantity) WHERE transaction_status = 'completed'",
        business_meaning="Aggregate physical or license item units fulfilled.",
        default_table="transactions",
        default_filter="transaction_status = 'completed'"
    )
]

TABLES_METADATA: List[SchemaTable] = [
    SchemaTable(
        table_name="transactions",
        description="Core ledger recording all customer purchases, order status, quantities, prices, and channels.",
        columns=[
            SchemaColumn(name="transaction_id", type="INTEGER", primary_key=True, description="Unique transaction identifier"),
            SchemaColumn(name="transaction_timestamp", type="DATETIME", description="UTC timestamp of the order (2026-08-01 to 2026-10-25)"),
            SchemaColumn(name="customer_id", type="INTEGER", foreign_key="customers.customer_id", description="ID of purchasing customer"),
            SchemaColumn(name="product_id", type="INTEGER", foreign_key="products.product_id", description="ID of purchased item"),
            SchemaColumn(name="region_id", type="INTEGER", foreign_key="regions.region_id", description="ID of geographic sales region"),
            SchemaColumn(name="quantity", type="INTEGER", description="Number of units purchased (1 to 10)"),
            SchemaColumn(name="unit_price", type="FLOAT", description="Unit list price in USD at purchase time"),
            SchemaColumn(name="discount_amount", type="FLOAT", description="Promotional or discount dollar deduction"),
            SchemaColumn(name="transaction_status", type="VARCHAR(30)", description="Status: 'completed', 'cancelled', 'refunded', 'pending'"),
            SchemaColumn(name="payment_method", type="VARCHAR(30)", description="Payment method: 'credit_card', 'bank_transfer', 'paypal', 'crypto'"),
            SchemaColumn(name="channel", type="VARCHAR(30)", description="Acquisition channel: 'web', 'mobile_app', 'direct_sales', 'partner'")
        ]
    ),
    SchemaTable(
        table_name="products",
        description="Catalog of software products, hardware gear, and professional services.",
        columns=[
            SchemaColumn(name="product_id", type="INTEGER", primary_key=True, description="Unique product ID (101-114)"),
            SchemaColumn(name="product_name", type="VARCHAR(100)", description="Human-readable product SKU name"),
            SchemaColumn(name="category", type="VARCHAR(50)", description="Broad category: 'Software', 'Electronics', 'Hardware', 'Services'"),
            SchemaColumn(name="subcategory", type="VARCHAR(50)", description="Detailed subcategory: 'Cloud', 'Analytics', 'Displays', etc.")
        ]
    ),
    SchemaTable(
        table_name="customers",
        description="Registered corporate and individual accounts purchasing products.",
        columns=[
            SchemaColumn(name="customer_id", type="INTEGER", primary_key=True, description="Unique customer ID (1-500)"),
            SchemaColumn(name="customer_segment", type="VARCHAR(50)", description="Segment: 'Enterprise', 'SMB', 'Consumer', 'VIP'"),
            SchemaColumn(name="signup_date", type="DATETIME", description="Account registration timestamp")
        ]
    ),
    SchemaTable(
        table_name="regions",
        description="Geographic business operating territories and host countries.",
        columns=[
            SchemaColumn(name="region_id", type="INTEGER", primary_key=True, description="Territory ID (1-7)"),
            SchemaColumn(name="region_name", type="VARCHAR(50)", description="Territory label (e.g. North America - West, Europe - Central)"),
            SchemaColumn(name="country", type="VARCHAR(50)", description="Country name")
        ]
    )
]


class SchemaService:
    @staticmethod
    def get_tables() -> List[SchemaTable]:
        return TABLES_METADATA

    @staticmethod
    def get_metric_definitions() -> List[MetricDefinition]:
        return METRIC_DEFINITIONS

    @staticmethod
    def get_allowed_tables() -> set:
        return ALLOWED_TABLES

    @staticmethod
    def get_schema_prompt_context() -> str:
        """Returns a compact textual summary of schema for LLM system prompt."""
        text = "DATABASE SCHEMA:\n"
        for tbl in TABLES_METADATA:
            cols = ", ".join([f"{c.name} ({c.type})" for c in tbl.columns])
            text += f"- Table `{tbl.table_name}`: {tbl.description}\n  Columns: {cols}\n"
        text += "\nBUSINESS METRIC DEFINITIONS:\n"
        for m in METRIC_DEFINITIONS:
            text += f"- {m.name} ({m.metric_id}): {m.formula} | Meaning: {m.business_meaning}\n"
        text += "\nREFERENCE BENCHMARK DATES:\n"
        text += "- Max data timestamp in DB: 2026-10-25 23:59:59\n"
        text += "- 'Last week' (complete calendar week) corresponds to: 2026-10-12 to 2026-10-18\n"
        text += "- 'Previous week' corresponds to: 2026-10-05 to 2026-10-11\n"
        text += "- 'This month' corresponds to: 2026-10-01 to 2026-10-25\n"
        text += "- 'Last month' corresponds to: 2026-09-01 to 2026-09-30\n"
        return text
