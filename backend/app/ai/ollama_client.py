import json
import logging
import time
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from app.tools.registry import ACADEMIC_TOOL_SPECS, execute_tool
from app.ai.multilingual import detect_language, build_multilingual_system_prompt

logger = logging.getLogger(__name__)


def get_ollama_tool_definitions() -> List[Dict[str, Any]]:
    """Converts internal Bedrock/Converse tool specifications into Ollama/OpenAI tool calling schemas."""
    ollama_tools = []
    for spec in ACADEMIC_TOOL_SPECS:
        s = spec["toolSpec"]
        ollama_tools.append({
            "type": "function",
            "function": {
                "name": s["name"],
                "description": s["description"],
                "parameters": s["inputSchema"]["json"]
            }
        })
    return ollama_tools


def check_ollama_health() -> bool:
    """Fast check whether local Ollama server is running and responsive."""
    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
        resp = httpx.get(url, timeout=3.0)
        return resp.status_code == 200
    except Exception:
        return False


def run_ollama_orchestration(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    current_user: User,
    db: Session,
    preferred_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ollama AI Orchestrator:
    1. Detects input language (English, Telugu, Tenglish, Hindi, or Hinglish).
    2. Builds role-specific system prompt with language rules.
    3. Calls Ollama /api/chat with tool definitions and inference settings.
    4. Executes requested tools securely.
    5. Feeds tool execution results back to Ollama to synthesize the final answer.
    6. Falls back gracefully to deterministic academic engine if Ollama is unreachable.
    """
    detected_code, confidence, display_lang = detect_language(user_message)
    active_lang = preferred_language if preferred_language else detected_code

    system_prompt = build_multilingual_system_prompt(
        language_code=active_lang,
        user_role=current_user.role.value,
        user_name=current_user.full_name
    )

    tools_executed = []
    citations = []

    # Prepare message payload
    messages = [{"role": "system", "content": system_prompt}]
    for m in conversation_history[-6:]:
        role = "user" if m.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": m.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    ollama_url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    tools_schema = get_ollama_tool_definitions()

    try:
        with httpx.Client(timeout=settings.OLLAMA_TIMEOUT) as client:
            req_body = {
                "model": settings.OLLAMA_MODEL,
                "messages": messages,
                "tools": tools_schema,
                "stream": False,
                "options": {
                    "temperature": settings.OLLAMA_TEMPERATURE,
                },
                "keep_alive": settings.OLLAMA_KEEP_ALIVE
            }

            logger.info(
                f"Calling Ollama model '{settings.OLLAMA_MODEL}' at {ollama_url} "
                f"for user={current_user.id} (lang={active_lang})"
            )
            response = client.post(ollama_url, json=req_body)

            if response.status_code == 200:
                resp_data = response.json()
                msg = resp_data.get("message", {})
                tool_calls = msg.get("tool_calls", [])

                if tool_calls:
                    # Append assistant message with tool calls
                    messages.append(msg)

                    for tc in tool_calls:
                        fn = tc.get("function", {})
                        tool_name = fn.get("name")
                        raw_args = fn.get("arguments", {})

                        if isinstance(raw_args, str):
                            try:
                                tool_input = json.loads(raw_args)
                            except Exception:
                                tool_input = {}
                        else:
                            tool_input = raw_args or {}

                        t0 = time.time()
                        tool_res = execute_tool(tool_name, tool_input, current_user, db)
                        elapsed_ms = round((time.time() - t0) * 1000, 2)

                        tools_executed.append({
                            "tool_name": tool_name,
                            "tool_input": tool_input,
                            "tool_output": tool_res,
                            "status": "success" if "error" not in tool_res else "failed",
                            "execution_time_ms": elapsed_ms
                        })

                        # Append tool response
                        messages.append({
                            "role": "tool",
                            "content": json.dumps(tool_res)
                        })

                    # Second call to Ollama to synthesize final answer from tool results
                    final_resp = client.post(ollama_url, json={
                        "model": settings.OLLAMA_MODEL,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": settings.OLLAMA_TEMPERATURE
                        }
                    })

                    if final_resp.status_code == 200:
                        final_msg = final_resp.json().get("message", {}).get("content", "")
                        return {
                            "message": final_msg,
                            "detected_language": active_lang,
                            "language_confidence": confidence,
                            "tools_executed": tools_executed,
                            "citations": citations,
                            "llm_provider": "ollama",
                            "model": settings.OLLAMA_MODEL
                        }

                else:
                    # Direct text response from Ollama
                    content = msg.get("content", "")
                    return {
                        "message": content,
                        "detected_language": active_lang,
                        "language_confidence": confidence,
                        "tools_executed": tools_executed,
                        "citations": citations,
                        "llm_provider": "ollama",
                        "model": settings.OLLAMA_MODEL
                    }
            else:
                logger.warning(
                    f"Ollama API returned HTTP {response.status_code}: {response.text}. "
                    "Falling back to local academic engine."
                )

    except Exception as e:
        logger.warning(
            f"Ollama connection/execution failed ({e}) at {ollama_url}. "
            "Falling back to high-fidelity academic responder."
        )

    # Seamless fallback to high-fidelity academic engine
    from app.ai.bedrock_client import _generate_local_academic_response
    fallback_res = _generate_local_academic_response(user_message, active_lang, current_user, db)
    fallback_res["llm_provider"] = "ollama-fallback"
    fallback_res["model"] = settings.OLLAMA_MODEL
    return fallback_res
