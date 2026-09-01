// ==========================================================================
// GUÍA ELI5 — TAYLOR BIVARIADO MEDIANTE DIFERENCIAS FINITAS
//
// Este documento no usa paquetes externos: se compila de forma reproducible
// con `typst compile docs/guia_eli5.typ docs/guia_eli5.pdf`.
// ==========================================================================

#set document(
  title: "Taylor de dos variables, explicado como si tuvieras 5 años",
  author: "Proyecto Taylor",
)
#set page(
  paper: "a4",
  margin: (x: 22mm, top: 20mm, bottom: 22mm),
  header: context {
    if counter(page).get().first() > 1 {
      set text(size: 8pt, fill: rgb("667085"))
      grid(
        columns: (1fr, auto),
        [Taylor bivariado · Guía ELI5],
        [#counter(page).display("1")],
      )
      line(length: 100%, stroke: rgb("d0d5dd"))
    }
  },
)
#set text(lang: "es", size: 10.5pt)
#set par(justify: true, leading: 0.72em)
#set heading(numbering: "1.1", outlined: true)
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  it
}
#set table(stroke: rgb("d0d5dd"), inset: 7pt)
#show raw.where(block: true): block.with(
  fill: rgb("f8fafc"),
  stroke: rgb("d0d5dd"),
  radius: 5pt,
  inset: 10pt,
)

#let blue = rgb("175cd3")
#let dark-blue = rgb("1849a9")
#let orange = rgb("f79009")
#let green = rgb("12b76a")
#let red = rgb("d92d20")
#let ink = rgb("101828")
#let soft-blue = rgb("eff8ff")
#let soft-orange = rgb("fffaeb")
#let soft-green = rgb("ecfdf3")
#let soft-red = rgb("fef3f2")
#let gray = rgb("f2f4f7")

#let idea(title, body) = block(
  width: 100%,
  fill: soft-blue,
  stroke: blue,
  radius: 7pt,
  inset: 12pt,
)[
  #text(fill: dark-blue, weight: "bold")[💡 #title]
  #v(4pt)
  #body
]

#let warning(title, body) = block(
  width: 100%,
  fill: soft-orange,
  stroke: orange,
  radius: 7pt,
  inset: 12pt,
)[
  #text(fill: rgb("b54708"), weight: "bold")[⚠ #title]
  #v(4pt)
  #body
]

#let checkpoint(body) = block(
  width: 100%,
  fill: soft-green,
  stroke: green,
  radius: 7pt,
  inset: 12pt,
)[
  #text(fill: rgb("027a48"), weight: "bold")[✓ Comprobación rápida]
  #v(4pt)
  #body
]

#let word(term, meaning) = [
  #text(weight: "bold", fill: dark-blue)[#term:] #meaning
]

// Celda uniforme para los encabezados de todas las tablas.
#let th(body) = table.cell(fill: dark-blue, inset: 7pt)[
  #text(fill: white, weight: "bold")[#body]
]

// --------------------------------------------------------------------------
// PORTADA
// --------------------------------------------------------------------------

#align(center)[
  #v(20mm)
  #text(size: 16pt, fill: orange, weight: "bold")[GUÍA VISUAL · ELI5 → HERO]
  #v(8mm)
  #text(size: 30pt, fill: ink, weight: "bold")[Taylor de dos variables]
  #v(3mm)
  #text(size: 19pt, fill: dark-blue)[con diferencias finitas y Pascal]
  #v(13mm)

  #rect(width: 82%, height: 48mm, fill: soft-blue, stroke: blue, radius: 10pt)[
    #align(center + horizon)[
      #text(size: 13pt)[
        Una explicación que empieza con una montaña de plastilina,
        llega paso a paso a la fórmula y termina enseñando
        exactamente qué hace el programa.
      ]
    ]
  ]

  #v(14mm)
  #text(size: 13pt, weight: "bold")[No necesitas saber cálculo para empezar.]
  #v(3mm)
  #text(fill: rgb("475467"))[
    Python · uv · NumPy · mpmath · Matplotlib · Ruff · Pytest
  ]
  #v(20mm)
  #text(size: 9pt, fill: rgb("667085"))[
    Documento reproducible escrito en Typst · Septiembre de 2026
  ]
]

#pagebreak()

= Antes de comenzar: el mapa completo

Imagina que alguien te da una función complicada y te pregunta:

#align(center)[
  #text(size: 18pt, fill: dark-blue, weight: "bold")[
    “¿Puedes construir una versión más sencilla que se parezca a ella?”
  ]
]

Eso es todo lo que vamos a hacer. La versión sencilla será un *polinomio*:
una suma de números, $x$, $y$, $x^2$, $x y$, $y^2$ y más piezas parecidas.

#idea[La historia en una sola frase][
  Miramos la altura y las inclinaciones de la función cerca de un punto,
  estimamos esas inclinaciones dando pasitos diminutos, y mezclamos toda la
  información usando números del triángulo de Pascal.
]

== Las siete estaciones del viaje

#table(
  columns: (10mm, 42mm, 1fr),
  align: (center, left, left),
  table.header(
    th[N.º],
    th[Idea],
    th[Pregunta que responde],
  ),
  [1], [Función], [¿Cómo es la superficie original?],
  [2], [Centro], [¿Alrededor de qué punto queremos copiarla?],
  [3], [Derivadas], [¿Hacia dónde se inclina y cómo se curva?],
  [4], [Diferencias finitas], [¿Cómo estimamos inclinaciones sin derivar a mano?],
  [5], [Pascal], [¿Cómo repartimos cada orden entre $x$ e $y$?],
  [6], [Taylor], [¿Cómo armamos el modelo sencillo?],
  [7], [Gráfica], [¿Dónde coinciden el original y el modelo?],
)

#checkpoint[
  Si por ahora entiendes “vamos a copiar localmente una forma complicada con
  piezas sencillas”, ya tienes la idea más importante.
]

= Una función de dos variables es una montaña

Una función de una variable, como $f(x)=x^2$, recibe un número y devuelve otro.
Podemos dibujarla como una curva.

Una función de dos variables recibe *dos* números:

$
  f(x,y) = "una altura"
$

Piensa en un mapa:

- $x$ dice cuánto caminar al este o al oeste.
- $y$ dice cuánto caminar al norte o al sur.
- $f(x,y)$ dice la altura del suelo en ese lugar.

#figure(
  image("assets/01_funcion_montana.png", width: 88%),
  caption: [
    *Función como montaña.* Cada pareja $(x,y)$ elige un lugar y la superficie
    da su altura. El punto rojo es el centro donde colocamos nuestra lupa.
  ],
)

#align(center)[
  #grid(
    columns: (38mm, 12mm, 38mm, 12mm, 38mm),
    align: center + horizon,
    rect(width: 38mm, height: 24mm, fill: soft-blue, stroke: blue, radius: 6pt)[
      #align(center + horizon)[Posición $x$]
    ],
    [#text(size: 18pt, fill: orange)[+]],
    rect(width: 38mm, height: 24mm, fill: soft-blue, stroke: blue, radius: 6pt)[
      #align(center + horizon)[Posición $y$]
    ],
    [#text(size: 18pt, fill: green)[→]],
    rect(width: 38mm, height: 24mm, fill: soft-green, stroke: green, radius: 6pt)[
      #align(center + horizon)[Altura $f(x,y)$]
    ],
  )
]

== Ejemplo: un tazón

$
  f(x,y) = x^2 + y^2
$

En $(0,0)$ la altura es cero. Al alejarnos en cualquier dirección, la altura
crece. La superficie parece un tazón.

== Ejemplo: una silla de montar

$
  f(x,y) = x^2 - y^2
$

En la dirección de $x$ sube, pero en la dirección de $y$ baja. El mismo punto
puede tener comportamientos diferentes según la dirección.

#idea[Por qué necesitamos varias derivadas][
  Una sola “inclinación” ya no basta. Necesitamos preguntar por la inclinación
  en $x$, la inclinación en $y$, las curvaturas y también cómo interactúan
  ambas direcciones.
]

= El centro: nuestra lupa matemática

Taylor no intenta copiar toda la montaña de una vez. Primero elegimos un punto:

$
  (a,b)
$

Este es el *centro de expansión*. Imagina que colocamos una lupa allí.

#align(center)[
  #rect(width: 80%, fill: gray, radius: 8pt, inset: 14pt)[
    #align(center)[
      Mundo completo: quizá enorme y complicado
      #v(7pt)
      #rect(width: 46%, fill: soft-orange, stroke: orange, radius: 50%, inset: 12pt)[
        #align(center)[Zona vista por la lupa alrededor de $(a,b)$]
      ]
    ]
  ]
]

Cuanto más cerca estamos del centro, mejor suele funcionar la copia de Taylor.

#figure(
  image("assets/02_lupa_local.png", width: 100%),
  caption: [
    *La misma aproximación vista con dos escalas.* Cerca de cero las curvas se
    confunden; lejos del centro empiezan a separarse. No cambió el polinomio:
    cambió cuánto nos alejamos.
  ],
)

== Un cambio de coordenadas muy útil

En vez de repetir $x-a$ e $y-b$ con palabras, llamamos:

$
  Delta x = x-a, quad Delta y = y-b
$

- $Delta x$ es cuánto nos alejamos horizontalmente del centro.
- $Delta y$ es cuánto nos alejamos verticalmente del centro.
- En el propio centro, ambos valen cero.

#warning[Local no significa global][
  Un Taylor excelente cerca del centro puede ser pésimo lejos de él. Si el
  dibujo usa un rango muy grande, ver separación entre superficies no implica
  automáticamente que el algoritmo esté roto.
]

= Derivadas: velocímetros de la superficie

Una derivada responde: “si doy un pasito, ¿cuánto cambia la salida?”.

En una carretera:

- la posición dice dónde estás;
- la primera derivada se parece a un velocímetro;
- la segunda derivada cuenta cómo cambia ese velocímetro.

En nuestra montaña tenemos dos velocímetros principales:

$
  f_x(a,b) quad "y" quad f_y(a,b)
$

$f_x$ mide el cambio al movernos en $x$ manteniendo $y$ quieta. $f_y$ hace lo
mismo al movernos en $y$.

== Órdenes de derivación

#table(
  columns: (30mm, 35mm, 1fr),
  table.header(
    th[Orden total],
    th[Símbolos],
    th[Qué cuentan],
  ),
  [0], [$f$], [La altura.],
  [1], [$f_x, f_y$], [Las dos inclinaciones.],
  [2], [$f_(x x), f_(x y), f_(y y)$], [Curvaturas e interacción.],
  [3], [$f_(x x x), f_(x x y), f_(x y y), f_(y y y)$], [Cómo cambian las curvaturas.],
)

La derivada $f_(x y)$ es *mixta*: primero pregunta por un cambio en una
dirección y luego por cómo cambia eso en la otra.

== ¿Cuántas derivadas aparecen hasta N?

En el orden exacto $n$ aparecen $n+1$ combinaciones. Hasta orden $N$ aparecen:

$
  1 + 2 + dots + (N+1) = ((N+1)(N+2))/2
$

Con $N=4$ son 15 términos. Con $N=10$ son 66. Por eso reutilizar cálculos es
importante.

= Diferencias finitas: medir con pasitos

Supón que no sabemos derivar una función a mano, pero sí podemos evaluarla.
Damos un paso pequeño $h$:

$
  "inclinación" approx (f(a+h)-f(a))/h
$

Esto es simplemente:

$
  ("altura nueva" - "altura anterior")/("distancia caminada")
$

#figure(
  image("assets/03_diferencias_finitas.png", width: 92%),
  caption: [
    *Medir una pendiente con puntos cercanos.* La recta naranja mira hacia
    delante. La azul usa un punto a cada lado; para esta parábola coincide con
    la tangente verde exacta.
  ],
)

#align(center)[
  #grid(
    columns: (1fr, auto, 1fr),
    align: center + horizon,
    rect(fill: soft-blue, stroke: blue, radius: 6pt, inset: 10pt)[
      En $a$: altura $f(a)$
    ],
    [#text(size: 18pt, fill: orange)[— paso $h$ →]],
    rect(fill: soft-green, stroke: green, radius: 6pt, inset: 10pt)[
      En $a+h$: altura $f(a+h)$
    ],
  )
]

== La trampa de hacer h demasiado pequeño

Parece que un paso diminuto siempre debería ser mejor. No es así:

- Si $h$ es grande, vemos demasiada montaña y perdemos detalle local.
- Si $h$ es minúsculo, restamos números casi iguales y la computadora pierde
  dígitos útiles.

#figure(
  image("assets/04_equilibrio_paso.png", width: 92%),
  caption: [
    *El error tiene dos enemigos.* Al reducir $h$ baja el truncamiento naranja,
    pero crece el redondeo rojo. El punto verde marca la zona de equilibrio.
    Los valores son ilustrativos; la forma de “U” es la lección.
  ],
)

#align(center)[
  #table(
    columns: (1fr, 1fr, 1fr),
    align: center,
    table.header(
      th[h grande],
      th[h razonable],
      th[h microscópico],
    ),
    [Error de truncamiento],
    [Buen equilibrio],
    [Error de redondeo],
    [🪨], [✅], [🔬],
  )
]

== Dos variables

Para $x$ usamos un paso $h_x$. Para $y$ usamos $h_y$. Una derivada mixta se
construye evaluando una pequeña cuadrícula alrededor del centro y combinando
sus alturas con pesos positivos y negativos.

#checkpoint[
  Diferencias finitas = estimar derivadas mirando valores cercanos. No se usa
  una derivada simbólica escondida.
]

= Pascal: una máquina para repartir

El triángulo de Pascal empieza con un 1. Cada nuevo número interior es la suma
de los dos que tiene encima:

#align(center)[
  #text(size: 15pt, weight: "bold", fill: dark-blue)[
    1
    #linebreak()
    1 1
    #linebreak()
    1 2 1
    #linebreak()
    1 3 3 1
    #linebreak()
    1 4 6 4 1
    #linebreak()
    1 5 10 10 5 1
  ]
]

#figure(
  image("assets/05_pascal_visual.png", width: 82%),
  caption: [
    *Pascal construido, no memorizado.* Las líneas muestran los dos padres de
    cada número interior. Por ejemplo, los dos 3 de arriba producen el 6.
  ],
)

== ¿Qué tiene que ver con x e y?

En el orden $n$, debemos repartir $n$ derivadas entre $x$ e $y$.

Para $n=3$ existen cuatro repartos:

#table(
  columns: (1fr, 1fr, 1fr, 1fr),
  align: center,
  table.header(
    th[$x x x$],
    th[$x x y$],
    th[$x y y$],
    th[$y y y$],
  ),
  [$f_(x x x)$], [$f_(x x y)$], [$f_(x y y)$], [$f_(y y y)$],
  [1], [3], [3], [1],
)

¡La fila es precisamente $1,3,3,1$!

== El binomial

El número en la posición $i$ de la fila $n$ se escribe:

$
  binom(n,i)
$

El programa *construye* todas las filas sumando vecinos. Después lee esos
números para ensamblar Taylor. No necesita una tabla guardada de antemano.

#idea[Dos trabajos de Pascal][
  En `beginner`, Pascal crea los pesos de las diferencias progresivas y también
  los coeficientes de Taylor. En `advanced` y `hero`, Fornberg crea los pesos
  numéricos, pero Pascal sigue ensamblando todos los términos de Taylor.
]

= La fórmula de Taylor, pieza por pieza

Primero la mostramos completa. No intentes memorizarla:

$
  T_N(x,y) = sum_(n=0)^N sum_(i=0)^n
  frac(binom(n,i), n!)
  (partial^n f)/(partial x^i partial y^(n-i))(a,b)
  (x-a)^i (y-b)^(n-i)
$

Ahora la desarmamos.

== $T_N(x,y)$

Es el nombre de nuestra copia sencilla. La letra $T$ recuerda a Taylor y $N$
indica el mayor orden incluido.

== Las dos sumas

- La suma exterior recorre los órdenes $0,1,2,...,N$.
- La suma interior recorre todas las formas de repartir cada orden entre $x$ e
  $y$.

== $binom(n,i)$

Es el número tomado de Pascal. Dice cuántas veces aparece ese reparto.

== $n!$

El factorial equilibra el tamaño de los términos:

$
  0! = 1, quad 1! = 1, quad 2! = 2, quad 3! = 6, quad 4! = 24
$

== La derivada parcial

Cuenta la forma local de la función en el centro. En este proyecto se obtiene
mediante diferencias finitas.

== $(x-a)^i (y-b)^(n-i)$

Cuenta cuánto nos hemos alejado del centro. En el centro, las potencias de
orden positivo desaparecen, por eso $T_N(a,b)=f(a,b)$.

#checkpoint[
  Cada término = número de Pascal × información local × distancia al centro,
  con un factorial para mantener la escala correcta.
]

= Un ejemplo completo que cabe en una hoja

Tomemos:

$
  f(x,y)=x^2+2x y+3y^2, quad (a,b)=(0,0), quad N=2
$

== Paso 1: valor en el centro

$
  f(0,0)=0
$

== Paso 2: primeras derivadas

$
  f_x=2x+2y, quad f_y=2x+6y
$

En el centro ambas valen cero.

== Paso 3: segundas derivadas

$
  f_(x x)=2, quad f_(x y)=2, quad f_(y y)=6
$

== Paso 4: fila 2 de Pascal

$
  1 quad 2 quad 1
$

== Paso 5: ensamblar

$
  T_2(x,y)
  = frac(1,2!) 2x^2
  + frac(2,2!) 2x y
  + frac(1,2!) 6y^2
$

Simplificando:

$
  T_2(x,y)=x^2+2x y+3y^2
$

¡Es exactamente la función original! Esto ocurre porque la función ya era un
polinomio de grado 2 y elegimos $N=2$.

#idea[¿Y si la función es seno o exponencial?][
  Entonces Taylor no suele ser idéntico en todas partes. Se parece mucho cerca
  del centro y mejora localmente al incluir más órdenes, siempre que las
  derivadas se calculen con suficiente precisión.
]

#figure(
  image("assets/07_ordenes_taylor.png", width: 96%),
  caption: [
    *Agregar órdenes añade detalle alrededor del centro.* La franja verde es la
    zona local. De $N=0$ a $N=6$, la curva naranja imita cada vez más a la azul
    antes de separarse lejos de cero.
  ],
)

= Los tres niveles del programa

Los niveles no son tres nombres para lo mismo. Cada uno cambia la estrategia
numérica y tiene un propósito claro.

== Nivel 1 — `beginner`

#rect(width: 100%, fill: soft-blue, stroke: blue, radius: 8pt, inset: 12pt)[
  #text(size: 14pt, weight: "bold", fill: dark-blue)[Objetivo: ver toda la mecánica]

  Usa diferencias progresivas. Sus pesos vienen directamente de Pascal:

  $
    D_x^i D_y^j f(a,b) approx frac(1, h_x^i h_y^j)
    sum_(p=0)^i sum_(q=0)^j
    (-1)^(i-p+j-q) binom(i,p) binom(j,q)
    f(a+p h_x,b+q h_y)
  $

  Es fácil de seguir con lápiz. Su error es aproximadamente $O(h)$, así que no
  es la mejor opción para resultados exigentes.
]

*Elige `beginner` cuando:* estás aprendiendo, explicando en clase o usando un
$N$ pequeño.

== Nivel 2 — `advanced`

#rect(width: 100%, fill: soft-green, stroke: green, radius: 8pt, inset: 12pt)[
  #text(size: 14pt, weight: "bold", fill: rgb("027a48"))[Objetivo: rapidez y buena precisión]

  1. Coloca nodos simétricos a ambos lados del centro.
  2. Genera pesos de cualquier orden con la recurrencia de Fornberg.
  3. Combina pesos de $x$ e $y$ como una cuadrícula.
  4. Evalúa la función una sola vez por punto y guarda el resultado.
  5. Repite con $h$, $h/2$ y $h/4$.
  6. Usa extrapolación de Richardson para reducir el error.
  7. Reporta una incertidumbre estimada.

  Todo se calcula con números normales de 64 bits (`float64`).
]

*Elige `advanced` cuando:* quieres el modo recomendado para órdenes moderados.

== Nivel 3 — `hero`

#rect(width: 100%, fill: soft-orange, stroke: orange, radius: 8pt, inset: 12pt)[
  #text(size: 14pt, weight: "bold", fill: rgb("b54708"))[Objetivo: sobrevivir a órdenes altos]

  Repite exactamente la estrategia de `advanced`, pero usa números con 80,
  120 o más dígitos internos mediante `mpmath`.

  Esto combate la cancelación: en una derivada de orden alto aparecen sumas de
  números grandes con signos contrarios cuyo resultado puede ser pequeño.
]

*Elige `hero` cuando:* $N$ es alto o `advanced` muestra derivadas inestables.

#warning[Hero no hace magia][
  Más dígitos ayudan contra el redondeo, pero no arreglan una función no suave,
  un punto fuera del dominio o una expansión demasiado lejos del centro.
]

#figure(
  image("assets/08_niveles_precision.png", width: 88%),
  caption: [
    *Una prueba con respuesta conocida.* Para $e^(x+y)$ todas las derivadas en
    el origen valen 1. En orden 8, la precisión arbitraria de `hero` conserva
    muchos más dígitos. El eje vertical es logarítmico.
  ],
)

= Fornberg sin misterio

Queremos números $w_k$ que cumplan:

$
  f^(m)(0) approx sum_k w_k f(z_k)
$

Los $z_k$ son posiciones de muestreo y los $w_k$ son pesos. Por ejemplo, para
la primera derivada con nodos $-1,0,1$:

$
  (w_(-1),w_0,w_1)=(-1/2,0,1/2)
$

Al incorporar el paso $h$ obtenemos la conocida diferencia centrada:

$
  f'(a) approx (f(a+h)-f(a-h))/(2h)
$

== ¿Por qué no resolver un sistema gigante?

Podríamos calcular los pesos resolviendo ecuaciones con potencias de los nodos,
pero esos sistemas se vuelven numéricamente incómodos. La recurrencia de
Fornberg construye los pesos progresivamente y admite:

- cualquier orden de derivada;
- cualquier cantidad suficiente de nodos;
- nodos uniformes o irregulares;
- aritmética normal o precisión arbitraria.

== Derivadas mixtas como producto tensorial

Si `wx` contiene pesos para $x$ y `wy` contiene pesos para $y$, entonces:

$
  D_x^i D_y^j f approx sum_p sum_q "wx"_p "wy"_q f(x_p,y_q)
$

Es como poner una regla horizontal encima de una regla vertical. El programa
guarda las alturas de toda la cuadrícula y las reutiliza para las distintas
derivadas.

#figure(
  image("assets/06_plantilla_mixta.png", width: 70%),
  caption: [
    *Una plantilla para $f_(x y)$.* Rojo significa sumar, azul restar y blanco
    peso cero. Las cuatro esquinas comparan cómo cambia la función en ambas
    direcciones a la vez.
  ],
)

= Richardson: comparar tres tamaños de paso

Supongamos que un cálculo tiene un error principal proporcional a $h^p$:

$
  A(h)=A_"real"+C h^p+"errores menores"
$

Calculamos $A(h)$ y $A(h/2)$. Como sabemos cómo cambia $h^p$, podemos cancelar
gran parte de ese error:

$
  A_"mejor" = A(h/2) + (A(h/2)-A(h))/(2^p-1)
$

El programa hace esto dos veces:

#align(center)[
  #grid(
    columns: (1fr, auto, 1fr, auto, 1fr),
    align: center + horizon,
    rect(fill: gray, radius: 6pt, inset: 10pt)[Paso $h$],
    [→],
    rect(fill: soft-blue, stroke: blue, radius: 6pt, inset: 10pt)[Paso $h/2$],
    [→],
    rect(fill: soft-green, stroke: green, radius: 6pt, inset: 10pt)[Paso $h/4$],
  )
]

Si al reducir el paso la estimación empeora, el programa conserva la etapa
anterior. Así evita perseguir pasos pequeños cuando el redondeo ya manda.

== Qué significa “incertidumbre” en la tabla

Es una estimación construida comparando refinamientos. Sirve como alarma y para
comparar términos. *No es una demostración rigurosa* del error total.

= Qué hace el código, de principio a fin

#align(center)[
  #grid(
    columns: (1fr,),
    row-gutter: 4pt,
    rect(fill: soft-blue, stroke: blue, radius: 6pt, inset: 8pt)[
      *1. Leer* una expresión como `sin(x)*cos(y)`
    ],
    [#align(center)[↓]],
    rect(fill: soft-blue, stroke: blue, radius: 6pt, inset: 8pt)[
      *2. Validar* que solo contenga matemáticas permitidas
    ],
    [#align(center)[↓]],
    rect(fill: soft-orange, stroke: orange, radius: 6pt, inset: 8pt)[
      *3. Construir Pascal* hasta la fila N
    ],
    [#align(center)[↓]],
    rect(fill: soft-orange, stroke: orange, radius: 6pt, inset: 8pt)[
      *4. Aproximar todas las parciales* según el nivel
    ],
    [#align(center)[↓]],
    rect(fill: soft-green, stroke: green, radius: 6pt, inset: 8pt)[
      *5. Ensamblar Taylor* con Pascal, derivadas y factoriales
    ],
    [#align(center)[↓]],
    rect(fill: soft-green, stroke: green, radius: 6pt, inset: 8pt)[
      *6. Evaluar dos superficies* sobre una malla
    ],
    [#align(center)[↓]],
    rect(fill: soft-red, stroke: red, radius: 6pt, inset: 8pt)[
      *7. Encontrar f − T = 0* y dibujar las intersecciones en rojo
    ],
  )
]

== Archivos principales

#table(
  columns: (52mm, 1fr),
  table.header(
    th[Archivo],
    th[Responsabilidad],
  ),
  [`src/taylor_fd/core.py`], [Pascal, Fornberg, los tres niveles y el modelo.],
  [`src/taylor_fd/expressions.py`], [Intérprete restringido de funciones.],
  [`src/taylor_fd/plotting.py`], [Mallas, métricas, superficies e intersecciones.],
  [`src/taylor_fd/cli.py`], [Argumentos y mensajes en español.],
  [`tests/`], [Pruebas matemáticas, seguridad e integración.],
)

= Cómo se encuentra una intersección

Las superficies se intersectan cuando tienen la misma altura:

$
  f(x,y)=T_N(x,y)
$

Movemos todo a un lado:

$
  d(x,y)=f(x,y)-T_N(x,y)
$

Entonces buscamos lugares donde $d(x,y)=0$.

== Del mapa 2D a la curva 3D

1. Evaluamos $d$ en una cuadrícula de puntos $(x,y)$.
2. Un algoritmo de contornos conecta los lugares donde el signo cambia.
3. Así obtenemos curvas en el plano $(x,y)$.
4. Calculamos $z=f(x,y)$ sobre cada curva.
5. Dibujamos esas coordenadas $(x,y,z)$ en rojo.

#idea[Detalle importante][
  La línea roja no se dibuja pegada al suelo como una sombra. Se eleva hasta la
  altura común de las dos superficies; por eso representa una intersección 3D.
]

#figure(
  image("assets/09_intersecciones.png", width: 100%),
  caption: [
    *Salida real del programa.* Izquierda: original. Centro: Taylor. Derecha:
    ambas superficies transparentes; la línea roja vive a la altura común y
    marca dónde se intersectan.
  ],
)

== Las métricas

En la misma malla se calcula el error $e=f-T$.

$
  "RMSE" = sqrt(frac(1,M) sum_(k=1)^M e_k^2)
$

- *RMSE:* tamaño típico del error, dando más peso a errores grandes.
- *Error máximo:* el peor punto observado en la malla.

Estas métricas dependen del rango y de la resolución elegidos.

= Qué significa “cualquier función”

La API de Python acepta cualquier objeto invocable `f(x, y)` que devuelva un
número y funcione en los puntos de la plantilla.

La terminal acepta expresiones con:

#rect(width: 100%, fill: gray, radius: 6pt, inset: 10pt)[
  Variables: `x`, `y`

  Constantes: `pi`, `e`

  Operadores: `+ - * / **`

  Funciones: `sin cos tan asin acos atan sinh cosh tanh exp log sqrt abs`
]

== Seguridad del intérprete

El texto no pasa directamente a `eval`. Se convierte en un árbol de sintaxis y
solo se aceptan nodos matemáticos de una lista explícita. Se rechazan atributos,
imports, archivos, llamadas desconocidas y variables distintas de $x$ e $y$.

== Requisitos matemáticos reales

Para pedir orden $N$, la función debe tener las derivadas correspondientes en
la vecindad usada. Ejemplos problemáticos:

- `abs(x)` en $x=0$: tiene una esquina.
- `log(x)` alrededor de un centro cuya plantilla toca $x<=0$.
- `1/x` alrededor de $x=0$.
- una función con saltos.

#warning[El dominio también incluye los pasitos][
  No basta con que la función exista exactamente en el centro. Debe existir en
  todos los puntos cercanos que use la plantilla finita.
]

= Uso del programa con uv

== Instalación reproducible

```bash
uv sync
```

`uv.lock` fija las versiones resueltas para que distintas computadoras instalen
el mismo conjunto de dependencias.

== Ejemplo recomendado

```bash
uv run taylor \
  --funcion "sin(x)*cos(y)" \
  --centro 0 0 \
  -N 6 \
  --nivel advanced
```

== Ejemplo hero

```bash
uv run taylor \
  --funcion "sin(x*y)*exp(x-y)" \
  --centro 0.1 0.2 \
  -N 10 \
  --nivel hero \
  --digitos 120 \
  --precision-plantilla 8
```

== Servidor sin pantalla

```bash
uv run taylor --no-mostrar --salida mi_grafica.png
```

== Argumentos más importantes

#table(
  columns: (48mm, 1fr),
  table.header(
    th[Opción],
    th[Significado],
  ),
  [`--funcion`], [Expresión de $f(x,y)$.],
  [`--orden` o `-N`], [Mayor orden total de Taylor.],
  [`--nivel`], [`beginner`, `advanced` o `hero`.],
  [`--centro A B`], [Punto de expansión.],
  [`--paso h`], [Paso común; también admite `hx hy`.],
  [`--digitos`], [Precisión decimal interna de `hero`.],
  [`--rango-x`, `--rango-y`], [Ventana mostrada.],
  [`--puntos`], [Resolución por eje de la gráfica.],
)

= Cómo elegir N, h y el rango

No existe un único valor perfecto para todas las funciones.

== Elección práctica de N

- Empieza con $N=3$ o $N=4$.
- Aumenta gradualmente y observa las métricas cerca del centro.
- Si las derivadas altas se vuelven absurdas en `advanced`, usa `hero`.
- Más términos no garantizan una mejor aproximación en un rango enorme.

== Elección práctica de h

- El valor predeterminado avanzado es $0.1$ y se refina internamente.
- Si la función cambia en escalas minúsculas, prueba un paso menor.
- Si la función cambia muy lentamente o el centro es enorme, prueba un paso
  proporcional a esa escala.
- Mira la columna de incertidumbre.

== Elección práctica del rango

Empieza viendo una caja pequeña alrededor del centro. Después amplíala. Esto
separa dos preguntas:

1. ¿Las derivadas están bien calculadas?
2. ¿Hasta dónde es buena esta aproximación local?

= Tests: cómo sabemos que funciona

La suite no compara solamente capturas de pantalla. Comprueba propiedades
matemáticas con respuestas conocidas.

== Pruebas unitarias

- Pascal produce la fila `1 5 10 10 5 1` para $N=5$.
- Fornberg produce $(-1/2,0,1/2)$ para la primera derivada centrada.
- Fornberg produce $(1,-2,1)$ para la segunda derivada centrada.
- Los tres niveles reconstruyen un polinomio conocido dentro de su precisión.
- Las derivadas mixtas de $e^x sin(y)$ coinciden con sus valores exactos.
- `hero` conserva derivadas mixtas de orden alto de $e^(x+y)$.

== Pruebas de seguridad

El parser rechaza intentos de importar módulos, abrir archivos, acceder a
atributos o usar símbolos desconocidos.

== Pruebas de integración

- La CLI completa construye un modelo y guarda un PNG válido.
- La visualización devuelve métricas finitas.
- El fuente Typst se compila y el PDF generado comienza con una cabecera PDF
  válida.
- La CI ejecuta Ruff, formato, Pytest y compilación de esta guía.

== Comandos de calidad

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
typst compile docs/guia_eli5.typ docs/guia_eli5.pdf
```

#checkpoint[
  Una prueba no demuestra que toda función imaginable funcionará, pero cada
  propiedad conocida protege una pieza crítica del algoritmo.
]

= Cuaderno de ejercicios: de cero a hero

Esta ruta está diseñada para hacerse en orden. No mires las soluciones hasta
haber escrito o dicho en voz alta un intento. Equivocarse aquí es parte del
método.

#idea[Cómo estudiar con estos ejercicios][
  1. Responde sin computadora. 2. Marca lo que no entiendas. 3. Usa la pista si
  pasan cinco minutos. 4. Comprueba la solución. 5. Explica la respuesta con tus
  propias palabras. Si puedes explicarla, ya no la estás memorizando.
]

== Nivel 0 — Intuición, sin fórmulas

=== Ejercicio 0.1 · El mapa y la altura

Una función recibe $(x,y)$ y devuelve $f(x,y)$. En la analogía de la montaña,
¿qué representa cada una de esas tres cosas?

_Pista:_ dos indican dónde estás y una indica qué tan arriba estás.

=== Ejercicio 0.2 · La lupa

Taylor copia muy bien una región pequeña alrededor de $(a,b)$. Si quieres
estudiar la superficie cerca de $(10,-3)$, ¿qué centro elegirías? ¿Por qué no
usar automáticamente $(0,0)$?

=== Ejercicio 0.3 · Dos caminos

En una superficie puedes caminar hacia $x$ o hacia $y$. Si la altura aumenta al
caminar hacia $x$ y no cambia al caminar hacia $y$, ¿qué derivada primera parece
positiva y cuál parece cero?

=== Ejercicio 0.4 · Copia local

Una aproximación coincide muy bien con la función en el centro, pero se separa
en los bordes de una gráfica enorme. ¿Es suficiente para declarar que el código
está mal? Propón una comprobación mejor.

=== Ejercicio 0.5 · Detecta la función problemática

¿Cuál es más amigable para un Taylor alrededor de $(0,0)$ y por qué?

1. $f(x,y)=x^2+y^2$
2. $f(x,y)=abs(x)+y^2$

_Pista:_ imagina la forma de `abs(x)` justo en cero.

== Nivel 1 — Pascal y cambios pequeños

=== Ejercicio 1.1 · Construye Pascal

Sin consultar la guía, escribe las filas 0 a 5 del triángulo de Pascal. Recuerda
que los extremos son 1 y cada interior suma dos vecinos de arriba.

=== Ejercicio 1.2 · Repartir cuatro derivadas

Escribe todas las derivadas parciales de orden total 4, desde “todo en $x$”
hasta “todo en $y$”. Después coloca debajo los números de la fila 4 de Pascal.

=== Ejercicio 1.3 · Una pendiente con datos

Sabemos que $f(2)=7$ y $f(2.1)=7.42$. Usa una diferencia progresiva con $h=0.1$
para estimar $f'(2)$.

=== Ejercicio 1.4 · Diferencia centrada

Sabemos que $f(1.9)=3.61$ y $f(2.1)=4.41$. Estima $f'(2)$ con:

$
  (f(2+h)-f(2-h))/(2h)
$

¿Reconoces una función sencilla compatible con esos valores?

=== Ejercicio 1.5 · El paso imposible

Explica por qué estas dos frases son falsas:

- “Un $h$ gigantesco siempre es mejor porque evita redondeo”.
- “Un $h$ tan pequeño como sea posible siempre es mejor”.

== Nivel 2 — Construir Taylor con las manos

=== Ejercicio 2.1 · Contar términos

¿Cuántos términos tiene un Taylor bivariado total hasta $N=3$? Usa la fórmula
$(N+1)(N+2)/2$ y comprueba contando por órdenes.

=== Ejercicio 2.2 · Una función lineal

Para $f(x,y)=3+2x-y$, centro $(0,0)$ y $N=1$:

1. calcula $f(0,0)$, $f_x$ y $f_y$;
2. construye $T_1(x,y)$;
3. explica por qué coincide en todas partes.

=== Ejercicio 2.3 · Un tazón desplazado

Para $f(x,y)=x^2+y^2$, centro $(1,1)$ y $N=2$, calcula:

$
  f(1,1), f_x(1,1), f_y(1,1), f_(x x), f_(x y), f_(y y)
$

Luego escribe el Taylor usando $Delta x=x-1$ y $Delta y=y-1$.

=== Ejercicio 2.4 · Usa Pascal de verdad

En el término de orden 3, ¿qué multiplicadores de Pascal acompañan a
$f_(x x x)$, $f_(x x y)$, $f_(x y y)$ y $f_(y y y)$? ¿Por qué todos se dividen
entre $3!$?

=== Ejercicio 2.5 · Evalúa una aproximación

Supón que alrededor de $(0,0)$ obtuviste:

$
  T_2(x,y)=1+2x-3y+frac(1,2) x^2+4x y-y^2
$

Calcula $T_2(0.1,-0.2)$ paso a paso.

== Nivel 3 — Usar y comprobar el programa

=== Ejercicio 3.1 · Primera ejecución

Ejecuta:

```bash
uv run taylor \
  --funcion "x**2 + 2*x*y + 3*y**2" \
  -N 2 \
  --nivel advanced \
  --rango-x -1 1 \
  --rango-y -1 1 \
  --no-mostrar \
  --salida ejercicio_3_1.png
```

Predice el RMSE antes de mirar la terminal. Después explica cualquier pequeña
diferencia respecto de cero.

=== Ejercicio 3.2 · Tres niveles

Ejecuta la misma función `exp(x-y)` con $N=4$ y los niveles `beginner`,
`advanced` y `hero`. Conserva el mismo centro y rango. Anota:

- RMSE;
- error máximo;
- incertidumbre de dos derivadas;
- tiempo aproximado.

¿Qué nivel elegirías para una demostración? ¿Y para un cálculo?

=== Ejercicio 3.3 · Cambiar el centro

Aproxima `sin(x)*cos(y)` primero alrededor de $(0,0)$ y luego alrededor de
$(1,1)$. Mantén el rango cerca de $(1,1)$. ¿Cuál modelo funciona mejor allí?
Explica sin decir solamente “porque el número fue menor”.

=== Ejercicio 3.4 · Local contra global

Con función `exp(-(x**2+y**2))`, centro $(0,0)$ y $N=6$, compara los rangos:

- $[-0.5,0.5]$ en ambos ejes;
- $[-2,2]$ en ambos ejes.

¿Cambiaron las derivadas? ¿Cambió el error sobre la malla? ¿Por qué?

=== Ejercicio 3.5 · Seguridad

Prueba la expresión siguiente y lee el error:

```bash
uv run taylor --funcion "__import__('os').system('echo NO')"
```

Explica por qué rechazarla es una característica, no una limitación matemática.

== Nivel 4 — Diagnóstico hero

=== Ejercicio 4.1 · Derivadas que conocemos

Para $f(x,y)=e^(x+y)$, toda derivada parcial en $(0,0)$ vale 1. Ejecuta con
$N=10$ en `advanced` y `hero`. Busca en la tabla las derivadas $(5,5)$, $(9,1)$
y $(0,10)$. ¿Cuál nivel conserva mejor el valor esperado?

=== Ejercicio 4.2 · Más pequeño no siempre gana

En `advanced`, prueba manualmente `--paso 0.5`, `--paso 0.1`, `--paso 0.001` y
`--paso 0.000001` para una derivada de orden alto. Describe la forma general del
error. ¿Dónde domina truncamiento y dónde redondeo?

=== Ejercicio 4.3 · Suavidad

Compara `sqrt(x**2+y**2)` alrededor de $(0,0)$ y alrededor de $(1,1)$. ¿Por qué
el mismo código puede comportarse de manera muy distinta?

=== Ejercicio 4.4 · Diseña un experimento justo

Quieres comparar `advanced` y `hero`. Escribe un protocolo que mantenga fijos
función, centro, $N$, paso, precisión de plantilla, rango y resolución. Indica
qué métricas registrarías y qué conclusión *no* podrías sacar de una sola
función.

=== Ejercicio 4.5 · Explica todo en 60 segundos

Sin mirar la guía, explica a otra persona estas seis palabras y conéctalas en
una historia: *centro, derivada, diferencia finita, Pascal, Taylor,
intersección*. Si falta una conexión, vuelve al capítulo correspondiente.

= Soluciones razonadas de los ejercicios

No basta con comparar el resultado final: revisa el camino.

== Soluciones del nivel 0

=== Solución 0.1

$x$ es la posición este–oeste, $y$ la posición norte–sur y $f(x,y)$ la altura.
Las dos entradas localizan un punto del mapa; la salida levanta ese punto a 3D.

=== Solución 0.2

Elegiríamos $(a,b)=(10,-3)$. Taylor usa información local del centro. El origen
podría estar lejos de la zona relevante, así que sus potencias describirían bien
otra vecindad.

=== Solución 0.3

$f_x$ parece positiva y $f_y$ parece cero. “Mantener la otra variable quieta”
es esencial al interpretar una derivada parcial.

=== Solución 0.4

No. Primero hay que reducir el rango alrededor del centro y comprobar derivadas
contra una función conocida. Taylor es local; el borde lejano prueba alcance,
no solamente corrección numérica.

=== Solución 0.5

$x^2+y^2$ es suave en el origen. `abs(x)` tiene una esquina allí: sus pendientes
izquierda y derecha no coinciden, así que no existe la derivada clásica en $x$.

== Soluciones del nivel 1

=== Solución 1.1

```text
1
1 1
1 2 1
1 3 3 1
1 4 6 4 1
1 5 10 10 5 1
```

=== Solución 1.2

$f_(x x x x)$, $f_(x x x y)$, $f_(x x y y)$, $f_(x y y y)$ y $f_(y y y y)$.
Debajo van $1,4,6,4,1$.

=== Solución 1.3

$
  f'(2) approx (7.42-7)/0.1=4.2
$

Es una estimación, no necesariamente el valor exacto.

=== Solución 1.4

$
  f'(2) approx (4.41-3.61)/0.2=4
$

Los datos son compatibles con $f(x)=x^2$, cuya derivada exacta en 2 es 4.

=== Solución 1.5

Con $h$ grande, la secante observa una región demasiado amplia: domina el error
de truncamiento. Con $h$ microscópico se restan valores casi iguales y se
amplifica el redondeo al dividir entre $h$. Buscamos equilibrio.

== Soluciones del nivel 2

=== Solución 2.1

$(3+1)(3+2)/2=10$. Por órdenes contamos $1+2+3+4=10$.

=== Solución 2.2

$f(0,0)=3$, $f_x=2$, $f_y=-1$. Por tanto $T_1=3+2x-y$. Coincide globalmente
porque la función original ya era un polinomio de grado 1.

=== Solución 2.3

$f(1,1)=2$, $f_x=2x$ da 2, $f_y=2y$ da 2, $f_(x x)=2$, $f_(x y)=0$ y
$f_(y y)=2$. Entonces:

$
  T_2=2+2 Delta x+2 Delta y+Delta x^2+Delta y^2
$

Al sustituir $Delta x=x-1$ y $Delta y=y-1$ se recupera $x^2+y^2$.

=== Solución 2.4

Los multiplicadores son $1,3,3,1$. Se dividen entre $3!=6$ porque todos
pertenecen al orden total 3; el factorial aparece en la expansión exponencial
del operador de desplazamiento y normaliza ese orden.

=== Solución 2.5

Con $x=0.1$, $y=-0.2$:

$
  1+0.2+0.6+0.005-0.08-0.04=1.685
$

El término $4 x y$ es negativo porque $x$ e $y$ tienen signos opuestos.

== Soluciones del nivel 3

=== Solución 3.1

Debe ser cero salvo ruido de punto flotante, porque un Taylor de orden 2
reconstruye exactamente ese polinomio cuadrático. Un resultado alrededor de
$10^(-14)$ o menor es numéricamente cero en `float64`.

=== Solución 3.2

Los números exactos dependen de plataforma y rango. La conclusión esperada es:
`beginner` muestra con claridad el procedimiento pero tiene mayor error;
`advanced` ofrece el mejor equilibrio; `hero` protege órdenes altos a cambio de
tiempo. La incertidumbre de `beginner` aparece como “—” porque no refina pasos.

=== Solución 3.3

El modelo centrado en $(1,1)$ debería funcionar mejor en una vecindad de
$(1,1)$ porque sus derivadas y distancias se organizan localmente allí. El
centrado en cero intenta extender una descripción creada en otra zona.

=== Solución 3.4

Las derivadas del modelo no cambian: función, centro y parámetros numéricos son
los mismos. Sí cambia el error medido porque la segunda malla incluye puntos más
lejanos, donde los términos omitidos de Taylor pesan más.

=== Solución 3.5

El parser debe rechazarla antes de ejecutar nada. La CLI promete matemáticas,
no acceso al sistema operativo. Limitar la sintaxis mantiene esa frontera.

== Soluciones del nivel 4

=== Solución 4.1

El valor teórico de las tres derivadas es 1. En orden 10, `float64` suele perder
exactitud por cancelación, mientras `hero` conserva muchos más dígitos gracias a
la precisión arbitraria. El resultado concreto depende de paso y plantilla.

=== Solución 4.2

La curva de error suele bajar y luego subir: con pasos grandes domina
truncamiento; en una zona intermedia hay equilibrio; con pasos extremadamente
pequeños domina redondeo/cancelación. Richardson automatiza parte de esta
comparación usando tres escalas.

=== Solución 4.3

$sqrt(x^2+y^2)$ es la distancia al origen y forma un cono con punta en $(0,0)$.
Allí no es diferenciable de la manera requerida. Alrededor de $(1,1)$ la
superficie es suave y las diferencias finitas tienen una vecindad regular.

=== Solución 4.4

El protocolo debe cambiar solamente el nivel, registrar derivadas conocidas,
incertidumbre, RMSE, error máximo y tiempo, y repetir para evitar ruido de
medición. Una función sola no demuestra superioridad universal: escalas,
suavidad, coste y orden cambian el problema.

=== Solución 4.5

Una respuesta posible: “Elegimos un *centro*. Medimos allí los cambios o
*derivadas* con pequeños muestreos llamados *diferencias finitas*. El triángulo
de *Pascal* reparte cada orden entre $x$ e $y$. Con todo armamos el polinomio de
*Taylor*. Finalmente buscamos dónde original y copia tienen la misma altura;
esas son sus *intersecciones*”.

= Preguntas frecuentes

== ¿SymPy calcula las derivadas?

No. SymPy ayuda a representar la expresión y crear evaluadores para NumPy o
mpmath. Las derivadas del modelo se calculan mediante diferencias finitas.

== ¿Pascal calcula las derivadas en todos los niveles?

En `beginner`, sí participa directamente en sus pesos. En `advanced` y `hero`,
los pesos se generan con Fornberg. En *todos* los niveles Pascal entrega los
coeficientes binomiales que ensamblan Taylor.

== ¿Por qué mi error crece lejos del centro?

Porque Taylor es local. Prueba un rango menor o mueve el centro hacia la región
que te interesa.

== ¿Por qué aumentar N empeoró el resultado?

Las derivadas altas son sensibles al redondeo y al paso. Prueba `hero`, más
dígitos, otra precisión de plantilla o un rango menor. También verifica que la
función sea suave.

== ¿Una línea roja significa infinitos puntos de igualdad?

Sí: cada curva aproximada reúne muchos puntos donde las dos alturas coinciden.
La precisión geométrica está limitada por la resolución de la malla.

== ¿Puedo usar una función escrita directamente en Python?

Sí:

```python
from taylor_fd import build_taylor_model

def mi_funcion(x, y):
    return x**2 * y + y**3

modelo = build_taylor_model(
    mi_funcion,
    center=(0.0, 0.0),
    order=3,
    level="advanced",
)

print(modelo.evaluate(0.2, 0.4))
```

= Glosario de bolsillo

#word[Callable][Algo que puede llamarse como `f(x, y)`.]

#word[Centro][Punto $(a,b)$ alrededor del cual copiamos la función.]

#word[Coeficiente][Número que multiplica una pieza del polinomio.]

#word[Derivada][Medida local de cambio.]

#word[Derivada mixta][Cambio que involucra tanto $x$ como $y$.]

#word[Diferencia finita][Estimación de una derivada usando valores cercanos.]

#word[Error de redondeo][Pérdida causada por representar números con dígitos finitos.]

#word[Error de truncamiento][Error causado por aproximar un proceso infinito con pasos o términos finitos.]

#word[Extrapolación de Richardson][Combinación de resultados con distintos pasos para cancelar el error principal.]

#word[Fornberg][Recurrencia estable para generar pesos de diferencias finitas.]

#word[Orden N][Mayor cantidad total de derivaciones o potencias incluida.]

#word[Pascal][Triángulo que contiene los coeficientes binomiales.]

#word[Plantilla o stencil][Conjunto de puntos vecinos usados por una diferencia finita.]

#word[Polinomio][Suma de potencias sencillas de las variables.]

#word[Precisión arbitraria][Uso de tantos dígitos internos como se soliciten.]

#word[Taylor][Polinomio que reproduce información local de una función.]

= La receta final en diez líneas

#rect(width: 100%, fill: soft-blue, stroke: blue, radius: 8pt, inset: 14pt)[
  + Elige una función suave $f(x,y)$.
  + Elige un centro $(a,b)$.
  + Elige el orden total $N$.
  + Construye Pascal hasta la fila $N$.
  + Evalúa la función en puntos vecinos.
  + Convierte esas evaluaciones en derivadas finitas.
  + Usa Pascal, factoriales y derivadas para armar $T_N$.
  + Evalúa $f$ y $T_N$ en una malla.
  + Busca el contorno $f-T_N=0$.
  + Dibuja y comprueba el error, recordando que Taylor es local.
]

#v(8mm)
#align(center)[
  #text(size: 16pt, weight: "bold", fill: dark-blue)[
    Si entendiste esta receta, entendiste el proyecto.
  ]
]

= Referencias y siguiente paso

- B. Fornberg, _Generation of Finite Difference Formulas on Arbitrarily
  Spaced Grids_, Mathematics of Computation 51 (1988), 699–706.
  DOI: #link("https://doi.org/10.1090/S0025-5718-1988-0935077-0")[10.1090/S0025-5718-1988-0935077-0].

- Documentación oficial de `mpmath`, sección de diferenciación numérica:
  #link("https://mpmath.org/doc/current/mpmath.pdf")[mpmath.org/doc/current/mpmath.pdf].

- Documentación del proyecto y ejemplos de ejecución:
  #link("https://github.com/Sekinal/taylor")[github.com/Sekinal/taylor].

#idea[Siguiente experimento sugerido][
  Ejecuta la misma función con los tres niveles, primero en un rango pequeño y
  luego en uno grande. Compara derivadas, incertidumbres, RMSE e intersecciones.
  Ver las diferencias convierte todas estas fórmulas en intuición.
]
