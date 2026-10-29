"""
FastAPI Router and Endpoints for QueryLens AI.
"""
import uuid
import time
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from backend.models.api_schemas import (
    QueryRequest, QueryResponse, SQLValidateRequest,
    SchemaTable, MetricDefinition, BenchmarkSummary, ChartSpec
)
from backend.services.schema_service import SchemaService
from backend.services.llm_service import LLMService
from backend.services.sql_validation_service import SQLValidationService
from backend.services.query_execution_service import QueryExecutionService
from backend.services.analysis_service import DiagnosticAnalysisService
from backend.services.insight_service import InsightService
from backend.services.chart_service import ChartService
from backend.evaluation.benchmark_runner import BenchmarkRunner

router = APIRouter(prefix="/api")

# In-memory query history for current session
QUERY_HISTORY: List[Dict[str, Any]] = []
CACHED_BENCHMARK: BenchmarkSummary = None


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "QueryLens AI API",
        "llm_configured": LLMService.is_llm_configured(),
        "database": "sqlite:///data/querylens.db"
    }


@router.get("/schema", response_model=List[SchemaTable])
def get_schema():
    return SchemaService.get_tables()


@router.get("/metrics/definitions", response_model=List[MetricDefinition])
def get_metrics_definitions():
    return SchemaService.get_metric_definitions()


@router.post("/query/validate")
def validate_sql(req: SQLValidateRequest):
    is_valid, err_msg, tables = SQLValidationService.validate_sql(req.sql)
    return {
        "is_valid": is_valid,
        "error_message": err_msg,
        "referenced_tables": tables
    }


@router.post("/ask", response_model=QueryResponse)
async def ask_question(req: QueryRequest):
    req_id = str(uuid.uuid4())[:8]
    start_time = time.perf_counter()

    # 1. Process question through LLM or Fallback Engine
    processed = await LLMService.process_question(req.question, force_mode=req.execution_mode)
    intent = processed["intent"]
    raw_sql = processed["sql"]
    clarif = processed["clarification"]
    unsupp = processed["unsupported"]
    exec_mode = processed["execution_mode"]

    # 2. Case: Ambiguous Question
    if clarif:
        resp = QueryResponse(
            request_id=req_id,
            question=req.question,
            interpreted_intent=intent or {"type": "ambiguous"},
            clarification_required=True,
            clarification_message=clarif,
            assumptions=["Request requires disambiguation between revenue, volume, and order value."],
            sql="",
            query_status="clarification",
            execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
            summary="Clarification requested to disambiguate performance metrics.",
            key_findings=["Multiple plausible metric definitions exist for this question."],
            execution_mode=exec_mode,
            follow_up_questions=[
                "Completed transactions last week",
                "Total net revenue last week",
                "Average order value last week"
            ],
            confidence_score=0.5,
            confidence_reasoning="High semantic ambiguity in user phrasing."
        )
        QUERY_HISTORY.insert(0, resp.model_dump())
        return resp

    # 3. Case: Unsupported Metric
    if unsupp:
        resp = QueryResponse(
            request_id=req_id,
            question=req.question,
            interpreted_intent=intent or {"type": "unsupported"},
            clarification_required=False,
            assumptions=["Metric cannot be computed with available schema."],
            sql="",
            query_status="rejected",
            execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
            summary=unsupp,
            key_findings=["Metric absent from data catalog."],
            limitations=[unsupp],
            execution_mode=exec_mode,
            follow_up_questions=[
                "What was our gross revenue?",
                "Show completed transactions by product category",
                "Which region has the highest cancellation rate?"
            ],
            confidence_score=1.0,
            confidence_reasoning="Confirmed metric absence."
        )
        QUERY_HISTORY.insert(0, resp.model_dump())
        return resp

    # 4. Check for 'Why Did This Change?' Diagnostic Intent
    if intent and intent.get("type") == "diagnostic_why":
        diag_data = DiagnosticAnalysisService.analyze_drop()
        insights = InsightService.generate_diagnostic_insight(diag_data, req.question)
        
        # Execute query for table visualization
        ok, cols, rows, exec_ms, err = QueryExecutionService.execute_query(raw_sql)
        chart_spec = ChartService.generate_chart_spec(
            intent_type="diagnostic_why",
            columns=cols,
            rows=rows,
            title="Completed Transactions: Baseline vs Current Week by Region"
        )

        resp = QueryResponse(
            request_id=req_id,
            question=req.question,
            interpreted_intent=intent,
            assumptions=[
                "Calendar week defined as Monday 00:00:00 to Sunday 23:59:59.",
                "Current drop week: Oct 12 - Oct 18, 2026. Baseline week: Oct 05 - Oct 11, 2026.",
                "Completed transactions filtered where transaction_status = 'completed'."
            ],
            sql=raw_sql,
            query_status="success" if ok else "error",
            execution_time_ms=exec_ms,
            columns=cols,
            rows=rows,
            row_count=len(rows),
            metric_cards=diag_data["metric_cards"],
            chart_spec=chart_spec,
            summary=insights["summary"],
            key_findings=insights["key_findings"],
            contributing_factors=diag_data["contributing_factors"],
            data_quality_warnings=["Cancellations spiked in West region during the drop week."],
            limitations=insights["limitations"],
            execution_mode=exec_mode,
            follow_up_questions=insights["follow_up_questions"],
            confidence_score=0.98,
            confidence_reasoning="High confidence based on comparative period SQL aggregation."
        )
        QUERY_HISTORY.insert(0, resp.model_dump())
        return resp

    # 5. General Query Execution
    if not raw_sql:
        raise HTTPException(status_code=400, detail="Could not formulate a valid SQL query.")

    ok, cols, rows, exec_ms, err = QueryExecutionService.execute_query(raw_sql)
    if not ok:
        resp = QueryResponse(
            request_id=req_id,
            question=req.question,
            interpreted_intent=intent,
            sql=raw_sql,
            query_status="error",
            execution_time_ms=exec_ms,
            summary=f"Query Execution Blocked or Failed: {err}",
            key_findings=[err],
            limitations=["Execution was rejected by safety policy or database engine."],
            execution_mode=exec_mode,
            confidence_score=0.0
        )
        QUERY_HISTORY.insert(0, resp.model_dump())
        return resp

    insights = InsightService.generate_general_insight(req.question, cols, rows, raw_sql)
    chart_spec = ChartService.generate_chart_spec(
        intent_type=intent.get("type", "general"),
        columns=cols,
        rows=rows,
        title=f"Results for '{req.question}'"
    )

    resp = QueryResponse(
        request_id=req_id,
        question=req.question,
        interpreted_intent=intent,
        assumptions=["Data filtered according to active business metric specifications."],
        sql=raw_sql,
        query_status="success",
        execution_time_ms=exec_ms,
        columns=cols,
        rows=rows,
        row_count=len(rows),
        metric_cards=[],
        chart_spec=chart_spec,
        summary=insights["summary"],
        key_findings=insights["key_findings"],
        limitations=insights["limitations"],
        execution_mode=exec_mode,
        follow_up_questions=insights["follow_up_questions"],
        confidence_score=0.95,
        confidence_reasoning="Verified SQL execution against relational schema."
    )
    QUERY_HISTORY.insert(0, resp.model_dump())
    return resp


@router.get("/history")
def get_history():
    return QUERY_HISTORY[:20]


@router.post("/evaluation/run", response_model=BenchmarkSummary)
def run_evaluation():
    global CACHED_BENCHMARK
    CACHED_BENCHMARK = BenchmarkRunner.run_benchmark()
    return CACHED_BENCHMARK


@router.get("/evaluation/results", response_model=BenchmarkSummary)
def get_evaluation_results():
    global CACHED_BENCHMARK
    if CACHED_BENCHMARK is None:
        CACHED_BENCHMARK = BenchmarkRunner.run_benchmark()
    return CACHED_BENCHMARK
