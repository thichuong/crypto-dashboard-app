"""Simplified and robust report workflow v2.

This module builds a workflow (LangGraph if available) and exposes a single
function to run the workflow with consistent return values. If LangGraph is
not installed the module falls back to a harmless stub implementation which
is useful for tests and local development.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict

try:
    from langgraph.graph import StateGraph, END
except Exception:  # pragma: no cover - allow code to run when langgraph is absent
    StateGraph = None
    END = None

from .progress_tracker import progress_tracker

logger = logging.getLogger(__name__)


def _build_workflow() -> Any:
    """Return a compiled workflow or a stub object with invoke(state).

    The stub returns a minimal successful state so higher-level code can
    behave uniformly in environments without LangGraph installed.
    """
    if StateGraph is None:
        logger.debug("LangGraph not available — using stub workflow")

        class StubWorkflow:
            def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
                state = dict(state)
                state.setdefault("success", True)
                state.setdefault("report_id", str(uuid.uuid4()))
                state.setdefault("html_content", "<div><p>Stub report</p></div>")
                state.setdefault("css_content", "")
                state.setdefault("js_content", "")
                state.setdefault("research_content", "Stub research content")
                return state

        return StubWorkflow()

    # Lazy imports for real workflow construction
    from .workflow_nodes.base import ReportState
    from .workflow_nodes.prepare_data import prepare_data_node
    from .workflow_nodes.research_deep import research_deep_node
    from .workflow_nodes.validate_report import validate_report_node
    from .workflow_nodes.generate_report_content import generate_report_content_node
    from .workflow_nodes.create_interface_components import (
        create_html_node,
        create_javascript_node,
        create_css_node,
    )
    from .workflow_nodes.translate_content import translate_content_node
    from .workflow_nodes.save_database import save_database_node
    from .workflow_nodes.routing import (
        should_retry_or_continue,
        should_retry_html_or_continue,
        should_retry_js_or_continue,
        should_retry_css_or_continue,
    )

    workflow = StateGraph(ReportState)

    workflow.add_node("prepare_data", prepare_data_node)
    workflow.add_node("research_deep", research_deep_node)
    workflow.add_node("validate_report", validate_report_node)
    workflow.add_node("generate_report_content", generate_report_content_node)
    workflow.add_node("create_html", create_html_node)
    workflow.add_node("create_javascript", create_javascript_node)
    workflow.add_node("create_css", create_css_node)
    workflow.add_node("translate_content", translate_content_node)
    workflow.add_node("save_database", save_database_node)

    workflow.set_entry_point("prepare_data")

    workflow.add_edge("prepare_data", "research_deep")
    workflow.add_edge("research_deep", "validate_report")

    workflow.add_conditional_edges(
        "validate_report",
        should_retry_or_continue,
        {"retry": "research_deep", "continue": "generate_report_content", "end": END},
    )

    workflow.add_edge("generate_report_content", "create_html")

    workflow.add_conditional_edges(
        "create_html",
        should_retry_html_or_continue,
        {"retry_html": "create_html", "continue": "create_javascript", "end": END},
    )

    workflow.add_conditional_edges(
        "create_javascript",
        should_retry_js_or_continue,
        {"retry_js": "create_javascript", "continue": "create_css", "end": END},
    )

    workflow.add_conditional_edges(
        "create_css",
        should_retry_css_or_continue,
        {"retry_css": "create_css", "continue": "translate_content", "end": END},
    )

    workflow.add_edge("translate_content", "save_database")
    workflow.add_edge("save_database", END)

    return workflow.compile()


def generate_auto_research_report_langgraph_v2(api_key: str, max_attempts: int = 3, session_id: str | None = None) -> Dict[str, Any]:
    """Run the report workflow and return a stable result dict.

    The function always returns a dictionary with predictable keys so callers
    don't need to know whether LangGraph was present or a stub was used.
    """
    start = time.time()
    if session_id is None:
        session_id = str(uuid.uuid4())

    progress_tracker.start_progress(session_id, total_steps=10)
    progress_tracker.update_step(session_id, 0, "starting", "Initializing report workflow v2")

    workflow = _build_workflow()

    initial_state: Dict[str, Any] = {
        "session_id": session_id,
        "api_key": api_key,
        "max_attempts": max_attempts,
        "created_at": datetime.utcnow().isoformat(),
        "success": False,
        "error_messages": [],
        "html_attempt": 0,
        "js_attempt": 0,
        "css_attempt": 0,
    }

    try:
        final = workflow.invoke(initial_state)
    except Exception as exc:
        logger.exception("Workflow raised an exception")
        progress_tracker.error_progress(session_id, str(exc))
        return {
            "success": False,
            "session_id": session_id,
            "report_id": None,
            "html_content": "",
            "css_content": "",
            "js_content": "",
            "research_content": "",
            "error_messages": [str(exc)],
            "execution_time": time.time() - start,
            "validation_result": "ERROR",
        }

    exec_time = time.time() - start

    result = {
        "success": bool(final.get("success", False)),
        "session_id": session_id,
        "report_id": final.get("report_id"),
        "html_content": final.get("html_content", ""),
        "css_content": final.get("css_content", ""),
        "js_content": final.get("js_content", ""),
        "research_content": final.get("research_content", ""),
        "error_messages": final.get("error_messages", []),
        "execution_time": exec_time,
        "validation_result": final.get("validation_result", "UNKNOWN"),
        "html_attempt": final.get("html_attempt", 0),
        "js_attempt": final.get("js_attempt", 0),
        "css_attempt": final.get("css_attempt", 0),
    }

    if not result["success"]:
        progress_tracker.error_progress(session_id, ", ".join(result.get("error_messages", [])))

    return result


# Backwards compatibility wrappers
def create_report_workflow():
    from .report_workflow import create_report_workflow as legacy

    return legacy()


def generate_auto_research_report_langgraph(api_key: str, max_attempts: int = 3, session_id: str | None = None) -> Dict[str, Any]:
    return generate_auto_research_report_langgraph_v2(api_key, max_attempts, session_id)
