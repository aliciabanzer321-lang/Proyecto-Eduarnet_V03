# 💧 App de Diseño de Red de Agua Potable (genérica)

App interactiva para diseñar redes de agua potable de **cualquier
municipio/proyecto**: población, caudales de diseño (NB 689), reparto de
caudales, diámetros y verificación hidráulica real (motor EPANET vía WNTR).

Trae datos de ejemplo (proyecto San Matías) precargados, pero **todo es
editable**: censos, cantidad de nodos y tramos, parámetros de diseño, ficha
del proyecto, logo, etc.

## Estructura del proyecto

```
├── app.py            # Interfaz Streamlit (8 pestañas)
├── calculos.py         # Fórmulas: población, caudales, reparto, diámetros, hidráulica
├── data.py              # Datos de EJEMPLO + textos de referencia normativa
├── requirements.txt
├── runtime.txt          # Sugiere Python 3.12 (ver nota importante abajo)
├── .streamlit/config.toml
└── README.md
```

## 1. Probarla en tu computadora

```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## 2. Subirla a GitHub

```bash
cd nombre_de_la_carpeta
git init
git add .
git commit -m "App de diseno de red de agua potable"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

## 3. Desplegarla en Streamlit Community Cloud

1. https://share.streamlit.io/ → inicia sesión con GitHub.
2. "New app" → elige tu repo, rama `main`, archivo `app.py`.
3. **IMPORTANTE:** antes de darle a "Deploy", abre **"Advanced settings"** y
   en **"Python version"** elige **3.12** (ver nota abajo).
4. Deploy. Espera 1-3 min mientras instala `wntr` y las demás dependencias.

## ⚠️ Nota importante: error `undefined symbol` / simulación que no corre

Si al correr la Verificación Hidráulica o generar el `.inp` te sale un error
como:
```
undefined symbol: _ZTVN10__cxxabiv120__si_class_type_infoE
```
Es porque Streamlit Cloud desplegó tu app con una versión de Python
demasiado nueva (3.13/3.14) para la que `wntr` todavía no tiene un binario
100% compatible (choque de ABI de C++). **Solución:**

1. En tu app dentro de share.streamlit.io, clic en los tres puntos (⋮) →
   **Settings** → **Advanced settings**.
2. Cambia **Python version** a **3.12** → **Save**.
3. Streamlit avisa que necesitas re-desplegar para que el cambio de versión
   de Python tome efecto: **borra la app y créala de nuevo** (mismo repo,
   misma rama, mismo archivo `app.py`), eligiendo Python 3.12 en "Advanced
   settings" **antes** de darle a "Deploy" esta vez.
4. El archivo `runtime.txt` (con "3.12" adentro) es un intento adicional,
   pero a veces Streamlit Cloud lo ignora — el ajuste manual en "Advanced
   settings" es el que realmente funciona.

## Notas técnicas

- Los datos "duros" de ejemplo (censos, topología, elevaciones) están en
  `data.py`, pero la app los carga solo como punto de partida — edítalos
  libremente desde la interfaz (pestañas 1, 2 y 3) para tu propio proyecto.
- La pestaña 3 (Topología) permite agregar/quitar nodos y tramos con las
  tablas editables, y también subir tus propios datos vía CSV.
- La pestaña 0 (Datos del proyecto) genera una ficha con nombre, ubicación,
  cliente, elaborado por, fecha, descripción y logo — útil para portadas de
  memorias de cálculo.
