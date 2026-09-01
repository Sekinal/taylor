# Taylor bivariado por diferencias finitas

Programa educativo y numérico para aproximar una función cualquiera
`f(x, y)` mediante un polinomio de Taylor total de orden `N`. Las derivadas
parciales se obtienen **numéricamente**, los coeficientes del polinomio salen
explícitamente del **triángulo de Pascal**, y una gráfica 3D muestra la función,
la aproximación y las curvas donde ambas superficies se intersectan.

## Inicio rápido con uv

```bash
uv sync
uv run taylor --funcion "sin(x)*cos(y)" -N 5 --nivel advanced
```

Esto abre la gráfica si existe una pantalla y siempre guarda
`taylor_aproximacion.png`. En un servidor o en CI:

```bash
uv run taylor --funcion "exp(-(x**2+y**2))" -N 6 --no-mostrar
```

Consulta todas las opciones con:

```bash
uv run taylor --help
```

## Los tres niveles, sin perderse

### Nivel 1: `beginner`

Objetivo: que la fórmula sea fácil de seguir a mano.

Las diferencias progresivas usan directamente filas de Pascal:

```text
D_x^i D_y^j f(a,b) ≈ 1/(hx^i hy^j) · Σp Σq
  (-1)^(i-p+j-q) C(i,p) C(j,q) f(a+p·hx, b+q·hy)
```

- Ventaja: Pascal aparece tanto en las derivadas como en Taylor.
- Costo: el error de la derivada es de primer orden, `O(h)`.
- Úsalo para aprender o demostrar el procedimiento con `N` pequeño.

```bash
uv run taylor --funcion "x**2 + 3*x*y + y**2" -N 2 --nivel beginner
```

### Nivel 2: `advanced` (recomendado)

Objetivo: un resultado serio y rápido en precisión normal (`float64`).

1. Construye una plantilla simétrica alrededor del centro.
2. Genera pesos para cualquier derivada con la recurrencia de Fornberg.
3. Forma derivadas mixtas con el producto tensorial de los pesos de `x` e `y`.
4. Reutiliza todas las evaluaciones de la función en una caché.
5. Repite con `h`, `h/2` y `h/4`.
6. Aplica extrapolación de Richardson y reporta una incertidumbre estimada.

```bash
uv run taylor \
  --funcion "exp(x)*cos(y)" \
  --centro 0.2 -0.3 \
  -N 6 \
  --nivel advanced \
  --paso 0.1 \
  --precision-plantilla 6
```

### Nivel 3: `hero`

Objetivo: combatir la cancelación y el redondeo de derivadas de orden alto.

Usa el mismo algoritmo trazable de `advanced`, pero todos los nodos, pesos,
evaluaciones, refinamientos y extrapolaciones se calculan con precisión
arbitraria de `mpmath`. Solamente los coeficientes finales se convierten a
`float` para la gráfica de Matplotlib.

```bash
uv run taylor \
  --funcion "sin(x*y)*exp(x-y)" \
  --centro 0.1 0.2 \
  -N 10 \
  --nivel hero \
  --digitos 120 \
  --precision-plantilla 8
```

`hero` no vuelve matemáticamente derivable a una función que no lo sea. El
punto y toda la plantilla deben estar dentro del dominio, y `f` debe poseer las
derivadas solicitadas.

## De Pascal al Taylor de dos variables

Para `dx=x-a`, `dy=y-b` y `j=n-i`, el programa ensambla:

```text
T_N(x,y) = Σ(n=0..N) Σ(i=0..n)
  [C(n,i)/n!] · [D_x^i D_y^j f(a,b)] · dx^i · dy^j
```

La fila `n` de Pascal entrega todos los `C(n,i)`. Aunque
`C(n,i)/n! = 1/(i!j!)`, el código conserva deliberadamente la primera forma
para que el origen de cada coeficiente sea visible. La terminal imprime la
cadena completa: orden parcial, valor de Pascal, derivada finita, coeficiente
de Taylor e incertidumbre.

## Funciones admitidas por la CLI

Se permiten `x`, `y`, números, `pi`, `e`, los operadores `+ - * / **` y:

```text
sin cos tan asin acos atan sinh cosh tanh exp log sqrt abs
```

La expresión se recorre mediante un AST restringido: no se ejecuta como código
Python libre. Desde una aplicación también se puede usar cualquier callable:

```python
from taylor_fd import build_taylor_model


def mi_funcion(x, y):
    return x**2 * y + y**3


modelo = build_taylor_model(mi_funcion, center=(0.0, 0.0), order=3)
print(modelo.evaluate(0.2, 0.4))
```

## Cómo leer la gráfica

- Panel izquierdo: función original.
- Panel central: polinomio de Taylor numérico.
- Panel derecho: ambas superficies superpuestas.
- Líneas rojas: contornos `f(x,y) - T_N(x,y) = 0`, elevados a su coordenada
  `z`; son intersecciones reales de las dos superficies.

Recuerda que Taylor es una aproximación **local**. Aumentar el rango de la
gráfica puede hacer crecer el error aunque las derivadas estén bien calculadas.

## Calidad, pruebas y GitHub

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

El workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) ejecuta esas
tres verificaciones en cada `push` y `pull_request`. Para crear el remoto cuando
hayas decidido visibilidad y propietario:

```bash
gh repo create taylor-finite-differences --source=. --public --push
```

Cambia `--public` por `--private` si corresponde.

## Fundamento numérico

La generación de pesos sigue B. Fornberg, *Generation of Finite Difference
Formulas on Arbitrarily Spaced Grids*, Mathematics of Computation 51 (1988),
699–706, DOI `10.1090/S0025-5718-1988-0935077-0`. El modo `hero` sigue la
recomendación práctica de aumentar la precisión para diferencias de orden alto,
documentada también por `mpmath`. Las diferencias finitas siempre equilibran
error de truncamiento (h demasiado grande) y redondeo (h demasiado pequeño),
razón por la cual los niveles avanzados refinan el paso y muestran incertidumbre.
