import re
from typing import Dict, Any
from app.tools.base import BaseTool


class CalculatorTool(BaseTool):
    """
    Tool for safely evaluating mathematical expressions.
    """

    name = "calculator"
    description = "Evaluates mathematical expressions (addition, subtraction, multiplication, division)."

    def execute(self, expression: str = "", **kwargs) -> Dict[str, Any]:
        try:
            clean_expr = re.sub(r"[^\d\+\-\*\/\(\)\.]", "", expression)
            if not clean_expr:
                return {"status": "error", "message": "Invalid expression."}

            result = eval(clean_expr)
            return {
                "status": "success",
                "expression": clean_expr,
                "result": float(result)
            }
        except Exception as e:
            return {"status": "error", "message": f"Calculation failed: {str(e)}"}