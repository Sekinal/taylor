"""Pruebas de integración: CLI, visualización y documentación compilada."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from taylor_fd import build_taylor_model
from taylor_fd.cli import main
from taylor_fd.plotting import plot_comparison


def test_plot_comparison_creates_three_panels_and_png(tmp_path: Path) -> None:
    """La tubería gráfica debe producir superficies, métricas y un PNG real."""

    def function(x, y):
        return np.exp(x + y)

    model = build_taylor_model(function, order=2, center=(0.0, 0.0))
    output = tmp_path / "comparacion.png"
    figure, metrics = plot_comparison(
        function,
        model,
        x_range=(-0.5, 0.5),
        y_range=(-0.5, 0.5),
        points=31,
        output=output,
        show=False,
    )

    try:
        assert len(figure.axes) == 3
        assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert output.stat().st_size > 10_000
        assert np.isfinite(metrics["rmse"])
        assert np.isfinite(metrics["max_error"])
        assert metrics["max_error"] >= metrics["rmse"] >= 0
    finally:
        plt.close(figure)


def test_cli_runs_end_to_end_in_spanish(tmp_path: Path, capsys) -> None:
    """La interfaz completa debe calcular, informar y guardar su resultado."""
    output = tmp_path / "cli.png"
    main(
        [
            "--funcion",
            "sin(x)*cos(y)",
            "-N",
            "3",
            "--nivel",
            "advanced",
            "--rango-x",
            "-0.5",
            "0.5",
            "--rango-y",
            "-0.5",
            "0.5",
            "--puntos",
            "25",
            "--salida",
            str(output),
            "--no-mostrar",
            "--sin-tabla",
        ]
    )
    terminal = capsys.readouterr().out

    assert "Triángulo de Pascal" in terminal
    assert "ADVANCED" in terminal
    assert "RMSE en la malla" in terminal
    assert "Gráfica guardada" in terminal
    assert output.exists()
    plt.close("all")


def test_typst_guide_and_pdf_are_complete() -> None:
    """El PDF versionado debe corresponder a una guía extensa con ejercicios."""
    source = Path("docs/guia_eli5.typ").read_text(encoding="utf-8")
    pdf = Path("docs/guia_eli5.pdf").read_bytes()
    assets = sorted(Path("docs/assets").glob("*.png"))

    assert source.count("=== Ejercicio ") >= 20
    assert source.count("=== Solución ") >= 20
    assert "Nivel 0 — Intuición" in source
    assert "Nivel 4 — Diagnóstico hero" in source
    assert "La fórmula de Taylor, pieza por pieza" in source
    assert source.count("#figure(") >= 9
    assert len(assets) == 9
    assert all(asset.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for asset in assets)
    assert all(asset.stat().st_size > 40_000 for asset in assets)
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 100_000
