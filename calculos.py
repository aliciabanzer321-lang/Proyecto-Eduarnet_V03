"""
Cálculos del proyecto de agua potable.
Todas las funciones son GENÉRICAS: no asumen una cantidad fija de nodos ni
de tramos, para que la app sirva para cualquier municipio/proyecto.

Cada función indica en su docstring la normativa/criterio en que se basa.
"""
import math
import pandas as pd


# ---------------------------------------------------------------------------
# 3b. POSICIONES AUTOMÁTICAS PARA EL DIAGRAMA DE LA RED
# ---------------------------------------------------------------------------
def layout_automatico(df_nodos, df_tramos, tanque_id):
    """
    Calcula posiciones (x,y) para dibujar la red automáticamente, usando un
    layout tipo 'resorte' (Fruchterman-Reingold, vía networkx) que separa
    los nodos según cómo están conectados. Sirve como punto de partida: el
    usuario puede ajustar manualmente las coordenadas después.
    """
    import networkx as nx

    G = nx.Graph()
    G.add_node(tanque_id)
    for n in df_nodos["Nodo"]:
        G.add_node(n)
    for _, row in df_tramos.iterrows():
        G.add_edge(row["Nodo 1"], row["Nodo 2"])

    pos = nx.spring_layout(G, seed=42, k=1.2)
    return {n: (float(p[0]), float(p[1])) for n, p in pos.items()}


# ---------------------------------------------------------------------------
# 1. POBLACIÓN
# ---------------------------------------------------------------------------
def calcular_poblacion(P0, Pf_censo, t_intercensal, anio_censo, anio_base, t_diseno):
    """
    Proyección de población por el método del ÍNDICE PROMEDIO
    (aritmético + geométrico), criterio recomendado por la NB 689 cuando
    se cuenta con datos de al menos 2 censos.

    iA = ((Pf/P0) - 1) * (100/t)                    <- método aritmético
    iG = ((Pf/P0)^(1/t) - 1) * 100                   <- método geométrico
    i  = (iA + iG) / 2                                <- índice adoptado

    Pf_diseno = Pf_censo * (1+i/100)^(t_censo->base) * (1+i/100)^t_diseno
    """
    iA = ((Pf_censo / P0) - 1) * (100 / t_intercensal)
    iG = (((Pf_censo / P0) ** (1 / t_intercensal)) - 1) * 100
    i = (iA + iG) / 2

    t1 = anio_base - anio_censo
    P_base = Pf_censo * (1 + i / 100) ** t1
    anio_final = anio_base + t_diseno
    Pf_diseno = P_base * (1 + i / 100) ** t_diseno

    serie = pd.DataFrame({
        "t": range(0, t_diseno + 1),
        "Año": [anio_base + k for k in range(0, t_diseno + 1)],
        "Población": [P_base * (1 + i / 100) ** k for k in range(0, t_diseno + 1)],
    })

    return {
        "iA": iA, "iG": iG, "i": i, "t1": t1, "P_base": P_base,
        "anio_final": anio_final, "Pf_diseno": Pf_diseno, "serie": serie,
    }


# ---------------------------------------------------------------------------
# 2. CAUDALES DE DISEÑO (NB 689 - Reglamento Técnico de Diseño de Sistemas
#    de Agua Potable, Bolivia). Ajusta los rangos en la interfaz si tu
#    normativa local (RAS, CONAGUA, etc.) usa otros valores.
# ---------------------------------------------------------------------------
def calcular_caudales(Pf, Do, d, t, k1, k2, pct_proyecto):
    """
    Do : dotación inicial (l/hab.dia)              -> NB 689, Tabla 3
    d  : incremento anual dotación (%)              -> NB 689, Sección 3.3.2
    t  : periodo de diseño (años)                   -> criterio del proyectista
    k1 : coef. caudal máximo diario (usual 1.2-1.5) -> NB 689, Sección 3.4.2
    k2 : coef. caudal máximo horario (usual 1.5-2.2)-> NB 689, Tabla 4
    pct_proyecto: % de la población total que cubre este proyecto específico
    """
    Df = Do * (1 + d / 100) ** t
    Qmd = (Pf * Df) / 86400
    Qmax_d = k1 * Qmd
    Qmax_h = k2 * Qmax_d
    Qproy = Qmax_h * pct_proyecto / 100
    return {"Df": Df, "Qmd": Qmd, "Qmax_d": Qmax_d, "Qmax_h": Qmax_h, "Qproy": Qproy}


# ---------------------------------------------------------------------------
# 4. REPARTO DE CAUDALES (método de longitudes tributarias / semisuma)
# ---------------------------------------------------------------------------
def reparto_caudales(Qproy, df_nodos, df_tramos):
    """
    Reparte Qproy (l/s) entre los nodos según longitud tributaria: a cada
    nodo se le asigna la semisuma de las longitudes de los tramos de
    DISTRIBUCIÓN (columna 'Es aducción' = False) que llegan a él.
    Método clásico de diseño de redes ramificadas/malladas. Los tramos
    marcados como aducción no participan del reparto: transportan el
    caudal completo aguas arriba del primer nodo de la red.

    df_nodos : DataFrame con columna 'Nodo'
    df_tramos: DataFrame con columnas 'Nodo 1','Nodo 2','Longitud (m)','Es aducción'
    """
    tramos_dist = df_tramos[~df_tramos["Es aducción"].astype(bool)]
    long_total = float(tramos_dist["Longitud (m)"].sum())

    trib = {n: 0.0 for n in df_nodos["Nodo"]}
    for _, row in tramos_dist.iterrows():
        n1, n2, L = row["Nodo 1"], row["Nodo 2"], row["Longitud (m)"]
        if n1 in trib:
            trib[n1] += L / 2
        if n2 in trib:
            trib[n2] += L / 2

    qu = Qproy / long_total if long_total > 0 else 0.0
    demandas = {n: trib[n] * qu for n in trib}

    df = pd.DataFrame({
        "Nodo": list(trib.keys()),
        "Longitud tributaria (m)": list(trib.values()),
        "Demanda base (l/s)": [demandas[n] for n in trib],
    })
    return df, demandas, long_total, qu


# ---------------------------------------------------------------------------
# 5. DIÁMETROS TEÓRICOS (criterio de continuidad, Q = v·A) + redondeo
#    al diámetro comercial inmediato superior.
# ---------------------------------------------------------------------------
def diametro_comercial(theo_mm, tabla):
    """Redondea hacia arriba al diámetro comercial inmediato superior."""
    for label, mm in tabla:
        if theo_mm <= mm:
            return label, mm
    return "FUERA DE RANGO", None


def diametros_teoricos(demandas, v_diseno, tabla_comercial):
    """
    d = raiz( 4*Q / (pi * v) )   <- ecuación de continuidad
    v_diseno: velocidad admisible de diseño (criterio usual 0.3-3.0 m/s,
    verificar el rango de tu normativa local).
    """
    filas = []
    for nodo, q_ls in demandas.items():
        q_m3s = q_ls / 1000
        d_m = math.sqrt((4 * q_m3s) / (math.pi * v_diseno)) if v_diseno > 0 else 0
        d_mm = d_m * 1000
        label, mm_com = diametro_comercial(d_mm, tabla_comercial)
        filas.append({
            "Nodo": nodo, "Q (l/s)": q_ls, "D teórico (mm)": d_mm,
            "D comercial (pulg)": label, "D comercial (mm)": mm_com,
        })
    return pd.DataFrame(filas)


def diametro_aduccion(Qproy, v_diseno, tabla_comercial):
    q_m3s = Qproy / 1000
    d_m = math.sqrt((4 * q_m3s) / (math.pi * v_diseno)) if v_diseno > 0 else 0
    d_mm = d_m * 1000
    label, mm_com = diametro_comercial(d_mm, tabla_comercial)
    return d_mm, label, mm_com


# ---------------------------------------------------------------------------
# 8. VERIFICACIÓN HIDRÁULICA (simulación real, motor EPANET vía WNTR)
# ---------------------------------------------------------------------------
def simular_red(df_nodos, df_tramos, demandas_ls, diametros_mm, tanque_id, tanque_elev, hazen_c):
    """
    Corre la red completa con el solver real de EPANET (continuidad en cada
    nodo + pérdida de carga Hazen-Williams en cada tramo/circuito, resuelto
    por el método del gradiente / Newton-Raphson que usa EPANET).

    df_nodos : DataFrame con columnas 'Nodo','Elevación (msnm)'
    df_tramos: DataFrame con columnas 'Tramo','Nodo 1','Nodo 2','Longitud (m)'
    demandas_ls  : dict {nodo: demanda l/s}
    diametros_mm : dict {tramo_id: diámetro mm}
    """
    import wntr

    wn = wntr.network.WaterNetworkModel()
    wn.options.hydraulic.headloss = "H-W"
    wn.add_reservoir(tanque_id, base_head=tanque_elev)

    for _, row in df_nodos.iterrows():
        nodo = row["Nodo"]
        wn.add_junction(nodo, base_demand=demandas_ls.get(nodo, 0.0) / 1000.0,
                         elevation=row["Elevación (msnm)"])

    for _, row in df_tramos.iterrows():
        tid, n1, n2, L = row["Tramo"], row["Nodo 1"], row["Nodo 2"], row["Longitud (m)"]
        d_m = diametros_mm[tid] / 1000.0
        wn.add_pipe(f"P{tid}", n1, n2, length=L, diameter=d_m,
                    roughness=hazen_c, minor_loss=0.0)

    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()

    flow = results.link["flowrate"].iloc[0]
    vel = results.link["velocity"].iloc[0]
    hl = results.link["headloss"].iloc[0]   # gradiente (m/m) -> x1000 = m/km
    pres = results.node["pressure"].iloc[0]

    filas = []
    for _, row in df_tramos.iterrows():
        tid, n1, n2, L = row["Tramo"], row["Nodo 1"], row["Nodo 2"], row["Longitud (m)"]
        lname = f"P{tid}"
        v = float(vel[lname])
        filas.append({
            "Tramo": tid, "Nodo 1": n1, "Nodo 2": n2, "Longitud (m)": L,
            "Diámetro (mm)": diametros_mm[tid],
            "Caudal (l/s)": abs(float(flow[lname]) * 1000),
            "Velocidad (m/s)": abs(v),
            "Pérdida unit. (m/km)": abs(float(hl[lname]) * 1000),
            "Velocidad OK": "SI" if 0.3 <= abs(v) <= 2.5 else "REVISAR",
        })
    df_tramos_res = pd.DataFrame(filas)
    presiones = pd.Series({n: float(pres[n]) for n in df_nodos["Nodo"]}, name="Presión (m)")
    return df_tramos_res, presiones
