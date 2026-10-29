"""
Pydantic API request and response schemas for QueryLens AI.
"""
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., description="The user's natural language business question")
    session_id: Optional[str] = Field(None, description="Optional conversation session ID")
    execution_mode: Optional[str] = Field("auto", description="Execution mode: auto, llm, fallback")


class SQLValidateRequest(BaseModel):
    sql: str = Field(..., description="Raw SQL query string to validate")


class ContributingFactor(BaseModel):
    dimension: str = Field(..., description="E.g. Region, Product Category, Channel")
    segment: str = Field(..., description="E.g. North America - West, Electronics")
    baseline_value: float = Field(..., description="Value in baseline period")
    current_value: float = Field(..., description="Value in current period")
    delta: float = Field(..., description="current_value - baseline_value")
    percentage_change: float = Field(..., description="Percentage change in segment")
    contribution_to_total_drop_pct: float = Field(
        ..., description="Share of total change accounted for by this segment"
    )
    is_anomaly: bool = Field(False, description="Whether this segment triggered anomaly detection")
    note: Optional[str] = None


class ChartSeries(BaseModel):
    data_key: str
    name: str
    color: Optional[str] = None


class ChartSpec(BaseModel):
    chart_type: str = Field(..., description="line, bar, grouped_bar, area, pie, or table")
    title: str
    x_axis_key: Optional[str] = None
    y_axis_key: Optional[str] = None
    series: List[ChartSeries] = []
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    unit: Optional[str] = None
    highlight_anomalies: bool = False


class MetricCard(BaseModel):
    label: str
    value: Union[str, float, int]
    change_pct: Optional[float] = None
    comparison_label: Optional[str] = None
    sentiment: Optional[str] = "neutral"  # positive, negative, neutral


class QueryResponse(BaseModel):
    request_id: str
    question: str
    interpreted_intent: Dict[str, Any]
    clarification_required: bool = False
    clarification_message: Optional[str] = None
    assumptions: List[str] = []
    sql: str
    query_status: str  # success, error, rejected, clarification
    execution_time_ms: float = 0.0
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    metric_cards: List[MetricCard] = []
    chart_spec: Optional[ChartSpec] = None
    summary: str
    key_findings: List[str] = []
    contributing_factors: List[ContributingFactor] = []
    data_quality_warnings: List[str] = []
    limitations: List[str] = []
    execution_mode: str  # llm or fallback
    follow_up_questions: List[str] = []
    confidence_score: float = 1.0
    confidence_reasoning: str = ""


class SchemaColumn(BaseModel):
    name: str
    type: str
    primary_key: bool = False
    foreign_key: Optional[str] = None
    description: str


class SchemaTable(BaseModel):
    table_name: str
    description: str
    columns: List[SchemaColumn]


class MetricDefinition(BaseModel):
    metric_id: str
    name: str
    formula: str
    business_meaning: str
    default_table: str
    default_filter: Optional[str] = None


class BenchmarkTestCase(BaseModel):
    test_id: str
    question: str
    difficulty: str  # easy, medium, hard, safety, edge_case
    category: str
    expected_intent: str
    expected_sql: Optional[str] = None
    expected_behavior: str  # execute_success, reject_unsafe, require_clarification, explain_unsupported
    notes: Optional[str] = None


class BenchmarkResultItem(BaseModel):
    test_id: str
    question: str
    difficulty: str
    category: str
    passed: bool
    execution_status: str
    safety_check_passed: bool
    result_correctness: bool
    semantic_correctness: bool
    insight_faithfulness: bool
    latency_ms: float
    generated_sql: Optional[str] = None
    failure_reason: Optional[str] = None


class BenchmarkSummary(BaseModel):
    total_tests: int
    passed_tests: int
    overall_accuracy_pct: float
    execution_accuracy_pct: float
    result_correctness_pct: float
    semantic_correctness_pct: float
    sql_safety_rate_pct: float
    insight_faithfulness_pct: float
    average_latency_ms: float
    execution_mode: str
    timestamp: str
    results: List[BenchmarkResultItem] = []
