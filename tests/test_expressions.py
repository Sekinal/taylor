"""Pruebas del intérprete restringido de funciones."""

import numpy as np
import pytest

from taylor_fd import parse_function


def test_parse_math_expression_for_numpy() -> None:
    parsed = parse_function("exp(-x**2) * cos(y) + pi")
    assert parsed.numpy(0.0, 0.0) == pytest.approx(1 + np.pi)


@pytest.mark.parametrize(
    "source",
    ["__import__('os').system('id')", "x.__class__", "open('secret')", "z + 1"],
)
def test_parser_rejects_non_math_syntax(source: str) -> None:
    with pytest.raises(ValueError):
        parse_function(source)
