"""
app.py
------
Interfaz y flujo del juego "Aventura de Segmentación".

El juego recorre el pipeline de clustering como una serie de niveles. En cada
nivel el jugador:
  1) lee la teoria (que es, para que sirve, como, consecuencias),
  2) toma una DECISION entre varias acciones posibles,
  3) ve VISUALMENTE el efecto sobre un dataset pequeño,
  4) recibe retroalimentacion y PUNTOS segun lo acertado de su decision.

Al final se registra su puntuacion en un ranking global para competir.
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from nicegui import app, ui

from juego import contenido, marcador, motor

PASOS = ["datos", "duplicados", "outliers", "escalamiento",
         "variables", "k", "kmeans", "jerarquico", "perfilado"]

PALETA = ["#1976d2", "#e53935", "#43a047", "#fb8c00", "#8e24aa", "#00897b"]


# --------------------------------------------------------------------- estado
def estado() -> dict:
    """Estado del juego para esta pestaña del navegador."""
    return app.storage.tab.setdefault("juego", {
        "fase": "inicio",
        "nombre": "",
        "puntos": 0,
        "paso": 0,
        "datos": motor.dataset_ejemplo(),
        "features": list(motor.COLUMNAS),
        "scaler": "standard",
        "k": 3,
        "labels_km": None,
        "labels_jq": None,
        "registrado": False,
        "historial": [],   # [(titulo, puntos_ganados, comentario)]
    })


def reset() -> None:
    app.storage.tab["juego"] = None
    estado()  # recrea limpio


# --------------------------------------------------------------------- helpers UI
def _tarjeta_teoria(clave: str) -> None:
    t = contenido.TEORIA[clave]
    with ui.card().classes("w-full bg-blue-50"):
        ui.label(t["titulo"]).classes("text-xl font-bold text-blue-900")
        with ui.column().classes("gap-1"):
            ui.markdown(f"**¿Qué es?** {t['que_es']}")
            ui.markdown(f"**¿Para qué sirve?** {t['para_que']}")
            ui.markdown(f"**¿Cómo se hace?** {t['como']}")
            ui.markdown(f"⚠️ **Consecuencias:** {t['consecuencias']}")


def _barra_progreso() -> None:
    e = estado()
    with ui.row().classes("items-center justify-between w-full"):
        ui.label(f"👤 {e['nombre']}").classes("font-semibold")
        idx = e["paso"]
        ui.label(f"Nivel {idx + 1} de {len(PASOS)}").classes("text-sm text-gray-600")
        ui.label(f"⭐ {e['puntos']} pts").classes("font-bold text-amber-700")
    ui.linear_progress((e["paso"]) / len(PASOS), show_value=False).classes("w-full")


def _scatter(datos: dict, x: str, y: str, labels=None, titulo="", resaltar=None):
    """Dispersion de dos variables, opcionalmente coloreada por cluster."""
    fig = go.Figure()
    xs = np.asarray(datos[x], dtype=float)
    ys = np.asarray(datos[y], dtype=float)
    if labels is None:
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers",
            marker=dict(size=10, color="#1976d2", opacity=0.75),
            name="clientes"))
    else:
        labels = np.asarray(labels)
        for ci, c in enumerate(np.unique(labels)):
            m = labels == c
            fig.add_trace(go.Scatter(
                x=xs[m], y=ys[m], mode="markers",
                marker=dict(size=10, color=PALETA[ci % len(PALETA)], opacity=0.85),
                name=f"Grupo {c}"))
    if resaltar is not None:
        resaltar = np.asarray(resaltar)
        fig.add_trace(go.Scatter(
            x=xs[resaltar], y=ys[resaltar], mode="markers",
            marker=dict(size=16, color="rgba(0,0,0,0)",
                        line=dict(color="red", width=3)),
            name="atípicos"))
    fig.update_layout(title=titulo, xaxis_title=x, yaxis_title=y,
                      height=380, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def _sumar(titulo: str, puntos: int, comentario: str) -> None:
    e = estado()
    e["puntos"] += puntos
    e["historial"].append((titulo, puntos, comentario))


def _feedback(puntos: int, comentario: str) -> None:
    color = "positive" if puntos >= 0 else "warning"
    ui.notify(f"{'+' if puntos>=0 else ''}{puntos} pts — {comentario}",
              type=color, timeout=4000)


# --------------------------------------------------------------------- pasos
def paso_datos(vista):
    e = estado()
    _tarjeta_teoria("datos")
    n = len(e["datos"][motor.COLUMNAS[0]])
    ui.label(f"Tu dataset tiene {n} clientes y {len(motor.COLUMNAS)} variables.").classes(
        "font-semibold mt-2")
    ui.plotly(_scatter(e["datos"], "IngresoAnual_k", "PuntajeGasto",
                       titulo="Clientes: Ingreso vs Puntaje de gasto")).classes("w-full")
    ui.label("👀 ¿Alcanzas a intuir grupos a simple vista? Avancemos a limpiarlos.").classes(
        "text-sm text-gray-600")

    def continuar():
        _sumar("Exploración", 50, "Conociste tus datos.")
        _feedback(50, "Buen inicio: conocer los datos es el primer paso.")
        _avanzar(vista)

    ui.button("Entendido, continuar", on_click=continuar).props("color=primary")


def paso_duplicados(vista):
    e = estado()
    _tarjeta_teoria("duplicados")
    n_dup = motor.contar_duplicados(e["datos"])
    ui.label(f"🔎 Se detectaron {n_dup} registros duplicados.").classes(
        "font-semibold mt-2 text-red-700")

    def eliminar():
        e["datos"] = motor.quitar_duplicados(e["datos"])
        _sumar("Duplicados", 100, "Eliminaste duplicados (decisión correcta).")
        _feedback(100, "Correcto: cada cliente debe contar una sola vez.")
        _avanzar(vista)

    def dejar():
        _sumar("Duplicados", 20, "Dejaste los duplicados (sesga los grupos).")
        _feedback(20, "Los duplicados sesgarán los centros de los clusters.")
        _avanzar(vista)

    with ui.row().classes("gap-3 mt-2"):
        ui.button("Eliminar duplicados", on_click=eliminar).props("color=primary")
        ui.button("Dejarlos así", on_click=dejar).props("flat color=grey")


def paso_outliers(vista):
    e = estado()
    _tarjeta_teoria("outliers")
    mask = motor.detectar_outliers_iqr(e["datos"], motor.COLUMNAS)
    n_out = int(mask.sum())
    ui.label(f"🔎 El método IQR detectó {n_out} outliers (marcados en rojo).").classes(
        "font-semibold mt-2 text-red-700")
    ui.plotly(_scatter(e["datos"], "IngresoAnual_k", "PuntajeGasto",
                       titulo="Outliers detectados", resaltar=mask)).classes("w-full")

    def eliminar():
        e["datos"] = motor.quitar_filas(e["datos"], mask)
        _sumar("Outliers", 100, "Quitaste los atípicos extremos.")
        _feedback(100, "Bien: estos atípicos eran extremos y distorsionan K-Means.")
        _avanzar(vista)

    def conservar():
        _sumar("Outliers", 40, "Conservaste los outliers.")
        _feedback(40, "Válido a veces, pero aquí jalarán los centros de los grupos.")
        _avanzar(vista)

    with ui.row().classes("gap-3 mt-2"):
        ui.button("Eliminar outliers", on_click=eliminar).props("color=primary")
        ui.button("Conservarlos", on_click=conservar).props("flat color=grey")


def paso_escalamiento(vista):
    e = estado()
    _tarjeta_teoria("escalamiento")
    eleccion = {"v": "standard"}
    ui.radio({"standard": "StandardScaler", "minmax": "MinMaxScaler",
              "ninguno": "No escalar"}, value="standard",
             on_change=lambda ev: eleccion.update(v=ev.value)).props("inline")

    cont = ui.column().classes("w-full")

    def previsualizar():
        cont.clear()
        X = motor.a_matriz(e["datos"], motor.COLUMNAS)
        Xs = motor.escalar(X, eleccion["v"])
        datos_s = {c: Xs[:, i].tolist() for i, c in enumerate(motor.COLUMNAS)}
        with cont:
            ui.plotly(_scatter(datos_s, "IngresoAnual_k", "PuntajeGasto",
                               titulo=f"Datos tras '{eleccion['v']}'")).classes("w-full")

    ui.button("Previsualizar efecto", on_click=previsualizar).props("flat")

    def aplicar():
        e["scaler"] = eleccion["v"]
        if eleccion["v"] in ("standard", "minmax"):
            _sumar("Escalamiento", 100, f"Escalaste con {eleccion['v']}.")
            _feedback(100, "Correcto: K-Means necesita variables en escala comparable.")
        else:
            _sumar("Escalamiento", 20, "No escalaste (el ingreso dominará).")
            _feedback(20, "Sin escalar, el Ingreso domina por tener números más grandes.")
        _avanzar(vista)

    ui.button("Aplicar y continuar", on_click=aplicar).props("color=primary")


def paso_variables(vista):
    e = estado()
    _tarjeta_teoria("variables")
    sel = ui.select(motor.COLUMNAS, value=list(motor.COLUMNAS), multiple=True,
                    label="Variables para segmentar").props("use-chips").classes("w-full")

    def aplicar():
        feats = list(sel.value) if sel.value else []
        if len(feats) < 2:
            ui.notify("Elige al menos 2 variables.", type="warning")
            return
        e["features"] = feats
        if len(feats) >= 3:
            _sumar("Variables", 100, "Usaste todas las variables informativas.")
            _feedback(100, "Buena elección: las 3 aportan información de negocio.")
        else:
            _sumar("Variables", 60, "Usaste 2 variables.")
            _feedback(60, "Funciona, pero podrías perder matices de un tercer eje.")
        _avanzar(vista)

    ui.button("Confirmar variables", on_click=aplicar).props("color=primary")


def paso_k(vista):
    e = estado()
    _tarjeta_teoria("k")
    X = motor.escalar(motor.a_matriz(e["datos"], e["features"]), e["scaler"])
    ks = list(range(2, 8))
    inercias, sils = motor.curva_codo(X, ks)
    k_opt = ks[int(np.argmax(sils))]

    f1 = go.Figure(go.Scatter(x=ks, y=inercias, mode="lines+markers"))
    f1.update_layout(title="Método del Codo (Inertia vs K)", xaxis_title="K",
                     yaxis_title="Inertia (WCSS)", height=320)
    f2 = go.Figure(go.Scatter(x=ks, y=sils, mode="lines+markers",
                              line=dict(color="green")))
    f2.update_layout(title="Silhouette vs K", xaxis_title="K",
                     yaxis_title="Silhouette", height=320)
    with ui.row().classes("w-full"):
        ui.plotly(f1).classes("w-1/2")
        ui.plotly(f2).classes("w-1/2")

    ui.label("Elige el K que creas mejor según el codo y el Silhouette:").classes(
        "font-semibold mt-2")
    knum = ui.number("K", value=3, min=2, max=7).classes("w-28")

    def confirmar():
        k = int(knum.value)
        e["k"] = k
        dif = abs(k - k_opt)
        pts = max(0, 120 - dif * 40)
        comentario = ("¡Elegiste el K óptimo según Silhouette!" if dif == 0
                      else f"El K con mejor Silhouette era {k_opt}.")
        _sumar("Elección de K", pts, comentario)
        _feedback(pts, comentario)
        _avanzar(vista)

    ui.button("Confirmar K", on_click=confirmar).props("color=primary")


def paso_kmeans(vista):
    e = estado()
    _tarjeta_teoria("kmeans")
    X = motor.escalar(motor.a_matriz(e["datos"], e["features"]), e["scaler"])
    labels, _, wcss = motor.kmeans(X, e["k"])
    e["labels_km"] = labels.tolist()
    sil = motor.silhouette(X, labels)

    ui.plotly(_scatter(e["datos"], "IngresoAnual_k", "PuntajeGasto", labels=labels,
                       titulo=f"K-Means con K={e['k']}")).classes("w-full")
    with ui.row().classes("gap-4"):
        ui.label(f"Silhouette: {sil:.3f}").classes("font-bold")
        ui.label(f"Inertia: {wcss:.1f}").classes("text-gray-600")

    def continuar():
        pts = int(max(0, sil) * 200)
        _sumar("K-Means", pts, f"Silhouette={sil:.3f}")
        _feedback(pts, f"Calidad de tus grupos (Silhouette): {sil:.3f}")
        _avanzar(vista)

    ui.button("Ver clustering jerárquico", on_click=continuar).props("color=primary")


def paso_jerarquico(vista):
    e = estado()
    _tarjeta_teoria("jerarquico")
    X = motor.escalar(motor.a_matriz(e["datos"], e["features"]), e["scaler"])
    labels = motor.aglomerativo(X, e["k"])
    e["labels_jq"] = labels.tolist()

    ui.plotly(_scatter(e["datos"], "IngresoAnual_k", "PuntajeGasto", labels=labels,
                       titulo=f"Jerárquico (aglomerativo) con K={e['k']}")).classes("w-full")

    # Concordancia con K-Means (cuantos clientes caen en el mismo grupo relativo)
    km = np.asarray(e["labels_km"])
    jq = labels
    # comparamos via "misma pareja agrupada" (ARI simplificado: % de pares coherentes)
    n = len(km)
    pares = mismos = 0
    for i in range(n):
        for j in range(i + 1, n):
            pares += 1
            if (km[i] == km[j]) == (jq[i] == jq[j]):
                mismos += 1
    concordancia = mismos / pares if pares else 0

    ui.label(f"Concordancia con K-Means: {concordancia*100:.0f}%").classes(
        "font-bold mt-2")
    ui.label("Si ambos métodos coinciden mucho, hay más confianza en los grupos.").classes(
        "text-sm text-gray-600")

    def continuar():
        pts = int(concordancia * 150)
        _sumar("Jerárquico", pts, f"Concordancia {concordancia*100:.0f}%")
        _feedback(pts, f"Los dos métodos concuerdan {concordancia*100:.0f}%.")
        _avanzar(vista)

    ui.button("Interpretar resultados", on_click=continuar).props("color=primary")


def paso_perfilado(vista):
    e = estado()
    _tarjeta_teoria("perfilado")
    labels = np.asarray(e["labels_km"])
    X = motor.a_matriz(e["datos"], motor.COLUMNAS)

    # Tabla de perfil: promedio por variable + tamaño
    filas = []
    for c in np.unique(labels):
        m = labels == c
        prom = X[m].mean(axis=0)
        filas.append({
            "Grupo": int(c),
            "Edad": round(prom[0], 1),
            "Ingreso_k": round(prom[1], 1),
            "Gasto": round(prom[2], 1),
            "Tamaño": int(m.sum()),
        })
    cols = [{"name": k, "label": k, "field": k} for k in filas[0].keys()]
    ui.table(columns=cols, rows=filas).classes("w-full")
    ui.label("La columna 'Tamaño' = cuántos clientes cumplen ese perfil.").classes(
        "text-sm text-gray-600")

    # Radar de perfiles (normalizado)
    Xn = motor.escalar(X, "minmax")
    radar = go.Figure()
    for ci, c in enumerate(np.unique(labels)):
        vals = Xn[labels == c].mean(axis=0).tolist()
        radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=motor.COLUMNAS + [motor.COLUMNAS[0]],
            fill="toself", name=f"Grupo {c}",
            line=dict(color=PALETA[ci % len(PALETA)])))
    radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                        title="Radar de perfiles", height=420)
    ui.plotly(radar).classes("w-full")

    # Mini-quiz de marketing
    ui.separator()
    ui.label("🎯 Reto final: ¿qué estrategia le darías al grupo que MÁS gasta?").classes(
        "font-semibold")
    grupo_gastador = int(np.unique(labels)[
        int(np.argmax([X[labels == c][:, 2].mean() for c in np.unique(labels)]))])
    ui.label(f"(Pista: ese es el Grupo {grupo_gastador})").classes("text-xs text-gray-500")

    opciones = {
        "vip": "Programa VIP / fidelización premium (correcto)",
        "descuento": "Descuentos agresivos para que compren algo",
        "ignorar": "No invertir en ellos",
    }
    elec = {"v": "vip"}
    ui.radio(opciones, value="vip",
             on_change=lambda ev: elec.update(v=ev.value)).props("inline")

    def terminar():
        if elec["v"] == "vip":
            _sumar("Estrategia", 120, "Fidelizar a quien más gasta: ¡acertado!")
            _feedback(120, "Correcto: a los que más gastan, cuídalos con un programa VIP.")
        else:
            _sumar("Estrategia", 30, "Estrategia poco óptima para ese segmento.")
            _feedback(30, "A los grandes gastadores conviene fidelizarlos, no malbaratar.")
        e["fase"] = "final"
        vista.refresh()

    ui.button("Terminar y ver mi puntuación", on_click=terminar).props("color=primary")


RENDER = {
    "datos": paso_datos, "duplicados": paso_duplicados, "outliers": paso_outliers,
    "escalamiento": paso_escalamiento, "variables": paso_variables, "k": paso_k,
    "kmeans": paso_kmeans, "jerarquico": paso_jerarquico, "perfilado": paso_perfilado,
}


def _avanzar(vista):
    e = estado()
    e["paso"] += 1
    if e["paso"] >= len(PASOS):
        e["fase"] = "final"
    vista.refresh()


# --------------------------------------------------------------------- pantallas
def pantalla_inicio(vista):
    with ui.card().classes("w-full max-w-2xl mx-auto"):
        ui.label("🧩 Aventura de Segmentación de Clientes").classes(
            "text-2xl font-bold")
        ui.markdown(
            "Recorre **todo el proceso de minería de datos para segmentar clientes** "
            "como si fuera un videojuego. En cada nivel decides qué hacer, ves el efecto "
            "en datos reales y ganas puntos por buenas decisiones.\n\n"
            "Sirve tanto si **ya sabes del tema** (para practicar y competir) como si "
            "**empiezas desde cero** (cada paso se explica con teoría)."
        )
        nombre = ui.input("Tu nombre de jugador").classes("w-full")

        def empezar():
            if not (nombre.value or "").strip():
                ui.notify("Escribe un nombre para empezar.", type="warning")
                return
            e = estado()
            e["nombre"] = nombre.value.strip()[:24]
            e["fase"] = "jugando"
            vista.refresh()

        with ui.row().classes("gap-3"):
            ui.button("¡Empezar!", on_click=empezar).props("color=primary size=lg")
            ui.button("Ver ranking", on_click=lambda: _mostrar_ranking()).props("flat")


def pantalla_final(vista):
    e = estado()
    if not e["registrado"]:
        marcador.registrar(e["nombre"], e["puntos"], {
            "k": e["k"], "scaler": e["scaler"], "features": e["features"]})
        e["registrado"] = True

    with ui.card().classes("w-full max-w-2xl mx-auto"):
        ui.label("🏁 ¡Completaste la aventura!").classes("text-2xl font-bold")
        ui.label(f"Puntuación final: {e['puntos']} pts").classes(
            "text-xl font-bold text-amber-700")
        pos = marcador.posicion(e["nombre"])
        if pos:
            ui.label(f"Estás en la posición #{pos} del ranking global.").classes(
                "font-semibold")

        ui.separator()
        ui.label("Resumen de tus decisiones:").classes("font-semibold")
        with ui.column().classes("gap-0"):
            for titulo, pts, com in e["historial"]:
                ui.markdown(f"- **{titulo}**: +{pts} pts — {com}")

        ui.separator()
        _mostrar_ranking(inline=True)

        with ui.row().classes("gap-3 mt-2"):
            def reiniciar():
                nombre = e["nombre"]
                reset()
                estado()["nombre"] = nombre
                estado()["fase"] = "inicio"
                vista.refresh()
            ui.button("Jugar de nuevo", on_click=reiniciar).props("color=primary")


def _mostrar_ranking(inline: bool = False):
    top = marcador.top(10)
    rows = [{"#": i, "Jugador": e["nombre"], "Puntos": e["puntos"], "Fecha": e["fecha"]}
            for i, e in enumerate(top, start=1)]
    cols = [{"name": k, "label": k, "field": k} for k in ["#", "Jugador", "Puntos", "Fecha"]]

    if inline:
        ui.label("🏆 Top 10 global").classes("font-bold")
        if rows:
            ui.table(columns=cols, rows=rows).classes("w-full")
        else:
            ui.label("Aún no hay puntuaciones. ¡Sé el primero!").classes("text-gray-500")
        return

    with ui.dialog() as dlg, ui.card():
        ui.label("🏆 Ranking global (Top 10)").classes("text-xl font-bold")
        if rows:
            ui.table(columns=cols, rows=rows).classes("w-full")
        else:
            ui.label("Aún no hay puntuaciones.").classes("text-gray-500")
        ui.button("Cerrar", on_click=dlg.close).props("flat")
    dlg.open()


# --------------------------------------------------------------------- pagina
def construir():
    """Construye la pagina del juego (llamar dentro de @ui.page)."""
    ui.colors(primary="#1976d2")

    @ui.refreshable
    def vista():
        e = estado()
        with ui.column().classes("w-full max-w-4xl mx-auto p-4 gap-3"):
            if e["fase"] == "inicio":
                pantalla_inicio(vista)
            elif e["fase"] == "final":
                pantalla_final(vista)
            else:
                _barra_progreso()
                RENDER[PASOS[e["paso"]]](vista)

    vista()
