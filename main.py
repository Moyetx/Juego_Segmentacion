"""
main.py
-------
Punto de entrada del juego "Aventura de Segmentación de Clientes".

Ejecutar en local:
    pip install -r requirements.txt
    python main.py
Abre http://localhost:8080

Despliegue (Railway / Docker): usa el Dockerfile incluido. El puerto y el
storage_secret se leen de variables de entorno.
"""

import os

from nicegui import ui

from juego.app import construir


@ui.page("/")
async def index(client):
    await client.connected()  # necesario para usar app.storage.tab
    construir()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Aventura de Segmentación",
        storage_secret=os.environ.get("STORAGE_SECRET", "dev-secret-juego"),
        reload=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
    )
