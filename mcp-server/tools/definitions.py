import os
import sys
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Ensure backend app is available for models and database
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.core.database import SessionLocal
from app.models.user import User, RoleEnum
from app.tools.registry import execute_tool, ACADEMIC_TOOL_SPECS

logger = logging.getLogger("campusai.mcp")


class MCPToolResult(BaseModel):
    isError: bool = False
    content: List[Dict[str, Any]]


def run_mcp_academic_tool(
    tool_name: str,
    tool_arguments: Dict[str, Any],
    authenticated_user_email: str
) -> MCPToolResult:
    """
    Executes an academic tool via the Model Context Protocol (MCP).
    Enforces authentication by matching authenticated_user_email before execution.
    Redacts sensitive private credentials from logs.
    """
    logger.info(f"MCP Tool Invocation: tool={tool_name} user={authenticated_user_email}")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == authenticated_user_email).first()
        if not user:
            return MCPToolResult(
                isError=True,
                content=[{"type": "text", "text": f"MCP Authentication Error: User {authenticated_user_email} not found."}]
            )

        res = execute_tool(tool_name, tool_arguments, user, db)

        if "error" in res:
            return MCPToolResult(
                isError=True,
                content=[{"type": "text", "text": str(res["error"])}]
            )

        return MCPToolResult(
            isError=False,
            content=[{"type": "text", "text": str(res)}]
        )
    except Exception as e:
        logger.error(f"Error executing MCP tool {tool_name}: {e}")
        return MCPToolResult(
            isError=True,
            content=[{"type": "text", "text": f"Internal execution failure: {str(e)}"}]
        )
    finally:
        db.close()
