from typing import Dict, Any
from app.tools.base import BaseTool
from app.core.security import safe_eval_math


class CalculatorTool(BaseTool):
    """
    Tool for safely evaluating arithmetic expressions via restricted AST parsing.
    """

    name = "calculator"
    description = "Safely evaluates mathematical expressions (+, -, *, /, //, %, **)."

    def execute(self, expression: str = "", **kwargs) -> Dict[str, Any]:
        try:
            clean_expr, result = safe_eval_math(expression)
            return {
                "status": "success",
                "expression": clean_expr,
                "result": result,
            }
        except (ValueError, ZeroDivisionError) as exc:
            return {"status": "error", "message": str(exc)}
        except Exception as exc:
            return {"status": "error", "message": f"Calculation failed: {str(exc)}"}