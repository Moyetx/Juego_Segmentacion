"""
marcador.py
-----------
Tabla de puntuaciones GLOBAL, compartida por todos los jugadores.

Usa `app.storage.general`, que NiceGUI persiste en disco (en .nicegui/).
En Railway, si montas un volumen y apuntas ahi el almacenamiento, las
puntuaciones sobreviven a los redeploys; si no, se reinician al redesplegar
(suficiente para un juego de clase).
"""

from __future__ import annotations

from datetime import datetime

from nicegui import app

CLAVE = "ranking"
MAX_ENTRADAS = 100


def _tabla() -> list:
    return app.storage.general.setdefault(CLAVE, [])


def registrar(nombre: str, puntos: int, detalle: dict) -> None:
    """Agrega o actualiza la mejor puntuacion de un jugador."""
    nombre = (nombre or "Anónimo").strip()[:24] or "Anónimo"
    tabla = _tabla()
    # Conserva solo la MEJOR puntuacion por nombre.
    existente = next((e for e in tabla if e["nombre"].lower() == nombre.lower()), None)
    if existente and existente["puntos"] >= puntos:
        return
    if existente:
        tabla.remove(existente)
    tabla.append({
        "nombre": nombre,
        "puntos": int(puntos),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "detalle": detalle,
    })
    tabla.sort(key=lambda e: e["puntos"], reverse=True)
    del tabla[MAX_ENTRADAS:]
    app.storage.general[CLAVE] = tabla


def top(n: int = 10) -> list:
    """Devuelve las n mejores puntuaciones."""
    return _tabla()[:n]


def posicion(nombre: str) -> int | None:
    """Posicion (1-based) de un jugador en el ranking, o None."""
    nombre = (nombre or "").strip().lower()
    for i, e in enumerate(_tabla(), start=1):
        if e["nombre"].lower() == nombre:
            return i
    return None
