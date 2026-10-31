"""
FastAPI Router and Endpoints for QueryLens AI.
"""
import uuid
import time
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
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
from backend.repositories.storage import (
    save_history_entry, get_history_entries,
    save_cached_benchmark, get_cached_benchmark
)

router = APIRouter(prefix="/api")


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "QueryLens AI API",
        "llm_configured": LLMService.is_llm_configured(),
        "database": "sqlite:///data/querylens.db",
        "security": {
            "ast_validation": "enforced",
            "read_only_connection": "enforced",
            "query_only_pragma": "enforced"
        }
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
async def ask_question(req: QueryRequest, request: Request):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])
    start_time = time.perf_counter()

    # 1. Process question through LLM or Fallback Engine
    processed = await LLMService.process_question(req.question, force_mode=req.execution_mode)
    intent = processed["intent"]
    raw_sql = processed["sql"]
    clarif = processed["clarification"]
    unsupp = processed["unsupported"]
    exec_mode = processed["execution_mode"]

    # 2. Case: Ambiguous Question or Unrecognized Intent (requesting clarification)
    if clarif:
        resp = QueryResponse(
            request_id=req_id,
            question=req.question,
            interpreted_intent=intent or {"type": "ambiguous"},
            clarification_required=True,
            clarification_message=clarif,
            assumptions=["Inquiry requires disambiguation between volume, revenue, or specific product dimensions."],
            sql="",
            query_status="clarification",
            execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
            summary="Clarification requested to disambiguate the metric or dimension.",
            key_findings=["Multiple interpretations exist or inquiry lacks specific metric constraints."],
            execution_mode=exec_mode,
            follow_up_questions=[
                "Completed transactions last week",
                "Total net revenue last week",
                "Average order value last week",
                "Which region has the highest cancellation rate?"
            ],
            confidence_score=intent.get("confidence", 0.40) if isinstance(intent, dict) else 0.40,
            confidence_reasoning="Confidence lowered due to semantic ambiguity or unmapped entities."
        )
        save_history_entry(resp.model_dump())
        return resp

    # 3. Case: Unsupported Metric
    if unsupp:
        resp = QueryResponse(
            request_id=req_id,
            question=req.question,
            interpreted_intent=intent or {"type": "unsupported"},
            clarification_required=False,
            assumptions=["Requested metric is not modeled within the transactions schema catalog."],
            sql="",
            query_status="rejected",
            execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
            summary=unsupp,
            key_findings=["Metric is not modeled in the available retail orders database."],
            limitations=[unsupp],
            execution_mode=exec_mode,
            follow_up_questions=[
                "What was our gross revenue?",
                "Show completed transactions by product category",
                "Which region has the highest cancellation rate?"
            ],
            confidence_score=1.0,
            confidence_reasoning="Metric absence confirmed against relational schema catalog."
        )
        save_history_entry(resp.model_dump())
        return resp

    # 4. Check for 'Why Did This Change?' Diagnostic Intent
    if intent and intent.get("type") == "diagnostic_why":
        diag_data = DiagnosticAnalysisService.analyze_drop(question=req.question)
        insights = InsightService.generate_diagnostic_insight(diag_data, req.question)
        
        # Execute query for table visualization
        ok, cols, rows, exec_ms, err = QueryExecutionService.execute_query(raw_sql) if raw_sql else (False, [], [], 0.0, "No SQL")
        chart_spec = ChartService.generate_chart_spec(
            intent_type="diagnostic_why",
            columns=cols,
            rows=rows,
            title="Completed Transactions: Baseline vs Current Period by Region"
        )

        resp = QueryResponse(
            request_id=req_id,
            question=req.question,
            interpreted_intent=intent,
            assumptions=[
                f"Comparison baseline: {diag_data.get('baseline_period')}; current period: {diag_data.get('current_period')}.",
                "Completed transactions strictly filtered where transaction_status = 'completed'."
            ],
            sql=raw_sql or "",
            query_status="success" if ok else "error",
            execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
            columns=cols,
            rows=rows,
            row_count=len(rows),
            metric_cards=diag_data["metric_cards"],
            chart_spec=chart_spec,
            summary=insights["summary"],
            key_findings=insights["key_findings"],
            contributing_factors=diag_data["contributing_factors"],
            data_quality_warnings=insights.get("data_quality_warnings", []),
            limitations=insights["limitations"],
            execution_mode=exec_mode,
            follow_up_questions=insights["follow_up_questions"],
            confidence_score=insights.get("confidence_score", 0.96),
            confidence_reasoning=insights.get("confidence_reasoning", "Empirically calculated segment contribution shares.")
        )
        save_history_entry(resp.model_dump())
        return resp

    # 5. General Query Execution
    if not raw_sql:
        raise HTTPException(status_code=400, detail="Could not formulate a valid SQL query.")

    ok, cols, rows, exec_ms, err = QueryExecutionService.execute_query(raw_sql)
    if not ok:
        resp = QueryResponse(
            request_id=req_id,
            question=req.question,
            interpreted_intent=intent or {},
            sql=raw_sql,
            query_status="error",
            execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
            summary=f"Query Execution Blocked or Failed: {err}",
            key_findings=[err],
            limitations=["Execution was rejected by safety policy, AST validation, or database engine."],
            execution_mode=exec_mode,
            confidence_score=0.0,
            confidence_reasoning="Query execution failed."
        )
        save_history_entry(resp.model_dump())
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
        assumptions=["Data filtered according to active business metric definitions and read-only AST safety rules."],
        sql=raw_sql,
        query_status="success",
        execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
        columns=cols,
        rows=rows,
        row_count=len(rows),
        metric_cards=[],
        chart_spec=chart_spec,
        summary=insights["summary"],
        key_findings=insights["key_findings"],
        data_quality_warnings=insights.get("data_quality_warnings", []),
        limitations=insights["limitations"],
        execution_mode=exec_mode,
        follow_up_questions=insights["follow_up_questions"],
        confidence_score=insights.get("confidence_score", 0.95),
        confidence_reasoning=insights.get("confidence_reasoning", "Verified AST-parsed SQL execution against relational schema.")
    )
    save_history_entry(resp.model_dump())
    return resp


@router.get("/history")
def get_history():
    return get_history_entries(limit=25)


@router.post("/evaluation/run", response_model=BenchmarkSummary)
def run_evaluation(mode: Optional[str] = "fallback"):
    summary = BenchmarkRunner.run_benchmark(mode=mode or "fallback")
    save_cached_benchmark(summary.model_dump())
    return summary


@router.get("/evaluation/results", response_model=BenchmarkSummary)
def get_evaluation_results():
    cached = get_cached_benchmark()
    if cached:
        return BenchmarkSummary(**cached)
    # If no cached run exists yet, execute benchmark and cache
    summary = BenchmarkRunner.run_benchmark(mode="fallback")
    save_cached_benchmark(summary.model_dump())
    return summary
