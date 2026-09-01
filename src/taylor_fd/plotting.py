"""Visualización de la función, Taylor y sus curvas de intersección."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from taylor_fd.core import TaylorModel


def _evaluate_grid(function: Callable[[Any, Any], Any], x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Evalúa callables vectorizados y también funciones escalares normales."""
    try:
        values = np.asarray(function(x, y), dtype=float)
        return np.broadcast_to(values, x.shape).copy()
    except (TypeError, ValueError):
        vectorized = np.vectorize(function, otypes=[float])
        return vectorized(x, y)


def _intersection_segments(
    x: np.ndarray, y: np.ndarray, difference: np.ndarray
) -> list[np.ndarray]:
    """Obtiene las curvas donde ``original - Taylor = 0``.

    Un contorno 2D de nivel cero da coordenadas (x,y) subpíxel. Luego cada curva
    se eleva a z=f(x,y), de modo que la línea roja sí vive sobre ambas superficies
    y no es una mera proyección en el plano inferior.
    """
    temporary_figure, temporary_axis = plt.subplots()
    try:
        contour = temporary_axis.contour(x, y, difference, levels=[0.0])
        return [segment for segment in contour.allsegs[0] if len(segment) > 1]
    finally:
        plt.close(temporary_figure)


def plot_comparison(
    function: Callable[[Any, Any], Any],
    model: TaylorModel,
    *,
    x_range: tuple[float, float] = (-2.0, 2.0),
    y_range: tuple[float, float] = (-2.0, 2.0),
    points: int = 121,
    output: str | Path | None = None,
    show: bool = True,
    title_expression: str | None = None,
) -> tuple[Figure, dict[str, float]]:
    """Crea tres paneles 3D y devuelve también métricas de error en la malla."""
    if points < 20:
        raise ValueError("La gráfica necesita al menos 20 puntos por eje.")
    if x_range[0] >= x_range[1] or y_range[0] >= y_range[1]:
        raise ValueError("Cada rango debe escribirse de menor a mayor.")

    x_values = np.linspace(*x_range, points)
    y_values = np.linspace(*y_range, points)
    x_grid, y_grid = np.meshgrid(x_values, y_values)
    with np.errstate(all="ignore"):
        original = _evaluate_grid(function, x_grid, y_grid)
        approximation = np.asarray(model.evaluate(x_grid, y_grid), dtype=float)

    # Los puntos fuera del dominio de la función quedan fuera de métricas/contornos.
    valid = np.isfinite(original) & np.isfinite(approximation)
    difference = np.where(valid, original - approximation, np.nan)
    absolute_error = np.abs(difference)
    finite_error = absolute_error[np.isfinite(absolute_error)]
    metrics = {
        "rmse": float(np.sqrt(np.mean(finite_error**2))) if finite_error.size else float("nan"),
        "max_error": float(np.max(finite_error)) if finite_error.size else float("nan"),
    }

    figure = plt.figure(figsize=(18, 6), constrained_layout=True)
    axes = [figure.add_subplot(1, 3, index, projection="3d") for index in range(1, 4)]
    common = {"rstride": 2, "cstride": 2, "linewidth": 0, "antialiased": True}

    axes[0].plot_surface(x_grid, y_grid, original, cmap="viridis", alpha=0.92, **common)
    axes[0].set_title("Función original")
    axes[1].plot_surface(x_grid, y_grid, approximation, cmap="plasma", alpha=0.92, **common)
    axes[1].set_title(f"Taylor numérico: N={model.order} · {model.level.value}")

    # El tercer panel contesta directamente: ¿dónde se intersectan?
    axes[2].plot_surface(x_grid, y_grid, original, color="#167d9a", alpha=0.55, **common)
    axes[2].plot_surface(x_grid, y_grid, approximation, color="#f0a202", alpha=0.48, **common)
    segments = _intersection_segments(x_grid, y_grid, difference)
    for segment in segments:
        z_values = _evaluate_grid(function, segment[:, 0], segment[:, 1])
        axes[2].plot(segment[:, 0], segment[:, 1], z_values, color="crimson", linewidth=3)
    axes[2].set_title(f"Superposición · {len(segments)} intersección(es) en rojo")

    for axis in axes:
        axis.set_xlabel("x")
        axis.set_ylabel("y")
        axis.set_zlabel("f(x, y)")
        axis.view_init(elev=28, azim=-125)
    heading = "Taylor bivariado mediante diferencias finitas y Pascal"
    if title_expression:
        heading += f"\n$f(x,y)={title_expression}$"
    figure.suptitle(heading, fontsize=15)

    if output is not None:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_path, dpi=180)
    if show:
        plt.show()
    return figure, metrics
