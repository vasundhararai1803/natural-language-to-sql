"""
LLM Provider Adapter and Prompt Orchestration Service.
Connects to OpenAI-compatible LLM endpoints if OPENAI_API_KEY is configured,
or gracefully delegates to the deterministic FallbackSQLEngine when offline or unavailable.
"""
import os
import json
import uuid
import httpx
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from backend.services.schema_service import SchemaService
from backend.services.fallback_sql_service import FallbackSQLEngine

load_dotenv()


class LLMService:
    @staticmethod
    def is_llm_configured() -> bool:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        return bool(api_key and len(api_key.strip()) > 5 and not api_key.startswith("gsk_your_actual"))

    @classmethod
    async def process_question(cls, question: str, force_mode: Optional[str] = "auto") -> Dict[str, Any]:
        """
        Processes a natural language question.
        Returns a dictionary containing intent, sql, clarification, unsupported, and execution_mode.
        """
        use_fallback = force_mode == "fallback" or not cls.is_llm_configured() or force_mode != "llm" and not cls.is_llm_configured()

        if use_fallback:
            intent, sql, clarif, unsupp = FallbackSQLEngine.generate_sql_and_intent(question)
            return {
                "execution_mode": "fallback",
                "intent": intent,
                "sql": sql,
                "clarification": clarif,
                "unsupported": unsupp
            }

        # Attempt LLM call with strict JSON output schema
        try:
            system_prompt = (
                "You are an expert SQL engineer for QueryLens AI. "
                "Translate business questions into a single, safe, read-only SQLite SELECT query. "
                "Adhere to the following schema, tables, and metric definitions:\n\n"
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
                "Rules:\n"
                "- Only return read-only SELECT or CTE queries.\n"
                "- If the user asks for net profit or payroll which does not exist in schema, set unsupported_metric=true.\n"
                "- If the question is ambiguous like 'how did we perform last week?', set clarification_required=true.\n"
                "- Never generate INSERT, UPDATE, DELETE, DROP or multiple statements."
            )

            api_key = os.environ.get("OPENAI_API_KEY", "")
            base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
            model = os.environ.get("OPENAI_MODEL", "llama-3.3-70b-versatile")

            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": question}
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.0
                    }
                )

                if res.status_code == 200:
                    payload = res.json()
                    content = payload["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return {
                        "execution_mode": "llm",
                        "intent": parsed.get("intent", {}),
                        "sql": parsed.get("sql"),
                        "clarification": parsed.get("clarification_message") if parsed.get("clarification_required") else None,
                        "unsupported": parsed.get("unsupported_message") if parsed.get("unsupported_metric") else None
                    }
                else:
                    # On API failure, smoothly fallback
                    intent, sql, clarif, unsupp = FallbackSQLEngine.generate_sql_and_intent(question)
                    return {
                        "execution_mode": "fallback (LLM API error)",
                        "intent": intent,
                        "sql": sql,
                        "clarification": clarif,
                        "unsupported": unsupp
                    }

        except Exception as e:
            # Fallback on timeout or connection error
            intent, sql, clarif, unsupp = FallbackSQLEngine.generate_sql_and_intent(question)
            return {
                "execution_mode": "fallback (connection exception)",
                "intent": intent,
                "sql": sql,
                "clarification": clarif,
                "unsupported": unsupp
            }
