import os
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel
from tools.definitions import run_mcp_academic_tool, ACADEMIC_TOOL_SPECS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("campusai.mcp_server")

MCP_API_KEY = os.getenv("MCP_API_KEY", "campusai_mcp_secure_token_key_2026")

app = FastAPI(
    title="CampusAI Model Context Protocol (MCP) Server",
    version="1.0.0",
    description="Standalone Python MCP service providing standard academic tool interfaces for LLMs."
)


class CallToolRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}
    user_email: str


@app.get("/health")
def health():
    return {"status": "healthy", "service": "campusai-mcp-server"}


@app.get("/mcp/tools")
def list_tools(x_mcp_api_key: Optional[str] = Header(None)):
    """Exposes tool schemas separated into Read-Only and Write-Capable groups."""
    if x_mcp_api_key != MCP_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing MCP API Key")

    read_only_tools = [
        "get_my_attendance", "calculate_attendance_target", "get_my_timetable",
        "get_my_exam_results", "get_my_exam_schedule", "get_subject_topics",
        "get_pending_fees", "search_academic_documents", "generate_study_plan",
        "get_correction_request_status"
    ]
    write_tools = [
        "create_attendance_correction_request",
        "approve_attendance_correction",
        "reject_attendance_correction"
    ]

    tools_catalog = []
    for t in ACADEMIC_TOOL_SPECS:
        name = t["toolSpec"]["name"]
        cat = "read_only" if name in read_only_tools else "write_capable"
        tools_catalog.append({
            "name": name,
            "description": t["toolSpec"]["description"],
            "category": cat,
            "input_schema": t["toolSpec"]["inputSchema"]["json"]
        })

    return {
        "tools": tools_catalog,
        "count": len(tools_catalog)
    }


@app.post("/mcp/tools/call")
def call_tool(
    req: CallToolRequest,
    x_mcp_api_key: Optional[str] = Header(None)
):
    """Executes an MCP academic tool with authorization check and timeout enforcement."""
    if x_mcp_api_key != MCP_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing MCP API Key")

    result = run_mcp_academic_tool(
        tool_name=req.name,
        tool_arguments=req.arguments,
        authenticated_user_email=req.user_email
    )
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
