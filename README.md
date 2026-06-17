# 🧩 Aventura de Segmentación de Clientes (juego)

Juego educativo e interactivo que recorre **todo el pipeline de minería de datos
para segmentar clientes** (la Propuesta 2) como si fuera un videojuego por niveles.

En cada nivel el jugador:
1. Lee la **teoría** (qué es, para qué sirve, cómo se hace y qué consecuencias tiene).
2. Toma una **decisión** entre varias acciones posibles.
3. Ve el **efecto visual** sobre un dataset pequeño de ejemplo.
4. Recibe **retroalimentación y puntos** según lo acertado de su decisión.

Al final, su puntuación se registra en un **ranking global** para competir con otros.

Sirve para dos públicos:
- **Quien ya sabe del tema:** practica decisiones y compite por el puntaje.
- **Quien empieza desde cero:** cada paso explica la teoría antes de actuar.

## Niveles (el pipeline completo)
1. Conocer los datos
2. Detección de duplicados
3. Detección de outliers (IQR)
4. Escalamiento (Standard / MinMax)
5. Selección de variables
6. Elegir K (método del codo + Silhouette)
7. K-Means
8. Clustering jerárquico (y concordancia con K-Means)
9. Perfilado e interpretación para marketing

## Tecnología
- **NiceGUI** para la interfaz web.
- **numpy puro** para los algoritmos (K-Means, jerárquico, Silhouette, escalado…).
- **plotly** para los gráficos.

> Se evitan `scikit-learn`, `scipy` y `matplotlib` a propósito para que la imagen
> sea ligera y **no se quede sin memoria** en planes gratuitos de despliegue.

## Correr en local
```bash
pip install -r requirements.txt
python main.py
# abre http://localhost:8080
```

## Desplegar en Railway
1. Sube este proyecto a un repositorio nuevo de GitHub.
2. En Railway: **New Project → Deploy from GitHub repo** y elige el repo.
3. Railway detecta el `Dockerfile` automáticamente.
4. Variables de entorno (Settings → Variables):
   - `STORAGE_SECRET` = una clave aleatoria larga.
5. En **Settings → Networking** pulsa **Generate Domain** (puerto `8080`).

### Persistir el ranking (opcional)
El ranking usa `app.storage.general`, que se guarda en la carpeta `.nicegui`.
Para que sobreviva a los redeploys, monta un **Volume** en Railway y apunta ahí
el almacenamiento (o simplemente acepta que se reinicie en cada despliegue, que
suele bastar para un uso de clase).
