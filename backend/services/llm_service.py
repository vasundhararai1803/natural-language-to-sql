"""
LLM Provider Adapter and Prompt Orchestration Service.
Connects to OpenAI-compatible LLM endpoints if OPENAI_API_KEY is configured,
grounds SQL generation in the database schema catalog, implements automatic 1-attempt SQL correction,
and clearly distinguishes LLM execution mode from Fallback mode.
"""
import os
import json
import httpx
from typing import Dict, Any, Optional
from backend.config import settings
from backend.services.schema_service import SchemaService
from backend.services.sql_validation_service import SQLValidationService
from backend.services.query_execution_service import QueryExecutionService
from backend.services.fallback_sql_service import FallbackSQLEngine


class LLMService:
    @staticmethod
    def is_llm_configured() -> bool:
        api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        return bool(api_key and len(api_key.strip()) > 5 and not api_key.startswith("gsk_your_actual"))

    @classmethod
    async def _call_llm(cls, messages: list) -> Optional[Dict[str, Any]]:
        api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        base_url = (settings.openai_base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        model = settings.openai_model or os.environ.get("OPENAI_MODEL", "llama-3.3-70b-versatile")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                        "temperature": 0.0
                    }
                )
                if res.status_code == 200:
                    payload = res.json()
                    content = payload["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception:
            return None
        return None

    @classmethod
    async def process_question(cls, question: str, force_mode: Optional[str] = "auto") -> Dict[str, Any]:
        """
        Processes a natural language question.
        Returns a dictionary containing intent, sql, clarification, unsupported, and execution_mode.
        """
        use_fallback = (
            force_mode == "fallback" or
            not cls.is_llm_configured() or
            (force_mode != "llm" and not cls.is_llm_configured())
        )

        if use_fallback:
            intent, sql, clarif, unsupp = FallbackSQLEngine.generate_sql_and_intent(question)
            return {
                "execution_mode": "fallback",
                "intent": intent,
                "sql": sql,
                "clarification": clarif,
                "unsupported": unsupp
            }

        # Attempt LLM call with schema grounding
        system_prompt = (
            "You are an expert analytics SQL engineer for QueryLens AI. "
            "Translate business questions into a single, safe, read-only SQLite SELECT query strictly grounded in the database schema and metric catalog below.\n\n"
            f"{SchemaService.get_schema_prompt_context()}\n\n"
            "Return ONLY a JSON object with this exact structure:\n"
            "{\n"
            '  "intent": {"type": string, "metric": string, "filters": object},\n'
            '  "sql": "SELECT ...",\n'
            '  "clarification_required": false,\n'
            '  "clarification_message": null,\n'
            '  "unsupported_metric": false,\n'
            '  "unsupported_message": null\n'
            "}\n"
            "Strict rules:\n"
            "- Only return read-only SELECT or CTE queries.\n"
            "- Ground all column and table names in the provided schema catalog.\n"
            "- If the question asks for metrics not in schema (like net profit, margin, payroll), set unsupported_metric=true.\n"
            "- If the question is ambiguous like 'how did we perform last week?', set clarification_required=true.\n"
            "- Never generate mutating statements or chained semicolons."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]

        parsed = await cls._call_llm(messages)

        if not parsed:
            # On LLM failure or timeout, fallback smoothly
            intent, sql, clarif, unsupp = FallbackSQLEngine.generate_sql_and_intent(question)
            return {
                "execution_mode": "fallback (LLM unavailable)",
                "intent": intent,
                "sql": sql,
                "clarification": clarif,
                "unsupported": unsupp
            }

        raw_sql = parsed.get("sql")
        clarif = parsed.get("clarification_message") if parsed.get("clarification_required") else None
        unsupp = parsed.get("unsupported_message") if parsed.get("unsupported_metric") else None

        # Automatic SQL Self-Correction Attempt
        # If SQL was generated, validate and test execution; if it fails, attempt 1 self-correction
        if raw_sql and not clarif and not unsupp:
            is_valid, val_err, _ = SQLValidationService.validate_sql(raw_sql)
            if not is_valid:
                # 1 self-correction attempt
                corr_messages = list(messages)
                corr_messages.append({"role": "assistant", "content": json.dumps(parsed)})
                corr_messages.append({
                    "role": "user",
                    "content": f"The previous SQL failed safety or schema validation: {val_err}. Please correct the SQL query using valid schema columns and syntax."
                })
                corrected = await cls._call_llm(corr_messages)
                if corrected and corrected.get("sql"):
                    raw_sql = corrected.get("sql")
                    parsed["intent"] = corrected.get("intent", parsed.get("intent"))

        return {
            "execution_mode": "llm",
            "intent": parsed.get("intent", {}),
            "sql": raw_sql,
            "clarification": clarif,
            "unsupported": unsupp
        }
