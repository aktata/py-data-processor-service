from __future__ import annotations

from collections import Counter
from typing import Any

from app.core.errors import AppError, ErrorCode


def analyze_json(payload: Any, max_depth: int, max_nodes: int) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    if not isinstance(payload, (dict, list)):
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="JSON payload must be an object or array.",
            status_code=400,
        )

    depth, nodes, type_summary = _traverse_json(payload, max_depth, max_nodes)
    if nodes >= max_nodes:
        warnings.append("JSON node limit reached during analysis.")
    if depth >= max_depth:
        warnings.append("JSON depth limit reached during analysis.")

    summary = {
        "top_level_keys": list(payload.keys()) if isinstance(payload, dict) else [],
        "estimated_depth": depth,
        "estimated_nodes_count": nodes,
        "type_summary": dict(type_summary),
    }
    return summary, warnings


def _traverse_json(payload: Any, max_depth: int, max_nodes: int) -> tuple[int, int, Counter[str]]:
    counter: Counter[str] = Counter()
    max_depth_found = 0
    nodes = 0
    stack: list[tuple[Any, int]] = [(payload, 1)]

    while stack and nodes < max_nodes:
        current, depth = stack.pop()
        nodes += 1
        max_depth_found = max(max_depth_found, depth)
        counter[type(current).__name__] += 1

        if depth >= max_depth:
            continue

        if isinstance(current, dict):
            for value in current.values():
                stack.append((value, depth + 1))
        elif isinstance(current, list):
            for value in current:
                stack.append((value, depth + 1))

    return max_depth_found, nodes, counter
