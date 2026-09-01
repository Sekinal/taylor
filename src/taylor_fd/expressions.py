"""Interpretación restringida de expresiones matemáticas en ``x`` e ``y``.

No se usa ``eval`` sobre el texto del usuario. Un árbol de sintaxis de Python se
recorre y solamente se aceptan números, las dos variables, operadores aritméticos
y una lista explícita de funciones matemáticas.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any

import sympy as sp

X, Y = sp.symbols("x y", real=True)

_FUNCTIONS: dict[str, Any] = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "exp": sp.exp,
    "log": sp.log,
    "sqrt": sp.sqrt,
    "abs": sp.Abs,
    "Abs": sp.Abs,
}
_NAMES = {"x": X, "y": Y, "pi": sp.pi, "e": sp.E, "E": sp.E}
_BINARY_OPERATORS = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
    ast.Pow: lambda left, right: left**right,
}


@dataclass(frozen=True, slots=True)
class ParsedFunction:
    """Una misma expresión preparada para NumPy y para mpmath."""

    source: str
    expression: sp.Expr
    numpy: Any
    mpmath: Any


def _convert_node(node: ast.AST) -> sp.Expr:
    """Convierte recursivamente solo los nodos AST permitidos."""
    if isinstance(node, ast.Expression):
        return _convert_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return sp.sympify(node.value)
    if isinstance(node, ast.Name) and node.id in _NAMES:
        return _NAMES[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        return _BINARY_OPERATORS[type(node.op)](_convert_node(node.left), _convert_node(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
        value = _convert_node(node.operand)
        return -value if isinstance(node.op, ast.USub) else value
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FUNCTIONS
        and len(node.args) == 1
        and not node.keywords
    ):
        return _FUNCTIONS[node.func.id](_convert_node(node.args[0]))
    raise ValueError(
        "Expresión no permitida. Usa x, y, números, + - * / ** y funciones matemáticas comunes."
    )


def parse_function(source: str) -> ParsedFunction:
    """Convierte texto matemático en evaluadores, sin calcular derivadas simbólicas."""
    try:
        syntax_tree = ast.parse(source, mode="eval")
        expression = _convert_node(syntax_tree)
    except (SyntaxError, ValueError, TypeError) as error:
        raise ValueError(f"No se pudo interpretar la función: {error}") from error

    unknown_symbols = expression.free_symbols - {X, Y}
    if unknown_symbols:
        raise ValueError(f"Símbolos desconocidos: {', '.join(map(str, unknown_symbols))}")
    return ParsedFunction(
        source=source,
        expression=expression,
        numpy=sp.lambdify((X, Y), expression, modules="numpy"),
        mpmath=sp.lambdify((X, Y), expression, modules="mpmath"),
    )
