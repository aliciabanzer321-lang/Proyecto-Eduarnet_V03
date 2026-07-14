"""
Datos de EJEMPLO (proyecto San Matías) usados como valores iniciales al
abrir la app. TODO esto es editable desde la interfaz (población, censos,
topología de la red, diámetros, etc.) para poder usar la app en cualquier
municipio/proyecto. Estos valores solo sirven de plantilla / demostración.
"""
import pandas as pd

# ---------------------------------------------------------------------------
# Datos censales de ejemplo
# ---------------------------------------------------------------------------
EJEMPLO_CENSO = {
    "P0_censo": 14470,        # Población censo anterior
    "Pf_censo": 15378,        # Población censo más reciente
    "t_intercensal": 12,      # años entre censos
    "anio_censo": 2024,       # año del censo más reciente
    "anio_base": 2026,        # año base del proyecto (año actual)
}

# ---------------------------------------------------------------------------
# Datos generales de la red de ejemplo
# ---------------------------------------------------------------------------
EJEMPLO_TANQUE_ID = "TANQUE"
EJEMPLO_TANQUE_ELEV = 150   # msnm
EJEMPLO_HAZEN_C = 150

EJEMPLO_NODOS = pd.DataFrame({
    "Nodo": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
             "K", "L", "M", "N", "O", "P", "Q", "R"],
    "Elevación (msnm)": [120, 120, 119, 118, 119, 119, 118, 118, 117, 117,
                          118, 118, 117, 118, 117, 118, 119, 118],
    "X": [0.0] * 18,
    "Y": [0.0] * 18,
})
EJEMPLO_TANQUE_XY = (0.0, 0.0)

# Tramo 1 = línea de aducción (Tanque -> A); tramos 2-28 = red de distribución
EJEMPLO_TRAMOS = pd.DataFrame([
    (1, "TANQUE", "A", 91.39, True),
    (2, "F", "A", 115.47, False),
    (3, "G", "F", 113.71, False),
    (4, "L", "G", 117.66, False),
    (5, "M", "L", 121.16, False),
    (6, "R", "M", 120.65, False),
    (7, "R", "Q", 104.34, False),
    (8, "Q", "P", 113.93, False),
    (9, "P", "O", 112.40, False),
    (10, "O", "J", 119.41, False),
    (11, "J", "I", 123.61, False),
    (12, "I", "D", 113.82, False),
    (13, "D", "C", 115.24, False),
    (14, "E", "B", 117.34, False),
    (15, "H", "E", 114.74, False),
    (16, "K", "H", 118.31, False),
    (17, "N", "K", 120.19, False),
    (18, "Q", "N", 115.09, False),
    (19, "M", "N", 109.69, False),
    (20, "L", "K", 112.66, False),
    (21, "G", "H", 112.22, False),
    (22, "F", "E", 113.32, False),
    (23, "A", "B", 112.54, False),
    (24, "B", "C", 113.36, False),
    (25, "E", "D", 114.45, False),
    (26, "H", "I", 114.85, False),
    (27, "K", "J", 114.06, False),
    (28, "N", "O", 111.39, False),
], columns=["Tramo", "Nodo 1", "Nodo 2", "Longitud (m)", "Es aducción"])

# Diámetros finales adoptados y validados por simulación hidráulica real
EJEMPLO_DIAMETROS_MM = {
    1: 101.6, 2: 101.6, 3: 101.6, 4: 76.2, 5: 76.2, 6: 38.1, 7: 25.4,
    8: 25.4, 9: 25.4, 10: 25.4, 11: 25.4, 12: 25.4, 13: 25.4, 14: 76.2,
    15: 76.2, 16: 50.8, 17: 76.2, 18: 50.8, 19: 38.1, 20: 50.8, 21: 25.4,
    22: 76.2, 23: 76.2, 24: 25.4, 25: 50.8, 26: 50.8, 27: 50.8, 28: 38.1,
}

# Tabla de diámetros comerciales PVC (pulgada -> mm) - editable en la app
DIAMETROS_COMERCIALES = [
    ('1/2"', 12.7), ('3/4"', 19.05), ('1"', 25.4), ('1 1/2"', 38.1),
    ('2"', 50.8), ('3"', 76.2), ('4"', 101.6), ('6"', 152.4),
    ('8"', 203.2), ('10"', 254.0), ('12"', 304.8),
]

# ---------------------------------------------------------------------------
# Textos de referencia normativa (mostrados como ayuda en la interfaz).
# Basados en NB 689 (Bolivia). Si tu proyecto usa otra norma (RAS 2000 en
# Colombia, CONAGUA en México, etc.), edita estos textos o los rangos de
# los sliders en la interfaz según corresponda.
# ---------------------------------------------------------------------------
NORMATIVA = {
    "poblacion": (
        "**Proyección de población** - método del índice promedio "
        "(aritmético + geométrico) usando dos censos. Es el método más "
        "usual cuando se cuenta con datos censales confiables; si solo hay "
        "un censo, la norma permite usar tasas de crecimiento departamentales "
        "o nacionales (INE)."
    ),
    "dotacion": (
        "**Dotación inicial (Do)** - NB 689, Tabla 3: la dotación recomendada "
        "depende de la zona geográfica (Altiplano, Valles, Llanos) y del "
        "rango poblacional. Para 5 001-20 000 hab en zona Llanos: 120-180 "
        "l/hab·día. Ajusta el rango según tu zona y tamaño de población."
    ),
    "incremento_dotacion": (
        "**Incremento anual de la dotación (d)** - NB 689, Sección 3.3.2: "
        "\"La dotación futura puede estimarse con un incremento anual entre "
        "0.50% y 2%.\" La norma no fija un valor único; se recomienda el "
        "promedio del rango salvo que existan estudios de consumo propios."
    ),
    "k1": (
        "**Coeficiente K1 (caudal máximo diario)** - NB 689, Sección 3.4.2: "
        "rango usual 1.20 a 1.50. Representa el incremento de consumo en el "
        "día de mayor demanda del año."
    ),
    "k2": (
        "**Coeficiente K2 (caudal máximo horario)** - NB 689, Tabla 4: "
        "para poblaciones entre 10 001 y 100 000 hab, rango usual 1.50-1.80 "
        "(varía según tamaño de población, revisar la tabla completa de la "
        "norma para tu rango poblacional específico)."
    ),
    "velocidad": (
        "**Velocidad de diseño** - criterio de continuidad (Q = v·A). Rango "
        "admisible usual en redes de agua potable: 0.3-2.5 m/s (velocidades "
        "menores favorecen sedimentación; mayores generan golpe de ariete y "
        "desgaste). Verifica el rango específico de tu normativa local."
    ),
    "reparto": (
        "**Reparto de caudales** - método de longitud tributaria (semisuma "
        "de tramos que llegan a cada nodo), método clásico de diseño de "
        "redes de distribución cuando no se cuenta con catastro de usuarios "
        "por predio."
    ),
    "hidraulica": (
        "**Verificación hidráulica** - simulación real con el motor de "
        "cálculo de EPANET (continuidad en cada nodo + pérdida de carga "
        "Hazen-Williams en cada tramo, resuelto por el método del "
        "gradiente). Es indispensable en redes con circuitos/mallas, donde "
        "el caudal real de cada tramo depende del balance de toda la red y "
        "no puede obtenerse con una fórmula simple por nodo."
    ),
}
