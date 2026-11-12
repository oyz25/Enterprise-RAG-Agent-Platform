import ast
import operator
import os
import re
import secrets
from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.telemetry import app_logger

MAX_QUERY_LENGTH = 2000
MAX_EXPONENT = 100

# Compiled patterns for prompt injection, system-prompt extraction, and payload abuse
BLOCKED_INPUT_PATTERNS = [
    (re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE), "Prompt override attempt detected."),
    (re.compile(r"disregard\s+(all\s+)?(previous|prior)\s+(instructions|rules)", re.IGNORECASE), "Prompt override attempt detected."),
    (re.compile(r"(reveal|show|print|output)\s+(your\s+)?(system\s+prompt|hidden\s+instructions)", re.IGNORECASE), "System prompt extraction attempt detected."),
    (re.compile(r"bypass\s+(all\s+)?(safety|security|guardrails)", re.IGNORECASE), "Guardrail bypass attempt detected."),
    (re.compile(r"<\s*script\b", re.IGNORECASE), "Unsafe HTML/script tag detected."),
    (re.compile(r";\s*drop\s+table\b", re.IGNORECASE), "Unsafe SQL injection pattern detected."),
]

# Allowed AST arithmetic operators for CalculatorTool
_SAFE_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_SAFE_UNARY_OPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def verify_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
) -> str:
    """
    Validate X-API-Key header when API_SECRET_KEY is configured in environment.
    Remains open in local dev mode when API_SECRET_KEY is unset.
    """
    configured_key = os.getenv("API_SECRET_KEY", "").strip()
    if not configured_key:
        return "dev-open-mode"

    if not x_api_key or not secrets.compare_digest(x_api_key, configured_key):
        app_logger.warning(
            "security.auth.unauthorized",
            extra={"structured": {"reason": "invalid_or_missing_api_key"}},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header.",
        )

    return "authenticated"


def validate_user_input(query: str, max_length: int = MAX_QUERY_LENGTH) -> str:
    """
    Enforce payload length limits and block prompt injection or malicious markup patterns.
    """
    cleaned = query.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty.",
        )

    if len(cleaned) > max_length:
        app_logger.warning(
            "security.guardrail.blocked",
            extra={"structured": {"reason": "max_length_exceeded", "length": len(cleaned)}},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query exceeds maximum allowed length of {max_length} characters.",
        )

    for pattern, reason in BLOCKED_INPUT_PATTERNS:
        if pattern.search(cleaned):
            app_logger.warning(
                "security.guardrail.blocked",
                extra={"structured": {"reason": reason}},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input rejected by security guardrail: {reason}",
            )

    return cleaned


def _eval_ast_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_ast_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        raise ValueError("Only numeric constants are allowed.")

    if isinstance(node, ast.UnaryOp):
        op_func = _SAFE_UNARY_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError("Unsupported unary operator.")
        return float(op_func(_eval_ast_node(node.operand)))

    if isinstance(node, ast.BinOp):
        op_func = _SAFE_BIN_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError("Unsupported arithmetic operator.")

        left = _eval_ast_node(node.left)
        right = _eval_ast_node(node.right)

        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise ValueError(f"Exponent exceeds safe limit ({MAX_EXPONENT}).")

        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
            raise ZeroDivisionError("Division by zero is not allowed.")

        return float(op_func(left, right))

    raise ValueError(f"Disallowed expression syntax: {type(node).__name__}")


def safe_eval_math(expression: str) -> tuple[str, float]:
    """
    Safely parse and evaluate an arithmetic expression using Python's AST module
    without calling eval(). Returns (normalized_expression, float_result).
    """
    clean_expr = re.sub(r"[^\d\+\-\*\/\%\(\)\.\s]", "", expression).strip()
    if not clean_expr:
        raise ValueError("No valid mathematical expression found.")

    try:
        tree = ast.parse(clean_expr, mode="eval")
    except SyntaxError as exc:
        raise ValueError("Malformed mathematical expression.") from exc

    result = _eval_ast_node(tree)
    return clean_expr, round(result, 8)