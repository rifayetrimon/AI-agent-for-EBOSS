import json
import logging

from crewai import Agent, Crew, Process, Task
from crewai.tools import BaseTool
from pydantic import BaseModel

from app.services.llm_factory import get_llm
from app.tools.registry import RegisteredTool, all_tools, tool_ctx

logger = logging.getLogger(__name__)


def _wrap_tool(t: RegisteredTool, ctx: dict, log: list) -> BaseTool:
    """Convert a RegisteredTool into a CrewAI BaseTool with closure-bound ctx + log.

    CrewAI may execute tools in worker threads, so we cannot rely on a ContextVar
    being inherited from the request thread. Instead, the wrapper:
    - sets `tool_ctx` inside its own `_run` (so downstream code in the same thread can read it),
    - appends to a closure-captured `log` list (always thread-safe under GIL).
    """
    fn = t.fn
    args_model = t.args_model
    tool_name = t.name

    class _Wrapped(BaseTool):
        name: str = tool_name
        description: str = t.description
        args_schema: type[BaseModel] = args_model

        def _run(self, **kwargs) -> str:
            ctx_token = tool_ctx.set(ctx)
            try:
                try:
                    args_obj = args_model(**kwargs)
                    result = fn(args_obj)
                except Exception as e:
                    logger.exception("[tool:%s] error", tool_name)
                    result = {"ok": False, "error": f"tool {tool_name} crashed: {e}"}
            finally:
                tool_ctx.reset(ctx_token)
            log.append({"tool": tool_name, "args": kwargs, "result": result})
            return json.dumps(result, default=str)

    return _Wrapped()


def _build_router_agent(tools: list[BaseTool]) -> Agent:
    return Agent(
        role="Operations Assistant",
        goal="Use the available tools to fulfil the user's request precisely and report what was done.",
        backstory=(
            "You are a careful operations assistant for an HR/CMS platform. "
            "Read the user's command, pick the most appropriate tool(s), and call them with well-formed arguments "
            "extracted from the command. Some tools rely on request-context data (staff directory, db, headers, "
            "available_templates, current_palette, timezone) that the system supplies automatically — never invent "
            "or pass that data as args. "
            "Chain tools when the command requires it (e.g. 'suggest and apply' = suggest_cms_colors then "
            "apply_cms_color_palette). If a tool returns ok=false, read the error: try a different tool only if "
            "it clearly fits, otherwise stop and report the error to the user."
        ),
        tools=tools,
        verbose=False,
        allow_delegation=False,
        llm=get_llm(),
    )


def run_router_agent(command: str, ctx: dict, log: list, context_summary: str) -> str:
    """Execute the router agent. ctx and log are bound into the tool wrappers."""
    if not all_tools():
        raise RuntimeError("no tools registered — import the tools modules at startup")

    crew_tools = [_wrap_tool(t, ctx, log) for t in all_tools()]
    agent = _build_router_agent(crew_tools)
    task = Task(
        description=(
            f"User command:\n\"{command}\"\n\n"
            f"Request context already available to tools (do NOT pass these as arguments):\n{context_summary}\n\n"
            "Pick and call the appropriate tool(s) with valid arguments derived from the command. "
            "After the tool(s) return, write a one-paragraph plain-English summary of what was done, including "
            "any plan_id, status, scheduled time, recipients, palette names, template ids, or relevant identifiers. "
            "If a tool returned ok=false, explain the failure clearly."
        ),
        expected_output=(
            "A concise human-readable summary (2-4 sentences) of the action(s) taken and key details."
        ),
        agent=agent,
    )
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    return str(result)
