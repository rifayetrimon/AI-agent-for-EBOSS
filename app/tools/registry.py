from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel


@dataclass
class RegisteredTool:
    name: str
    description: str
    args_model: type[BaseModel]
    fn: Callable[..., Any]
    requires_confirmation: bool = False


_REGISTRY: dict[str, RegisteredTool] = {}

# Per-request injection: tools read this for db session, staff list, timezone, auto_confirm flag.
tool_ctx: ContextVar[dict | None] = ContextVar("tool_ctx", default=None)

# Per-request log of tool calls: the router endpoint inspects this to return a structured trace.
tool_call_log: ContextVar[list | None] = ContextVar("tool_call_log", default=None)


def tool(
    *,
    name: str,
    description: str,
    args_model: type[BaseModel],
    requires_confirmation: bool = False,
):
    def decorator(fn):
        _REGISTRY[name] = RegisteredTool(
            name=name,
            description=description,
            args_model=args_model,
            fn=fn,
            requires_confirmation=requires_confirmation,
        )
        return fn

    return decorator


def all_tools() -> list[RegisteredTool]:
    return list(_REGISTRY.values())


def get_tool(name: str) -> RegisteredTool | None:
    return _REGISTRY.get(name)
