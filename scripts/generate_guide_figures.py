"""Genera todas las figuras matemáticas de la guía ELI5.

Las imágenes no se dibujan a mano ni dependen de datos externos: cada píxel
sale de las mismas fórmulas que explica el documento. Ejecutar:

    uv run python scripts/generate_guide_figures.py

El backend Agg permite regenerarlas en GitHub Actions sin una pantalla.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle

from taylor_fd import ComputationLevel, build_taylor_model, parse_function, pascal_triangle
from taylor_fd.plotting import plot_comparison

OUTPUT_DIRECTORY = Path(__file__).resolve().parents[1] / "docs" / "assets"
BLUE = "#175CD3"
DARK_BLUE = "#1849A9"
ORANGE = "#F79009"
GREEN = "#12B76A"
RED = "#D92D20"
INK = "#101828"
GRAY = "#667085"
LIGHT_BLUE = "#EFF8FF"


def _style() -> None:
    """Aplica una identidad visual legible y coherente con el PDF."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#98A2B3",
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "axes.titlesize": 12,
            "font.size": 10,
            "text.color": INK,
            "xtick.color": GRAY,
            "ytick.color": GRAY,
            "grid.color": "#D0D5DD",
            "grid.alpha": 0.55,
            "legend.frameon": False,
            "savefig.bbox": "tight",
            "savefig.dpi": 180,
        }
    )


def _save(figure: plt.Figure, filename: str) -> None:
    """Guarda y cierra para que el script no acumule memoria."""
    figure.savefig(OUTPUT_DIRECTORY / filename, facecolor="white")
    plt.close(figure)


def surface_as_mountain() -> None:
    """Figura 1: f(x,y) como altura y el centro como punto de observación."""
    x = np.linspace(-2.0, 2.0, 100)
    y = np.linspace(-2.0, 2.0, 100)
    x_grid, y_grid = np.meshgrid(x, y)
    z = 0.45 * x_grid**2 + 0.25 * y_grid**2 + 0.25 * np.sin(2 * x_grid) * np.cos(y_grid)
    center = (0.45, -0.35)
    center_z = (
        0.45 * center[0] ** 2
        + 0.25 * center[1] ** 2
        + 0.25 * np.sin(2 * center[0]) * np.cos(center[1])
    )

    figure = plt.figure(figsize=(8.2, 5.1))
    axis = figure.add_subplot(projection="3d")
    surface = axis.plot_surface(
        x_grid,
        y_grid,
        z,
        cmap="viridis",
        linewidth=0,
        alpha=0.9,
        rstride=2,
        cstride=2,
    )
    axis.scatter(*center, center_z, color=RED, s=75, edgecolor="white", linewidth=1.5)
    axis.text(center[0], center[1], center_z + 0.35, "centro (a,b)", color=RED, weight="bold")
    axis.plot([center[0], center[0]], [center[1], center[1]], [0, center_z], color=RED, ls="--")
    axis.set(xlabel="posición x", ylabel="posición y", zlabel="altura f(x,y)")
    axis.set_title("Una función de dos variables se puede mirar como una montaña")
    axis.view_init(elev=27, azim=-125)
    figure.colorbar(surface, ax=axis, shrink=0.64, pad=0.09, label="altura")
    _save(figure, "01_funcion_montana.png")


def local_magnifying_glass() -> None:
    """Figura 2: el mismo Taylor se ve bien localmente y peor lejos."""
    x = np.linspace(-3.0, 3.0, 800)
    original = np.exp(x)
    taylor = 1 + x + x**2 / 2 + x**3 / 6 + x**4 / 24

    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.1))
    for axis, limits, title in zip(
        axes,
        [(-0.7, 0.7), (-3.0, 3.0)],
        ["Con la lupa: cerca del centro", "Sin la lupa: lejos del centro"],
        strict=True,
    ):
        mask = (x >= limits[0]) & (x <= limits[1])
        axis.plot(x[mask], original[mask], color=BLUE, lw=3, label="función original")
        axis.plot(x[mask], taylor[mask], color=ORANGE, lw=2.6, ls="--", label="Taylor N=4")
        axis.axvline(0, color=RED, lw=1.5, ls=":")
        axis.scatter([0], [1], color=RED, zorder=5)
        axis.annotate("centro", (0, 1), xytext=(8, 16), textcoords="offset points", color=RED)
        axis.set_title(title)
        axis.set_xlabel("distancia x desde el centro")
        axis.set_ylabel("altura")
        axis.grid(True)
    axes[0].legend(loc="upper left")
    figure.suptitle("Taylor es una copia local: el centro importa", weight="bold")
    figure.tight_layout()
    _save(figure, "02_lupa_local.png")


def finite_difference_steps() -> None:
    """Figura 3: pendiente exacta, progresiva y centrada sobre una parábola."""

    def function(values):
        return values**2

    x = np.linspace(0.4, 2.6, 400)
    center = 1.5
    step = 0.55
    exact_slope = 2 * center
    forward_slope = (function(center + step) - function(center)) / step
    centered_slope = (function(center + step) - function(center - step)) / (2 * step)

    tangent = function(center) + exact_slope * (x - center)
    forward = function(center) + forward_slope * (x - center)
    centered = function(center) + centered_slope * (x - center)

    figure, axis = plt.subplots(figsize=(9.2, 5.1))
    axis.plot(x, function(x), color=INK, lw=3, label=r"función $f(x)=x^2$")
    axis.plot(x, tangent, color=GREEN, lw=2.6, label="tangente exacta")
    axis.plot(x, forward, color=ORANGE, lw=2, ls="--", label="paso hacia delante")
    axis.plot(x, centered, color=BLUE, lw=2, ls=":", label="paso centrado")
    points = np.array([center - step, center, center + step])
    axis.scatter(points, function(points), color=[BLUE, RED, ORANGE], s=65, zorder=6)
    axis.annotate(
        "a-h", (points[0], function(points[0])), xytext=(-8, 14), textcoords="offset points"
    )
    axis.annotate("a", (center, function(center)), xytext=(3, 14), textcoords="offset points")
    axis.annotate(
        "a+h", (points[2], function(points[2])), xytext=(3, 14), textcoords="offset points"
    )
    axis.set(xlabel="posición", ylabel="altura", title="Una derivada se estima dando pasitos")
    axis.grid(True)
    axis.legend(ncol=2, loc="upper left")
    _save(figure, "03_diferencias_finitas.png")


def step_size_tradeoff() -> None:
    """Figura 4: curva en U del compromiso truncamiento/redondeo."""
    # Valores sintéticos pero con escalas compactas: interesa la forma en U,
    # no asociarlos a una función concreta.
    step = np.logspace(-8, 0, 600)
    truncation = 0.1 * step**2
    roundoff = 1e-12 / step
    total = truncation + roundoff
    best_index = int(np.argmin(total))

    figure, axis = plt.subplots(figsize=(9.2, 5.0))
    axis.loglog(step, truncation, color=ORANGE, lw=2.4, label="truncamiento")
    axis.loglog(step, roundoff, color=RED, lw=2.4, label="redondeo")
    axis.loglog(step, total, color=BLUE, lw=3.2, label="error total")
    axis.scatter(step[best_index], total[best_index], color=GREEN, s=85, zorder=6)
    axis.annotate(
        "zona de equilibrio",
        (step[best_index], total[best_index]),
        xytext=(-85, 38),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": GREEN},
        color=GREEN,
        weight="bold",
    )
    axis.text(1.5e-8, 2e-3, "h demasiado pequeño", color=RED, ha="left")
    axis.text(8e-2, 2e-2, "h demasiado grande", color=ORANGE, ha="center")
    axis.set(xlabel="tamaño del paso h", ylabel="error (escala logarítmica)")
    axis.set_title("El mejor paso está entre dos errores")
    axis.grid(True, which="both")
    axis.legend()
    _save(figure, "04_equilibrio_paso.png")


def pascal_visual() -> None:
    """Figura 5: triángulo de Pascal con flechas de suma entre vecinos."""
    triangle = pascal_triangle(6)
    figure, axis = plt.subplots(figsize=(9.2, 6.1))
    axis.set_aspect("equal")
    axis.axis("off")

    for row_index, row in enumerate(triangle):
        y = -row_index
        for column_index, value in enumerate(row):
            x = column_index - row_index / 2
            normalized = value / max(row)
            color = plt.cm.Blues(0.25 + 0.65 * normalized)
            axis.add_patch(
                Circle((x, y), 0.36, facecolor=color, edgecolor=DARK_BLUE, linewidth=1.3)
            )
            axis.text(x, y, str(value), ha="center", va="center", weight="bold", color=INK)
            if row_index < len(triangle) - 1:
                axis.plot([x, x - 0.5], [y - 0.37, y - 0.63], color="#98A2B3", lw=0.8)
                axis.plot([x, x + 0.5], [y - 0.37, y - 0.63], color="#98A2B3", lw=0.8)

    axis.annotate(
        "3 + 3 = 6",
        xy=(0, -4),
        xytext=(3.0, -3.5),
        arrowprops={"arrowstyle": "->", "color": ORANGE, "lw": 2},
        color=ORANGE,
        fontsize=12,
        weight="bold",
    )
    axis.set_xlim(-4.1, 4.1)
    axis.set_ylim(-6.6, 0.7)
    axis.set_title("Pascal: cada círculo interior suma sus dos padres", pad=12, weight="bold")
    _save(figure, "05_pascal_visual.png")


def mixed_derivative_stencil() -> None:
    """Figura 6: producto tensorial para una derivada mixta f_xy."""
    weights = np.outer(np.array([-0.5, 0.0, 0.5]), np.array([-0.5, 0.0, 0.5]))
    cmap = LinearSegmentedColormap.from_list("signed", [BLUE, "white", RED])
    figure, axis = plt.subplots(figsize=(7.4, 6.0))
    image = axis.imshow(weights, cmap=cmap, vmin=-0.25, vmax=0.25, origin="lower")
    labels = ["-h", "0", "+h"]
    axis.set_xticks(range(3), labels)
    axis.set_yticks(range(3), labels)
    axis.set_xlabel("pasitos en x")
    axis.set_ylabel("pasitos en y")
    axis.set_title(r"Plantilla mixta: combinar cambios en $x$ y en $y$")
    for row in range(3):
        for column in range(3):
            value = weights[row, column]
            axis.text(
                column,
                row,
                f"{value:+.2f}",
                ha="center",
                va="center",
                fontsize=12,
                weight="bold",
                color="white" if abs(value) > 0.15 else INK,
            )
    figure.colorbar(image, ax=axis, shrink=0.82, label="peso antes de dividir por h²")
    figure.tight_layout()
    _save(figure, "06_plantilla_mixta.png")


def taylor_orders() -> None:
    """Figura 7: cómo se agregan detalles al aumentar el orden de Taylor."""
    x = np.linspace(-3.5, 3.5, 800)
    original = np.cos(x)
    approximations = {
        0: np.ones_like(x),
        2: 1 - x**2 / math.factorial(2),
        4: 1 - x**2 / math.factorial(2) + x**4 / math.factorial(4),
        6: 1 - x**2 / math.factorial(2) + x**4 / math.factorial(4) - x**6 / math.factorial(6),
    }

    figure, axes = plt.subplots(2, 2, figsize=(10.3, 7.2), sharex=True, sharey=True)
    for axis, (order, approximation) in zip(axes.flat, approximations.items(), strict=True):
        axis.plot(x, original, color=BLUE, lw=3, label="cos(x)")
        axis.plot(x, approximation, color=ORANGE, lw=2.4, ls="--", label=f"Taylor N={order}")
        axis.axvspan(-1, 1, color=GREEN, alpha=0.08)
        axis.axvline(0, color=RED, lw=1, ls=":")
        axis.set_title(f"Orden N={order}")
        axis.set_ylim(-2.2, 2.2)
        axis.grid(True)
    axes[0, 0].legend(loc="lower center")
    for axis in axes[1, :]:
        axis.set_xlabel("x")
    for axis in axes[:, 0]:
        axis.set_ylabel("altura")
    figure.suptitle(
        "Cada orden añade una nueva capa de detalle alrededor del centro", weight="bold"
    )
    figure.tight_layout()
    _save(figure, "07_ordenes_taylor.png")


def levels_accuracy() -> None:
    """Figura 8: error de derivadas de exp(x+y) para los tres niveles."""
    parsed = parse_function("exp(x+y)")
    models = {
        ComputationLevel.BEGINNER: build_taylor_model(
            parsed.numpy, order=8, level=ComputationLevel.BEGINNER
        ),
        ComputationLevel.ADVANCED: build_taylor_model(
            parsed.numpy, order=8, level=ComputationLevel.ADVANCED, accuracy=6
        ),
        ComputationLevel.HERO: build_taylor_model(
            parsed.mpmath,
            order=8,
            level=ComputationLevel.HERO,
            accuracy=6,
            precision=100,
        ),
    }
    labels = ["beginner", "advanced", "hero"]
    colors = [ORANGE, BLUE, GREEN]
    maximum_errors = [
        max(abs(value - 1.0) for value in models[ComputationLevel(label)].derivatives.values())
        for label in labels
    ]
    maximum_errors = np.maximum(maximum_errors, 1e-16)

    figure, axis = plt.subplots(figsize=(8.8, 5.0))
    bars = axis.bar(labels, maximum_errors, color=colors, width=0.58)
    axis.set_yscale("log")
    axis.set_ylabel("mayor error de las derivadas (escala log)")
    axis.set_title(r"Orden 8 para $e^{x+y}$: todas las derivadas exactas valen 1")
    axis.grid(True, axis="y", which="both")
    for bar, value in zip(bars, maximum_errors, strict=True):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            value * 1.7,
            f"{value:.1e}",
            ha="center",
            va="bottom",
            weight="bold",
        )
    axis.text(
        2,
        2e-14,
        "más dígitos\nprotegen N alto",
        ha="center",
        color=GREEN,
        weight="bold",
    )
    _save(figure, "08_niveles_precision.png")


def intersection_surfaces() -> None:
    """Figura 9: salida real del proyecto, incluida la curva de intersección."""
    parsed = parse_function("sin(x)*cos(y)")
    model = build_taylor_model(parsed.numpy, order=3, level="advanced", accuracy=6)
    figure, _ = plot_comparison(
        parsed.numpy,
        model,
        x_range=(-1.7, 1.7),
        y_range=(-1.7, 1.7),
        points=101,
        show=False,
        title_expression=r"\sin(x)\cos(y)",
    )
    figure.set_size_inches(13.2, 4.7)
    _save(figure, "09_intersecciones.png")


def main() -> None:
    """Regenera el conjunto completo de recursos visuales."""
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    _style()
    generators = (
        surface_as_mountain,
        local_magnifying_glass,
        finite_difference_steps,
        step_size_tradeoff,
        pascal_visual,
        mixed_derivative_stencil,
        taylor_orders,
        levels_accuracy,
        intersection_surfaces,
    )
    for generator in generators:
        generator()
        print(f"✓ {generator.__name__}")
    print(f"\nFiguras guardadas en: {OUTPUT_DIRECTORY}")


if __name__ == "__main__":
    main()
