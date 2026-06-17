"""
contenido.py
------------
Texto teorico de cada paso del juego. Separado de la logica para poder
ajustar las explicaciones sin tocar el codigo de la interfaz.

Cada paso tiene:
  - titulo
  - que_es         : definicion corta (para principiantes)
  - para_que       : por que se hace / utilidad en marketing
  - como           : como se hace tecnicamente (para quien ya sabe)
  - consecuencias  : que pasa si se hace mal / se omite
"""

TEORIA = {
    "intro": {
        "titulo": "¿Qué es la segmentación de clientes?",
        "que_es": (
            "Segmentar es dividir a los clientes en grupos donde los miembros de "
            "un mismo grupo se parecen entre sí y se diferencian de los otros grupos."
        ),
        "para_que": (
            "Permite diseñar campañas de marketing distintas para cada grupo: no es "
            "lo mismo hablarle a un cliente joven que gasta mucho que a uno mayor "
            "que ahorra. Mensajes a la medida = más ventas y menos gasto desperdiciado."
        ),
        "como": (
            "Usamos clustering NO supervisado: el algoritmo descubre los grupos solo, "
            "sin que nadie le diga de antemano las etiquetas. Recorreremos el pipeline "
            "completo: limpieza → escalamiento → selección de variables → modelo → "
            "evaluación → interpretación."
        ),
        "consecuencias": (
            "Sin segmentar, tratas a todos igual y desperdicias presupuesto en clientes "
            "a los que tu mensaje no les interesa."
        ),
    },
    "datos": {
        "titulo": "Paso 1 — Conocer los datos",
        "que_es": (
            "Explorar el dataset: qué columnas hay, qué representan y cómo se distribuyen "
            "los valores."
        ),
        "para_que": (
            "No puedes limpiar ni modelar algo que no entiendes. Conocer los datos evita "
            "errores graves más adelante (ej. usar un ID como si fuera una característica)."
        ),
        "como": (
            "Aquí cada fila es un cliente con 3 variables: Edad, Ingreso anual (en miles) "
            "y Puntaje de gasto (1–100). Observa el gráfico: ¿se intuyen grupos?"
        ),
        "consecuencias": (
            "Saltarte esta exploración te lleva a decisiones a ciegas y resultados que "
            "no sabrás interpretar."
        ),
    },
    "duplicados": {
        "titulo": "Paso 2 — Detección de registros duplicados",
        "que_es": "Filas exactamente repetidas (el mismo cliente contado dos veces).",
        "para_que": (
            "Los duplicados dan más 'peso' artificial a ciertos clientes y sesgan los "
            "grupos. Limpiarlos hace que cada cliente cuente una sola vez."
        ),
        "como": (
            "Se comparan las filas y se eliminan las repetidas (en pandas: "
            "df.drop_duplicates()). Aquí hay duplicados metidos a propósito."
        ),
        "consecuencias": (
            "Si NO los quitas, el centro de un cluster se desplaza hacia los clientes "
            "duplicados y la segmentación queda distorsionada."
        ),
    },
    "outliers": {
        "titulo": "Paso 3 — Detección de outliers (valores atípicos)",
        "que_es": "Clientes con valores extremos, muy alejados del resto.",
        "para_que": (
            "Un outlier puede ser un error de captura o un caso genuino pero raro. "
            "K-Means es MUY sensible a ellos porque usa promedios."
        ),
        "como": (
            "Método IQR: se calcula Q1, Q3 e IQR=Q3-Q1; es outlier todo lo que cae fuera "
            "de [Q1-1.5·IQR, Q3+1.5·IQR]. (Otra opción es Z-Score con |z|>3)."
        ),
        "consecuencias": (
            "Si dejas outliers, un solo cliente extremo puede 'jalar' el centro de un "
            "grupo entero. Si eliminas demasiado, pierdes información real. Hay que decidir."
        ),
    },
    "escalamiento": {
        "titulo": "Paso 4 — Escalamiento de variables",
        "que_es": "Poner todas las variables en una escala comparable.",
        "para_que": (
            "K-Means mide distancias. Si el Ingreso va de 10 a 150 y el Gasto de 1 a 100, "
            "el Ingreso domina la distancia solo por tener números más grandes."
        ),
        "como": (
            "StandardScaler: resta la media y divide por la desviación (media 0, desv 1). "
            "MinMaxScaler: lleva todo al rango [0,1]. Ambos igualan la influencia."
        ),
        "consecuencias": (
            "Sin escalar, los clusters se forman casi solo por la variable de mayor "
            "magnitud y el resto se ignora. ¡Es uno de los errores más comunes!"
        ),
    },
    "variables": {
        "titulo": "Paso 5 — Selección de variables (features)",
        "que_es": "Elegir qué columnas entran al modelo.",
        "para_que": (
            "Más variables no siempre es mejor. Variables irrelevantes o redundantes "
            "añaden ruido y dificultan encontrar grupos claros."
        ),
        "como": (
            "Se eligen las variables con sentido de negocio y poca redundancia (se revisa "
            "la correlación). Aquí decides con cuáles segmentar."
        ),
        "consecuencias": (
            "Incluir una variable sin sentido (o un ID) ensucia las distancias; quitar "
            "una clave hace que pierdas grupos reales."
        ),
    },
    "k": {
        "titulo": "Paso 6 — Elegir K (número de grupos)",
        "que_es": "Decidir en cuántos grupos dividir a los clientes.",
        "para_que": (
            "K es la decisión más importante de K-Means. Muy pocos grupos mezclan "
            "clientes distintos; demasiados los fragmentan sin sentido."
        ),
        "como": (
            "Método del codo: se grafica la inertia (WCSS) vs K y se busca el 'codo' donde "
            "deja de mejorar mucho. Silhouette Score: se elige el K con el valor más alto "
            "(rango -1 a 1)."
        ),
        "consecuencias": (
            "Un K mal elegido produce segmentos inútiles para marketing: o demasiado "
            "genéricos o imposibles de accionar."
        ),
    },
    "kmeans": {
        "titulo": "Paso 7 — K-Means",
        "que_es": "Algoritmo que agrupa minimizando la distancia de cada punto a su centro.",
        "para_que": "Es rápido y eficaz para encontrar grupos esféricos y de tamaño similar.",
        "como": (
            "1) Coloca K centros al azar. 2) Asigna cada cliente al centro más cercano. "
            "3) Recalcula cada centro como el promedio de su grupo. 4) Repite hasta que "
            "se estabiliza."
        ),
        "consecuencias": (
            "Depende de la inicialización (por eso se corre varias veces) y asume grupos "
            "redondeados; con formas raras puede fallar."
        ),
    },
    "jerarquico": {
        "titulo": "Paso 8 — Clustering Jerárquico",
        "que_es": "Construye una jerarquía de grupos uniendo lo más parecido paso a paso.",
        "para_que": (
            "No necesitas fijar K de antemano: el dendrograma muestra cómo se agrupan y "
            "tú decides dónde 'cortar'. Útil para validar lo que vio K-Means."
        ),
        "como": (
            "Aglomerativo: empieza con cada cliente como su propio grupo y fusiona los "
            "dos más cercanos repetidamente (enlace: ward, average, complete...)."
        ),
        "consecuencias": (
            "Es más costoso en cómputo para datasets grandes, pero muy interpretable. "
            "Comparar sus grupos con K-Means da confianza en el resultado."
        ),
    },
    "perfilado": {
        "titulo": "Paso 9 — Perfilado e interpretación para marketing",
        "que_es": "Traducir cada cluster (números) en un perfil de cliente accionable.",
        "para_que": (
            "Aquí es donde el análisis se vuelve dinero: a cada segmento le diseñas una "
            "estrategia. Es el objetivo final de toda la Propuesta 2."
        ),
        "como": (
            "Se calcula el promedio de cada variable por cluster y el tamaño (cuántos "
            "clientes hay). Con eso describes cada grupo y propones una acción."
        ),
        "consecuencias": (
            "Sin interpretar, tienes números sin valor de negocio. La interpretación es "
            "lo que convierte el clustering en estrategia."
        ),
    },
}
