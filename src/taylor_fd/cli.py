"""Interfaz de terminal completamente en español."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from taylor_fd.core import ComputationLevel, TaylorModel, build_taylor_model
from taylor_fd.expressions import parse_function
from taylor_fd.plotting import plot_comparison

_LEVEL_EXPLANATIONS = {
    ComputationLevel.BEGINNER: (
        "BEGINNER — diferencias progresivas O(h); pesos y Taylor salen de Pascal."
    ),
    ComputationLevel.ADVANCED: (
        "ADVANCED — Fornberg centrado + Richardson + estimación de error en float64."
    ),
    ComputationLevel.HERO: ("HERO — Fornberg + Richardson con precisión arbitraria de mpmath."),
}


def _pair(values: list[float]) -> tuple[float, float]:
    """Convierte una lista argparse de longitud dos en tupla tipada."""
    return values[0], values[1]


def build_parser() -> argparse.ArgumentParser:
    """Define argumentos con ejemplos y nombres en español."""
    parser = argparse.ArgumentParser(
        prog="taylor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Aproxima f(x,y) con Taylor, derivadas por diferencias finitas\n"
            "y coeficientes del triángulo de Pascal.\n\n"
            "NIVELES:\n"
            "  beginner  fórmula corta para aprender; baja precisión\n"
            "  advanced  recomendado: Fornberg centrado y Richardson\n"
            "  hero      N alto: igual que advanced, con 80+ dígitos internos"
        ),
        epilog=(
            "Ejemplo:\n  uv run taylor --funcion 'sin(x)*cos(y)' -N 6 --nivel hero --no-mostrar"
        ),
    )
    parser.add_argument("--funcion", default="exp(-(x**2 + y**2))", help="Expresión en x e y.")
    parser.add_argument("-N", "--orden", type=int, default=4, help="Orden total de Taylor.")
    parser.add_argument(
        "--nivel",
        choices=[level.value for level in ComputationLevel],
        default=ComputationLevel.ADVANCED.value,
        help="Nivel de cálculo; advanced es el recomendado.",
    )
    parser.add_argument("--centro", nargs=2, type=float, default=[0.0, 0.0], metavar=("A", "B"))
    parser.add_argument("--paso", nargs="+", type=float, help="Un valor h o dos valores hx hy.")
    parser.add_argument(
        "--precision-plantilla",
        type=int,
        default=4,
        metavar="P",
        help="Orden par de la plantilla centrada (advanced/hero).",
    )
    parser.add_argument("--digitos", type=int, default=80, help="Dígitos internos del modo hero.")
    parser.add_argument("--rango-x", nargs=2, type=float, default=[-2.0, 2.0])
    parser.add_argument("--rango-y", nargs=2, type=float, default=[-2.0, 2.0])
    parser.add_argument("--puntos", type=int, default=121, help="Resolución por eje.")
    parser.add_argument(
        "--salida", default="taylor_aproximacion.png", help="Archivo PNG de salida."
    )
    parser.add_argument("--no-mostrar", action="store_true", help="No abre ventana interactiva.")
    parser.add_argument("--sin-tabla", action="store_true", help="Oculta derivadas y coeficientes.")
    return parser


def _parse_step(values: list[float] | None) -> float | tuple[float, float] | None:
    """Acepta ``--paso h`` y ``--paso hx hy`` sin ambigüedad."""
    if values is None:
        return None
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return values[0], values[1]
    raise ValueError("--paso acepta uno (h) o dos valores (hx hy).")


def _print_summary(model: TaylorModel, *, show_table: bool) -> None:
    """Explica qué pasó y muestra la trazabilidad Pascal → derivada → término."""
    print("\n" + "=" * 78)
    print(_LEVEL_EXPLANATIONS[model.level])
    print(f"Centro={model.center} · N={model.order} · paso={model.step}")
    print("=" * 78)
    print("\nTriángulo de Pascal usado para ensamblar Taylor:")
    width = len(" ".join(map(str, model.pascal[-1])))
    for row in model.pascal:
        print(" ".join(map(str, row)).center(width))
    if not show_table:
        return

    print("\nCada fila sigue: parcial → Pascal → valor finito → coeficiente Taylor")
    print("  (i,j)        Pascal        derivada             coeficiente          incertidumbre")
    for term in model.terms:
        uncertainty = "—" if term.uncertainty != term.uncertainty else f"{term.uncertainty:.2e}"
        print(
            f"  ({term.x_order},{term.y_order})"
            f"{term.pascal_coefficient:>13d}"
            f"{term.derivative:>20.10g}"
            f"{term.coefficient:>22.10g}"
            f"{uncertainty:>22}"
        )


def main(argv: list[str] | None = None) -> None:
    """Ejecuta lectura → derivadas → Taylor → intersecciones → PNG."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        parsed = parse_function(args.funcion)
        level = ComputationLevel(args.nivel)

        # Hero necesita el evaluador mpmath; los otros usan el más rápido de NumPy.
        scalar_function = parsed.mpmath if level is ComputationLevel.HERO else parsed.numpy
        model = build_taylor_model(
            scalar_function,
            center=_pair(args.centro),
            order=args.orden,
            level=level,
            step=_parse_step(args.paso),
            accuracy=args.precision_plantilla,
            precision=args.digitos,
        )
        _print_summary(model, show_table=not args.sin_tabla)

        # En CI o servidores sin pantalla se guarda el PNG sin intentar abrir GUI.
        has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        should_show = not args.no_mostrar and has_display
        _, metrics = plot_comparison(
            parsed.numpy,
            model,
            x_range=_pair(args.rango_x),
            y_range=_pair(args.rango_y),
            points=args.puntos,
            output=Path(args.salida),
            show=should_show,
            title_expression=str(parsed.expression),
        )
    except (ValueError, TypeError, ZeroDivisionError) as error:
        parser.error(str(error))

    print(f"\nRMSE en la malla: {metrics['rmse']:.6g}")
    print(f"Error máximo:       {metrics['max_error']:.6g}")
    print(f"Gráfica guardada:   {Path(args.salida).resolve()}")
    if not should_show and not args.no_mostrar:
        print("No se detectó una pantalla; se guardó el PNG sin abrir una ventana.")
