"""Núcleo numérico para Taylor de funciones de dos variables.

La fórmula implementada alrededor de ``(a, b)`` es::

    T_N(x, y) = sum_{n=0}^N sum_{i=0}^n
                  C(n, i) / n! * D_x^i D_y^(n-i) f(a,b)
                  * (x-a)^i * (y-b)^(n-i)

``C(n, i)`` se obtiene del triángulo de Pascal. Lo único que cambia entre
los tres niveles es *cómo* se aproximan las derivadas parciales.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from math import ceil, factorial
from typing import Any

import numpy as np
from mpmath import mp

Function2D = Callable[[Any, Any], Any]


class ComputationLevel(StrEnum):
    """Las tres estrategias de cálculo disponibles.

    BEGINNER
        Diferencias progresivas cuyos coeficientes también salen de Pascal.
        Es la fórmula más transparente, pero solo tiene error O(h).
    ADVANCED
        Plantillas centradas de orden alto generadas con Fornberg, más dos
        refinamientos del paso y extrapolación de Richardson en float64.
    HERO
        El mismo método avanzado ejecutado con precisión arbitraria mediante
        mpmath. Está pensado para N alto, donde el redondeo domina rápidamente.
    """

    BEGINNER = "beginner"
    ADVANCED = "advanced"
    HERO = "hero"


@dataclass(frozen=True, slots=True)
class TaylorTerm:
    """Un término ``c·(x-a)^i·(y-b)^j`` del polinomio."""

    total_order: int
    x_order: int
    y_order: int
    pascal_coefficient: int
    derivative: float
    coefficient: float
    uncertainty: float


@dataclass(frozen=True, slots=True)
class TaylorModel:
    """Polinomio de Taylor bivariado y metadatos de su construcción."""

    center: tuple[float, float]
    order: int
    level: ComputationLevel
    step: tuple[float, float]
    accuracy: int
    terms: tuple[TaylorTerm, ...]
    pascal: tuple[tuple[int, ...], ...]

    def evaluate(self, x: Any, y: Any) -> Any:
        """Evalúa el polinomio; acepta escalares o arreglos de NumPy."""
        dx = np.asarray(x) - self.center[0]
        dy = np.asarray(y) - self.center[1]
        shape = np.broadcast_shapes(dx.shape, dy.shape)
        result: Any = np.zeros(shape, dtype=float)
        for term in self.terms:
            result = result + term.coefficient * dx**term.x_order * dy**term.y_order
        return float(result) if np.ndim(result) == 0 else result

    @property
    def derivatives(self) -> dict[tuple[int, int], float]:
        """Devuelve las derivadas parciales indexadas por ``(orden_x, orden_y)``."""
        return {(term.x_order, term.y_order): term.derivative for term in self.terms}


# ---------------------------------------------------------------------------
# PASO COMÚN A LOS TRES NIVELES: TRIÁNGULO DE PASCAL
# ---------------------------------------------------------------------------


def pascal_triangle(order: int) -> list[list[int]]:
    """Construye las filas 0..N del triángulo de Pascal sin usar factoriales."""
    if order < 0:
        raise ValueError("El orden N debe ser mayor o igual que cero.")

    triangle: list[list[int]] = [[1]]
    for row_number in range(1, order + 1):
        previous = triangle[-1]
        row = [1]
        row.extend(previous[index - 1] + previous[index] for index in range(1, row_number))
        row.append(1)
        triangle.append(row)
    return triangle


# ---------------------------------------------------------------------------
# HERRAMIENTA DE LOS NIVELES ADVANCED/HERO: RECURRENCIA DE FORNBERG
# ---------------------------------------------------------------------------


def finite_difference_weights[Scalar](
    nodes: list[Scalar], derivative_order: int, *, point: Scalar | None = None
) -> list[Scalar]:
    """Genera pesos de diferencias finitas con la recurrencia de Fornberg.

    Dados nodos ``z_k``, devuelve pesos ``w_k`` tales que::

        f^(m)(point) ≈ sum_k w_k f(z_k)

    El algoritmo evita resolver explícitamente un sistema de Vandermonde y
    funciona tanto con ``float`` como con ``mpmath.mpf``. Esa genericidad es
    lo que permite compartir exactamente el mismo código entre ADVANCED y HERO.
    """
    if not nodes:
        raise ValueError("Se necesita al menos un nodo.")
    if derivative_order < 0:
        raise ValueError("El orden de derivación no puede ser negativo.")
    if derivative_order >= len(nodes):
        raise ValueError("Se requieren más nodos que el orden de derivación.")
    if len(set(nodes)) != len(nodes):
        raise ValueError("Los nodos de la plantilla deben ser distintos.")

    # Crear cero y uno a partir del tipo de los nodos conserva float o mpf.
    zero = nodes[0] * 0
    one = zero + 1
    x0 = zero if point is None else point
    coefficients = [[zero for _ in range(derivative_order + 1)] for _ in nodes]
    coefficients[0][0] = one
    previous_product = one
    previous_offset = nodes[0] - x0

    # Traducción directa de la primera recurrencia del artículo de Fornberg.
    for node_index in range(1, len(nodes)):
        max_derivative = min(node_index, derivative_order)
        product = one
        old_offset = previous_offset
        previous_offset = nodes[node_index] - x0

        for previous_index in range(node_index):
            separation = nodes[node_index] - nodes[previous_index]
            product *= separation

            if previous_index == node_index - 1:
                for current_order in range(max_derivative, 0, -1):
                    coefficients[node_index][current_order] = (
                        previous_product
                        * (
                            current_order * coefficients[node_index - 1][current_order - 1]
                            - old_offset * coefficients[node_index - 1][current_order]
                        )
                        / product
                    )
                coefficients[node_index][0] = (
                    -previous_product * old_offset * coefficients[node_index - 1][0] / product
                )

            for current_order in range(max_derivative, 0, -1):
                coefficients[previous_index][current_order] = (
                    previous_offset * coefficients[previous_index][current_order]
                    - current_order * coefficients[previous_index][current_order - 1]
                ) / separation
            coefficients[previous_index][0] = (
                previous_offset * coefficients[previous_index][0] / separation
            )

        previous_product = product

    return [row[derivative_order] for row in coefficients]


# ---------------------------------------------------------------------------
# NIVEL 1 — BEGINNER: DIFERENCIAS PROGRESIVAS CON PASCAL
# ---------------------------------------------------------------------------


def _beginner_derivative(
    function: Function2D,
    center: tuple[float, float],
    orders: tuple[int, int],
    step: tuple[float, float],
    pascal: list[list[int]],
) -> float:
    """Aproxima una parcial mixta con una fórmula visible y didáctica.

    Para ``i`` derivadas respecto de x y ``j`` respecto de y se usa::

        1/(hx^i hy^j) sum_p sum_q
        (-1)^(i-p+j-q) C(i,p) C(j,q) f(a+p hx, b+q hy)

    Los dos binomiales se leen directamente de Pascal. No se oculta ninguna
    generación de pesos, lo cual hace este nivel ideal para aprender.
    """
    x_order, y_order = orders
    total = 0.0
    for x_index, x_binomial in enumerate(pascal[x_order]):
        x_sign = -1 if (x_order - x_index) % 2 else 1
        for y_index, y_binomial in enumerate(pascal[y_order]):
            y_sign = -1 if (y_order - y_index) % 2 else 1
            value = function(center[0] + x_index * step[0], center[1] + y_index * step[1])
            total += x_sign * y_sign * x_binomial * y_binomial * float(value)
    return total / (step[0] ** x_order * step[1] ** y_order)


# ---------------------------------------------------------------------------
# NIVELES 2 Y 3 — PLANTILLA CENTRADA TENSORIAL + REFINAMIENTO
# ---------------------------------------------------------------------------


def _stencil_radius(order: int, accuracy: int) -> int:
    """Elige suficientes nodos a cada lado para derivada y precisión pedidas."""
    return max(1, ceil((order + accuracy) / 2))


def _formal_centered_accuracy(radius: int, derivative_order: int) -> int:
    """Orden formal real de una plantilla simétrica de ``2r+1`` puntos.

    La simetría anula un momento adicional para derivadas pares. El caso de
    orden cero es una evaluación exacta en el nodo central y se trata aparte.
    """
    if derivative_order == 0:
        return 10**9  # Representa "exacto" al tomar el mínimo con el otro eje.
    points = 2 * radius + 1
    parity_bonus = 1 if derivative_order % 2 == 0 else 0
    return points - derivative_order + parity_bonus


def _all_centered_derivatives(
    function: Function2D,
    center: tuple[Any, Any],
    order: int,
    step: tuple[Any, Any],
    accuracy: int,
    *,
    use_mpmath: bool,
) -> dict[tuple[int, int], Any]:
    """Calcula todas las parciales reutilizando una sola malla tensorial.

    Una parcial mixta es el producto tensorial de los pesos unidimensionales:
    ``D_x^i D_y^j f ≈ Σ_p Σ_q wx[p] wy[q] f(xp,yq)``. Cada evaluación de la
    función se almacena una vez, una mejora importante cuando N crece.
    """
    radius = _stencil_radius(order, accuracy)
    if use_mpmath:
        nodes = [mp.mpf(index) for index in range(-radius, radius + 1)]
    else:
        nodes = [float(index) for index in range(-radius, radius + 1)]

    weights = {
        derivative_order: finite_difference_weights(nodes, derivative_order)
        for derivative_order in range(order + 1)
    }

    # Caché explícita: la función solo se evalúa (2r+1)^2 veces por escala.
    samples: dict[tuple[int, int], Any] = {}
    for x_index, x_node in enumerate(nodes):
        for y_index, y_node in enumerate(nodes):
            samples[x_index, y_index] = function(
                center[0] + step[0] * x_node, center[1] + step[1] * y_node
            )

    derivatives: dict[tuple[int, int], Any] = {}
    for total_order in range(order + 1):
        for x_order in range(total_order + 1):
            y_order = total_order - x_order
            value = nodes[0] * 0
            for x_index, x_weight in enumerate(weights[x_order]):
                for y_index, y_weight in enumerate(weights[y_order]):
                    value += x_weight * y_weight * samples[x_index, y_index]
            derivatives[x_order, y_order] = value / (step[0] ** x_order * step[1] ** y_order)
    return derivatives


def _adaptive_derivatives(
    function: Function2D,
    center: tuple[Any, Any],
    order: int,
    step: tuple[Any, Any],
    accuracy: int,
    *,
    use_mpmath: bool,
) -> tuple[dict[tuple[int, int], Any], dict[tuple[int, int], float]]:
    """Refina ``h`` dos veces y aplica extrapolación de Richardson.

    Se calculan las plantillas con h, h/2 y h/4. Las parejas consecutivas
    permiten estimar el término principal del error O(h^accuracy). Si al hacer
    h más pequeño el error crece, se conserva el resultado anterior para no
    amplificar redondeo o cancelación catastrófica.
    """
    two = mp.mpf(2) if use_mpmath else 2.0
    scales = (two**0, two**-1, two**-2)
    approximations = [
        _all_centered_derivatives(
            function,
            center,
            order,
            (step[0] * scale, step[1] * scale),
            accuracy,
            use_mpmath=use_mpmath,
        )
        for scale in scales
    ]
    radius = _stencil_radius(order, accuracy)
    result: dict[tuple[int, int], Any] = {}
    uncertainty: dict[tuple[int, int], float] = {}

    for key in approximations[0]:
        coarse, middle, fine = (approximation[key] for approximation in approximations)
        x_accuracy = _formal_centered_accuracy(radius, key[0])
        y_accuracy = _formal_centered_accuracy(radius, key[1])
        actual_accuracy = min(x_accuracy, y_accuracy)
        if key == (0, 0):
            # La función en el centro aparece exactamente en las tres mallas.
            result[key] = fine
            uncertainty[key] = 0.0
            continue
        richardson_factor = two**actual_accuracy - 1
        extrapolated_1 = middle + (middle - coarse) / richardson_factor
        extrapolated_2 = fine + (fine - middle) / richardson_factor
        error_1 = abs(extrapolated_1 - middle)
        error_2 = abs(extrapolated_2 - fine)

        if error_2 <= error_1 * two:
            result[key] = extrapolated_2
            uncertainty[key] = float(max(error_2, abs(extrapolated_2 - extrapolated_1)))
        else:
            result[key] = extrapolated_1
            uncertainty[key] = float(error_1)
    return result, uncertainty


# ---------------------------------------------------------------------------
# CONSTRUCTOR PÚBLICO: SELECCIONA EL NIVEL Y ENSAMBLA TAYLOR CON PASCAL
# ---------------------------------------------------------------------------


def build_taylor_model(
    function: Function2D,
    *,
    center: tuple[float, float] = (0.0, 0.0),
    order: int = 4,
    level: ComputationLevel | str = ComputationLevel.ADVANCED,
    step: float | tuple[float, float] | None = None,
    accuracy: int = 4,
    precision: int = 80,
) -> TaylorModel:
    """Construye un Taylor bivariado total hasta orden ``N``.

    Parameters
    ----------
    function:
        Cualquier callable ``f(x, y)`` suficientemente suave cerca del centro.
    center:
        Punto de expansión ``(a, b)``.
    order:
        Orden total N. Se generan todas las parciales con ``i+j <= N``.
    level:
        ``beginner``, ``advanced`` o ``hero``; véase :class:`ComputationLevel`.
    step:
        Un h común o la pareja ``(hx, hy)``. Si se omite se elige un valor
        conservador; cambiarlo puede ser necesario si la escala de f es extrema.
    accuracy:
        Orden par objetivo de la plantilla centrada (advanced/hero).
    precision:
        Dígitos decimales internos de mpmath en hero.

    Notes
    -----
    Diferencias finitas requieren que f tenga las derivadas solicitadas. "Cualquier
    función" significa cualquier callable suave en la plantilla, no funciones
    discontinuas o puntos donde f quede fuera de su dominio.
    """
    if order < 0:
        raise ValueError("El orden N debe ser mayor o igual que cero.")
    if accuracy < 2 or accuracy % 2:
        raise ValueError("La precisión de la plantilla debe ser un entero par >= 2.")
    if precision < 30:
        raise ValueError("El nivel hero requiere al menos 30 dígitos de precisión.")

    selected_level = ComputationLevel(level)
    if step is None:
        default_step = 0.05 if selected_level is ComputationLevel.BEGINNER else 0.1
        step_pair = (default_step, default_step)
    elif isinstance(step, tuple):
        step_pair = (float(step[0]), float(step[1]))
    else:
        step_pair = (float(step), float(step))
    if step_pair[0] <= 0 or step_pair[1] <= 0:
        raise ValueError("Los pasos hx y hy deben ser positivos.")

    pascal = pascal_triangle(order)
    uncertainties: dict[tuple[int, int], float]

    # NIVEL 1: fórmula progresiva, simple y 100 % visible desde Pascal.
    if selected_level is ComputationLevel.BEGINNER:
        derivatives = {
            (x_order, total_order - x_order): _beginner_derivative(
                function,
                center,
                (x_order, total_order - x_order),
                step_pair,
                pascal,
            )
            for total_order in range(order + 1)
            for x_order in range(total_order + 1)
        }
        uncertainties = {key: float("nan") for key in derivatives}

    # NIVEL 3: Fornberg/Richardson dentro de un contexto de precisión arbitraria.
    elif selected_level is ComputationLevel.HERO:
        with mp.workdps(precision):
            mp_center = (mp.mpf(center[0]), mp.mpf(center[1]))
            mp_step = (mp.mpf(step_pair[0]), mp.mpf(step_pair[1]))
            derivatives, uncertainties = _adaptive_derivatives(
                function,
                mp_center,
                order,
                mp_step,
                accuracy,
                use_mpmath=True,
            )

    # NIVEL 2: mismo algoritmo robusto, pero rápido y vectorizable en float64.
    else:
        derivatives, uncertainties = _adaptive_derivatives(
            function,
            center,
            order,
            step_pair,
            accuracy,
            use_mpmath=False,
        )

    # Paso final común: ensamblar todos los coeficientes desde Pascal.
    terms: list[TaylorTerm] = []
    for total_order in range(order + 1):
        for x_order in range(total_order + 1):
            y_order = total_order - x_order
            binomial = pascal[total_order][x_order]
            derivative = float(derivatives[x_order, y_order])

            # C(n,i)/n! = 1/(i!j!), pero esta forma muestra el origen en Pascal.
            coefficient = binomial * derivative / factorial(total_order)
            terms.append(
                TaylorTerm(
                    total_order=total_order,
                    x_order=x_order,
                    y_order=y_order,
                    pascal_coefficient=binomial,
                    derivative=derivative,
                    coefficient=coefficient,
                    uncertainty=uncertainties[x_order, y_order],
                )
            )

    return TaylorModel(
        center=center,
        order=order,
        level=selected_level,
        step=step_pair,
        accuracy=accuracy,
        terms=tuple(terms),
        pascal=tuple(tuple(row) for row in pascal),
    )
