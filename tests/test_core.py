"""Pruebas matemáticas del triángulo, los pesos y los tres niveles."""

from math import cos, exp, sin

import numpy as np
import pytest

from taylor_fd import (
    ComputationLevel,
    build_taylor_model,
    finite_difference_weights,
    parse_function,
    pascal_triangle,
)


def test_pascal_triangle() -> None:
    assert pascal_triangle(5)[-1] == [1, 5, 10, 10, 5, 1]


def test_fornberg_centered_first_and_second_derivative_weights() -> None:
    nodes = [-1.0, 0.0, 1.0]
    assert finite_difference_weights(nodes, 1) == pytest.approx([-0.5, 0.0, 0.5])
    assert finite_difference_weights(nodes, 2) == pytest.approx([1.0, -2.0, 1.0])


@pytest.mark.parametrize("level", list(ComputationLevel))
def test_polynomial_is_recovered(level: ComputationLevel) -> None:
    def function(x, y):
        return 3 + 2 * x - y + 4 * x * y + x**2 + 2 * y**2

    model = build_taylor_model(function, order=2, center=(0.2, -0.3), level=level)
    # La fórmula progresiva beginner es deliberadamente O(h); las plantillas
    # centradas de advanced/hero sí deben reconstruir este polinomio casi exacto.
    absolute_tolerance = 0.11 if level is ComputationLevel.BEGINNER else 2e-4
    assert model.evaluate(0.7, 0.4) == pytest.approx(function(0.7, 0.4), abs=absolute_tolerance)


def test_advanced_mixed_derivatives() -> None:
    def function(x, y):
        return np.exp(x) * np.sin(y)

    center = (0.2, 0.4)
    model = build_taylor_model(function, order=3, center=center)
    derivatives = model.derivatives
    assert derivatives[1, 1] == pytest.approx(exp(center[0]) * cos(center[1]), rel=1e-8)
    assert derivatives[2, 1] == pytest.approx(exp(center[0]) * cos(center[1]), rel=1e-7)
    assert derivatives[1, 2] == pytest.approx(-exp(center[0]) * sin(center[1]), rel=1e-7)


def test_hero_retains_high_order_derivatives() -> None:
    """Todas las parciales de exp(x+y) en (0,0) valen exactamente uno."""
    parsed = parse_function("exp(x+y)")
    model = build_taylor_model(
        parsed.mpmath,
        order=8,
        level=ComputationLevel.HERO,
        accuracy=6,
        precision=100,
    )
    assert model.derivatives[4, 4] == pytest.approx(1.0, rel=1e-12)
    assert model.derivatives[7, 1] == pytest.approx(1.0, rel=1e-12)


def test_invalid_order_and_accuracy() -> None:
    with pytest.raises(ValueError):
        pascal_triangle(-1)
    with pytest.raises(ValueError):
        build_taylor_model(lambda x, y: x + y, order=2, accuracy=3)
