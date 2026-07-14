import streamlit as st
import pandas as pd

import data
import calculos

st.set_page_config(page_title="Diseño de Red de Agua Potable", page_icon="💧", layout="wide")

# ===========================================================================
# ESTADO INICIAL (se carga una sola vez por sesión; todo editable después)
# ===========================================================================
def _init_state():
    defaults = {
        "proyecto_nombre": "Proyecto San Matías - Agua Potable",
        "proyecto_ubicacion": "San Matías, Santa Cruz, Bolivia",
        "proyecto_cliente": "",
        "proyecto_elaborado_por": "",
        "proyecto_fecha": "",
        "proyecto_descripcion": (
            "Diseño de la red de distribución de agua potable, según NB 689."
        ),
        "proyecto_logo": None,
        "censo": dict(data.EJEMPLO_CENSO),
        "tanque_id": data.EJEMPLO_TANQUE_ID,
        "tanque_elev": data.EJEMPLO_TANQUE_ELEV,
        "hazen_c": data.EJEMPLO_HAZEN_C,
        "df_nodos": data.EJEMPLO_NODOS.copy(),
        "df_tramos": data.EJEMPLO_TRAMOS.copy(),
        "tanque_xy": data.EJEMPLO_TANQUE_XY,
        "df_diametros": pd.DataFrame({
            "Tramo": list(data.EJEMPLO_DIAMETROS_MM.keys()),
            "Diámetro (mm)": list(data.EJEMPLO_DIAMETROS_MM.values()),
        }),
        "df_comercial": pd.DataFrame(data.DIAMETROS_COMERCIALES, columns=["Pulgada", "mm"]),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()

# ===========================================================================
# ENCABEZADO
# ===========================================================================
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if st.session_state["proyecto_logo"] is not None:
        st.image(st.session_state["proyecto_logo"], width=90)
with col_title:
    st.title(f"💧 {st.session_state['proyecto_nombre']}")
    st.caption(st.session_state["proyecto_ubicacion"])

st.caption(
    "App genérica de diseño de redes de agua potable: población, caudales "
    "(NB 689), reparto de caudales, diámetros y verificación hidráulica real "
    "con EPANET. Adaptable a cualquier proyecto: cambia los datos censales, "
    "la cantidad de nodos/tramos y los parámetros de diseño en cada pestaña."
)

tabs = st.tabs([
    "📋 Datos del proyecto",
    "1️⃣ Población",
    "2️⃣ Caudales de diseño",
    "3️⃣ Topología de la red",
    "🗺️ Diagrama de la red",
    "4️⃣ Reparto de caudales",
    "5️⃣ Diámetros",
    "6️⃣ Datos EPANET",
    "7️⃣ Verificación hidráulica",
])

# ===========================================================================
# TAB 0 - DATOS DEL PROYECTO
# ===========================================================================
with tabs[0]:
    st.header("Ficha del proyecto")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state["proyecto_nombre"] = st.text_input(
            "Nombre del proyecto", st.session_state["proyecto_nombre"])
        st.session_state["proyecto_ubicacion"] = st.text_input(
            "Ubicación (municipio, provincia, país)", st.session_state["proyecto_ubicacion"])
        st.session_state["proyecto_cliente"] = st.text_input(
            "Cliente / entidad contratante", st.session_state["proyecto_cliente"])
        st.session_state["proyecto_elaborado_por"] = st.text_input(
            "Elaborado por", st.session_state["proyecto_elaborado_por"])
        st.session_state["proyecto_fecha"] = st.text_input(
            "Fecha", st.session_state["proyecto_fecha"], placeholder="ej. julio 2026")
    with c2:
        st.session_state["proyecto_descripcion"] = st.text_area(
            "Descripción / comentarios del proyecto",
            st.session_state["proyecto_descripcion"], height=150)
        logo_file = st.file_uploader("Logo (opcional)", type=["png", "jpg", "jpeg"])
        if logo_file is not None:
            st.session_state["proyecto_logo"] = logo_file.getvalue()
        if st.session_state["proyecto_logo"] is not None:
            st.image(st.session_state["proyecto_logo"], width=120, caption="Logo actual")
            if st.button("Quitar logo"):
                st.session_state["proyecto_logo"] = None
                st.rerun()

    st.divider()
    st.subheader("Resumen para portada / memoria de cálculo")
    st.table(pd.DataFrame({
        "Campo": ["Proyecto", "Ubicación", "Cliente", "Elaborado por", "Fecha"],
        "Valor": [st.session_state["proyecto_nombre"], st.session_state["proyecto_ubicacion"],
                  st.session_state["proyecto_cliente"] or "-",
                  st.session_state["proyecto_elaborado_por"] or "-",
                  st.session_state["proyecto_fecha"] or "-"],
    }))


# ===========================================================================
# TAB 1 - POBLACIÓN
# ===========================================================================
with tabs[1]:
    st.header("1. Población de diseño")
    st.info(data.NORMATIVA["poblacion"])

    st.subheader("Datos censales (edítalos para tu municipio)")
    c1, c2, c3 = st.columns(3)
    censo = st.session_state["censo"]
    with c1:
        censo["P0_censo"] = st.number_input("Población censo anterior (P0)",
                                              min_value=1, value=int(censo["P0_censo"]))
        censo["anio_censo"] = st.number_input("Año del censo más reciente",
                                                min_value=1900, max_value=2100,
                                                value=int(censo["anio_censo"]))
    with c2:
        censo["Pf_censo"] = st.number_input("Población censo más reciente (Pf)",
                                              min_value=1, value=int(censo["Pf_censo"]))
        censo["anio_base"] = st.number_input("Año base del proyecto (año actual)",
                                               min_value=1900, max_value=2100,
                                               value=int(censo["anio_base"]))
    with c3:
        censo["t_intercensal"] = st.number_input("Periodo intercensal (años)",
                                                   min_value=1, value=int(censo["t_intercensal"]))
        t_diseno = st.number_input("Periodo de diseño (años) - libre, lo define el cliente",
                                     min_value=1, max_value=60, value=20)

    st.session_state["censo"] = censo

    pob = calculos.calcular_poblacion(
        censo["P0_censo"], censo["Pf_censo"], censo["t_intercensal"],
        censo["anio_censo"], censo["anio_base"], t_diseno,
    )

    st.subheader("Índices de crecimiento")
    c1, c2, c3 = st.columns(3)
    c1.metric("iA (aritmético)", f"{pob['iA']:.3f} %")
    c2.metric("iG (geométrico)", f"{pob['iG']:.3f} %")
    c3.metric("i (promedio adoptado)", f"{pob['i']:.3f} %")

    st.subheader("Proyección")
    c1, c2 = st.columns(2)
    c1.metric(f"Población año base ({censo['anio_base']})", f"{pob['P_base']:,.0f} hab")
    c2.metric(f"Población de diseño ({pob['anio_final']})", f"{pob['Pf_diseno']:,.0f} hab")

    st.line_chart(pob["serie"].set_index("Año")["Población"])
    with st.expander("Ver tabla año a año"):
        st.dataframe(pob["serie"], use_container_width=True, hide_index=True)

    st.session_state["Pf_diseno"] = pob["Pf_diseno"]
    st.session_state["t_diseno"] = t_diseno


# ===========================================================================
# TAB 2 - CAUDALES DE DISEÑO
# ===========================================================================
with tabs[2]:
    st.header("2. Caudales de diseño")
    Pf = st.session_state.get("Pf_diseno", 17220.0)
    t_diseno = st.session_state.get("t_diseno", 20)

    st.info(f"Población de diseño (pestaña 1): **{Pf:,.0f} hab** · "
            f"Periodo de diseño: **{t_diseno} años**")

    st.subheader("Dotación")
    st.caption(data.NORMATIVA["dotacion"])
    c1, c2 = st.columns(2)
    with c1:
        Do_min, Do_max = st.slider("Rango dotación inicial (l/hab·día)", 50, 300, (120, 180))
        Do = (Do_min + Do_max) / 2
        st.metric("Do adoptado", f"{Do:.1f} l/hab·día")
    with c2:
        st.caption(data.NORMATIVA["incremento_dotacion"])
        d_min, d_max = st.slider("Rango incremento anual dotación (%)", 0.0, 5.0, (0.5, 2.0), step=0.05)
        d = (d_min + d_max) / 2
        st.metric("d adoptado", f"{d:.2f} %")

    st.subheader("Coeficientes de variación")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption(data.NORMATIVA["k1"])
        k1_min, k1_max = st.slider("Rango K1", 1.0, 2.0, (1.20, 1.50), step=0.05)
        k1 = (k1_min + k1_max) / 2
        st.metric("K1 adoptado", f"{k1:.2f}")
    with c2:
        st.caption(data.NORMATIVA["k2"])
        k2_min, k2_max = st.slider("Rango K2", 1.0, 2.5, (1.50, 1.80), step=0.05)
        k2 = (k2_min + k2_max) / 2
        st.metric("K2 adoptado", f"{k2:.2f}")
    with c3:
        st.caption("Porcentaje de la población total que cubre este proyecto (si es toda, deja 100%).")
        pct_proyecto = st.number_input("Cobertura del proyecto (%)", 1.0, 100.0, 100.0)

    res = calculos.calcular_caudales(Pf, Do, d, t_diseno, k1, k2, pct_proyecto)

    st.subheader("Resultados")
    c1, c2, c3 = st.columns(3)
    c1.metric("Dotación futura (Df)", f"{res['Df']:.2f} l/hab·día")
    c2.metric("Caudal medio diario (Qmd)", f"{res['Qmd']:.2f} l/s")
    c3.metric("Caudal máx. diario", f"{res['Qmax_d']:.2f} l/s")
    c1, c2, c3 = st.columns(3)
    c1.metric("Caudal máx. horario (100%)", f"{res['Qmax_h']:.2f} l/s")
    c2.metric(f"Caudal de diseño del proyecto ({pct_proyecto:.0f}%)", f"{res['Qproy']:.2f} l/s")
    c3.metric("Periodo de diseño", f"{t_diseno} años")

    st.session_state["Qproy"] = res["Qproy"]


# ===========================================================================
# TAB 3 - TOPOLOGÍA DE LA RED (dinámica: agrega/quita nodos y tramos)
# ===========================================================================
with tabs[3]:
    st.header("3. Topología de la red")
    st.write(
        "La cantidad de nodos y tramos **no es fija**: agrega o elimina filas "
        "directamente en las tablas (ícono ➕ al final de cada tabla, o clic "
        "derecho / selecciona fila y borra). También puedes subir tus propios "
        "datos desde un CSV."
    )

    st.subheader("Datos generales")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state["tanque_id"] = st.text_input("ID del tanque/reservorio",
                                                         st.session_state["tanque_id"])
    with c2:
        st.session_state["tanque_elev"] = st.number_input(
            "Elevación del tanque (msnm)", value=float(st.session_state["tanque_elev"]))
    with c3:
        st.session_state["hazen_c"] = st.number_input(
            "Coeficiente Hazen-Williams (C)", value=float(st.session_state["hazen_c"]),
            help="PVC nuevo ≈150, HDPE ≈150, fierro fundido usado ≈100-120.")

    st.subheader("Nodos (uniones)")
    up_nodos = st.file_uploader("Subir CSV de nodos (columnas: Nodo, Elevación (msnm))",
                                  type=["csv"], key="up_nodos")
    if up_nodos is not None:
        st.session_state["df_nodos"] = pd.read_csv(up_nodos)
    st.session_state["df_nodos"] = st.data_editor(
        st.session_state["df_nodos"], num_rows="dynamic",
        use_container_width=True, hide_index=True, key="editor_nodos")
    st.download_button("⬇️ Descargar nodos como CSV",
                        st.session_state["df_nodos"].to_csv(index=False),
                        "nodos.csv", "text/csv")

    st.subheader("Tramos (tuberías)")
    st.caption(
        "Marca 'Es aducción' = True en la(s) tubería(s) que van del tanque a "
        "la red: esas no se reparten (transportan el 100% del caudal)."
    )
    up_tramos = st.file_uploader(
        "Subir CSV de tramos (columnas: Tramo, Nodo 1, Nodo 2, Longitud (m), Es aducción)",
        type=["csv"], key="up_tramos")
    if up_tramos is not None:
        st.session_state["df_tramos"] = pd.read_csv(up_tramos)
    st.session_state["df_tramos"] = st.data_editor(
        st.session_state["df_tramos"], num_rows="dynamic",
        use_container_width=True, hide_index=True, key="editor_tramos")
    st.download_button("⬇️ Descargar tramos como CSV",
                        st.session_state["df_tramos"].to_csv(index=False),
                        "tramos.csv", "text/csv")

    st.metric("Nº de nodos", len(st.session_state["df_nodos"]))
    st.metric("Nº de tramos", len(st.session_state["df_tramos"]))
    st.metric("Longitud total de la red",
              f"{st.session_state['df_tramos']['Longitud (m)'].sum():,.2f} m")


# ===========================================================================
# TAB 4 - REPARTO DE CAUDALES
# ===========================================================================
with tabs[4]:
    st.header("Diagrama de la red")
    st.write(
        "Diagrama interactivo generado a partir de tu tabla de nodos y "
        "tramos (pestaña 3): acércate con scroll, pasa el mouse sobre un "
        "nodo o tramo para ver sus datos. Las posiciones (X, Y) son "
        "editables por si quieres acomodar el dibujo a la disposición real "
        "del terreno."
    )

    df_nodos = st.session_state["df_nodos"]
    df_tramos = st.session_state["df_tramos"]

    if df_nodos.empty or df_tramos.empty:
        st.warning("Completa la topología de la red en la pestaña 3 primero.")
    else:
        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("🔄 Generar posiciones automáticas"):
                pos = calculos.layout_automatico(df_nodos, df_tramos, st.session_state["tanque_id"])
                df_nodos = df_nodos.copy()
                df_nodos["X"] = df_nodos["Nodo"].map(lambda n: pos.get(n, (0, 0))[0])
                df_nodos["Y"] = df_nodos["Nodo"].map(lambda n: pos.get(n, (0, 0))[1])
                st.session_state["df_nodos"] = df_nodos
                tx, ty = pos.get(st.session_state["tanque_id"], (0, 0))
                st.session_state["tanque_xy"] = (tx, ty)
                st.rerun()
            st.caption(
                "Genera un acomodo inicial automático; luego edita X e Y a "
                "mano (abajo o en la pestaña 3) para que se parezca al "
                "plano real del terreno."
            )

            tx, ty = st.session_state["tanque_xy"]
            tx = st.number_input("X del tanque", value=float(tx))
            ty = st.number_input("Y del tanque", value=float(ty))
            st.session_state["tanque_xy"] = (tx, ty)

        with c2:
            with st.expander("Editar posiciones X, Y de los nodos", expanded=False):
                st.session_state["df_nodos"] = st.data_editor(
                    st.session_state["df_nodos"], use_container_width=True,
                    hide_index=True, key="editor_nodos_xy")

        df_nodos = st.session_state["df_nodos"]
        demandas = st.session_state.get("demandas", {})
        diam_map = dict(zip(st.session_state["df_diametros"]["Tramo"],
                             st.session_state["df_diametros"]["Diámetro (mm)"])) \
            if "df_diametros" in st.session_state else {}

        import plotly.graph_objects as go

        fig = go.Figure()
        pos_nodo = {row["Nodo"]: (row["X"], row["Y"]) for _, row in df_nodos.iterrows()}
        tx, ty = st.session_state["tanque_xy"]
        pos_nodo[st.session_state["tanque_id"]] = (tx, ty)

        # --- tramos (líneas) ---
        for _, row in df_tramos.iterrows():
            n1, n2 = row["Nodo 1"], row["Nodo 2"]
            if n1 not in pos_nodo or n2 not in pos_nodo:
                continue
            x1, y1 = pos_nodo[n1]
            x2, y2 = pos_nodo[n2]
            es_aduccion = bool(row.get("Es aducción", False))
            diam = diam_map.get(row["Tramo"])
            hover = (f"Tramo {row['Tramo']}: {n1} → {n2}<br>"
                     f"Longitud: {row['Longitud (m)']} m"
                     + (f"<br>Diámetro: {diam} mm" if diam else "")
                     + ("<br>(Línea de aducción)" if es_aduccion else ""))
            fig.add_trace(go.Scatter(
                x=[x1, x2], y=[y1, y2], mode="lines",
                line=dict(width=4 if es_aduccion else 2,
                          color="#C00000" if es_aduccion else "#2E75B6"),
                hovertext=hover, hoverinfo="text", showlegend=False,
            ))
            fig.add_annotation(x=(x1 + x2) / 2, y=(y1 + y2) / 2,
                                text=str(row["Tramo"]), showarrow=False,
                                font=dict(size=10, color="gray"))

        # --- nodos (puntos) ---
        xs, ys, labels, hovers = [], [], [], []
        for _, row in df_nodos.iterrows():
            n = row["Nodo"]
            xs.append(row["X"]); ys.append(row["Y"]); labels.append(n)
            dem = demandas.get(n)
            hovers.append(f"Nodo {n}<br>Elevación: {row['Elevación (msnm)']} msnm"
                           + (f"<br>Demanda: {dem:.3f} l/s" if dem is not None else ""))
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers+text", text=labels, textposition="top center",
            marker=dict(size=16, color="#E2EFDA", line=dict(width=2, color="#2E75B6")),
            hovertext=hovers, hoverinfo="text", showlegend=False,
        ))

        # --- tanque (triángulo) ---
        fig.add_trace(go.Scatter(
            x=[tx], y=[ty], mode="markers+text", text=[st.session_state["tanque_id"]],
            textposition="top center",
            marker=dict(size=22, symbol="triangle-up", color="#C00000"),
            hovertext=[f"{st.session_state['tanque_id']}<br>Elevación: "
                       f"{st.session_state['tanque_elev']} msnm"],
            hoverinfo="text", showlegend=False,
        ))

        fig.update_layout(
            height=650, plot_bgcolor="white",
            xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Línea roja gruesa = tubería de aducción. Líneas azules = red de "
            "distribución. Los números junto a cada línea son el ID del tramo."
        )


with tabs[5]:
    st.header("4. Reparto de caudales por nodo")
    st.caption(data.NORMATIVA["reparto"])
    Qproy = st.session_state.get("Qproy", 0.0)
    df_nodos = st.session_state["df_nodos"]
    df_tramos = st.session_state["df_tramos"]

    if df_nodos.empty or df_tramos.empty:
        st.warning("Completa la topología de la red en la pestaña 3 primero.")
    else:
        df_reparto, demandas, long_total, qu = calculos.reparto_caudales(Qproy, df_nodos, df_tramos)

        c1, c2, c3 = st.columns(3)
        c1.metric("Qproy", f"{Qproy:.2f} l/s")
        c2.metric("Longitud total distribución", f"{long_total:,.2f} m")
        c3.metric("Caudal unitario (qu)", f"{qu:.5f} l/s·m")

        st.dataframe(df_reparto, use_container_width=True, hide_index=True)

        total_demanda = df_reparto["Demanda base (l/s)"].sum()
        check = "✅ OK" if round(total_demanda, 2) == round(Qproy, 2) else "⚠️ REVISAR"
        st.write(f"**Verificación (suma demandas = Qproy):** {total_demanda:.2f} l/s — {check}")

        st.session_state["demandas"] = demandas


# ===========================================================================
# TAB 5 - DIÁMETROS
# ===========================================================================
with tabs[6]:
    st.header("5. Diámetros teóricos y comerciales")
    demandas = st.session_state.get("demandas")
    Qproy = st.session_state.get("Qproy", 0.0)

    if not demandas:
        st.warning("Ve primero a la pestaña 'Reparto de caudales'.")
    else:
        st.caption(data.NORMATIVA["velocidad"])
        v_diseno = st.slider("Velocidad de diseño (m/s)", 0.1, 3.0, 1.0, step=0.05)

        st.subheader("Tabla de diámetros comerciales (edítala según tu material/proveedor)")
        st.session_state["df_comercial"] = st.data_editor(
            st.session_state["df_comercial"], num_rows="dynamic",
            use_container_width=True, hide_index=True, key="editor_comercial")
        tabla_comercial = list(st.session_state["df_comercial"].itertuples(index=False, name=None))

        st.subheader("Diámetro teórico por nodo (criterio de continuidad Q=v·A)")
        df_diam = calculos.diametros_teoricos(demandas, v_diseno, tabla_comercial)
        st.dataframe(df_diam, use_container_width=True, hide_index=True)

        st.subheader("Diámetro de la(s) línea(s) de aducción")
        d_mm, label, mm_com = calculos.diametro_aduccion(Qproy, v_diseno, tabla_comercial)
        c1, c2, c3 = st.columns(3)
        c1.metric("Caudal (Qproy)", f"{Qproy:.2f} l/s")
        c2.metric("Diámetro teórico", f"{d_mm:.2f} mm")
        c3.metric("Diámetro comercial", f"{label} ({mm_com} mm)")

        st.warning(
            "⚠️ En una red **cerrada/con circuitos** el diámetro de cada tramo "
            "no puede fijarse solo con la demanda de un nodo — el tramo "
            "troncal cerca del tanque transporta el caudal acumulado de toda "
            "la red aguas abajo. Este cálculo es un punto de partida; valida "
            "siempre el diseño final en la pestaña 7 (simulación hidráulica)."
        )


# ===========================================================================
# TAB 6 - DATOS PARA EPANET
# ===========================================================================
with tabs[7]:
    st.header("6. Datos para EPANET")
    demandas = st.session_state.get("demandas")
    df_nodos = st.session_state["df_nodos"]
    df_tramos = st.session_state["df_tramos"]

    if not demandas:
        st.warning("Ve primero a la pestaña 'Reparto de caudales'.")
    else:
        st.subheader("Reservorio")
        st.dataframe(pd.DataFrame([{
            "ID": st.session_state["tanque_id"],
            "Elevación (msnm)": st.session_state["tanque_elev"],
        }]), hide_index=True)

        st.subheader("Nodos (uniones)")
        df_junctions = df_nodos.copy()
        df_junctions["Demanda base (l/s)"] = df_junctions["Nodo"].map(
            lambda n: round(demandas.get(n, 0.0), 4))
        st.dataframe(df_junctions, use_container_width=True, hide_index=True)

        st.subheader("Tuberías - diámetro final (editable)")
        st.caption(
            "Precarga los diámetros calculados en la pestaña 5 (redondeados al "
            "comercial). Ajusta manualmente cualquier tramo si lo necesitas."
        )
        if st.button("↻ Recargar diámetros teóricos calculados (pestaña 5)"):
            tabla_comercial = list(st.session_state["df_comercial"].itertuples(index=False, name=None))
            nuevo = []
            for _, row in df_tramos.iterrows():
                if row["Es aducción"]:
                    _, _, mm = calculos.diametro_aduccion(
                        st.session_state.get("Qproy", 0.0), 1.0, tabla_comercial)
                else:
                    # Diámetro del tramo = mayor entre el teórico de sus 2 nodos
                    # (criterio de partida; ajustable manualmente después).
                    q1 = demandas.get(row["Nodo 1"], 0.0)
                    q2 = demandas.get(row["Nodo 2"], 0.0)
                    _, _, mm1 = calculos.diametro_aduccion(q1, 1.0, tabla_comercial)
                    _, _, mm2 = calculos.diametro_aduccion(q2, 1.0, tabla_comercial)
                    mm = max(mm1 or 0, mm2 or 0)
                nuevo.append(mm or 25.4)
            st.session_state["df_diametros"] = pd.DataFrame({
                "Tramo": df_tramos["Tramo"], "Diámetro (mm)": nuevo})

        st.session_state["df_diametros"] = st.data_editor(
            st.session_state["df_diametros"], use_container_width=True,
            hide_index=True, key="editor_diametros_final")

        df_pipes = df_tramos.merge(st.session_state["df_diametros"], on="Tramo", how="left")
        df_pipes["Rugosidad (C)"] = st.session_state["hazen_c"]
        st.dataframe(df_pipes, use_container_width=True, hide_index=True)

        try:
            import wntr
            diam_dict = dict(zip(st.session_state["df_diametros"]["Tramo"],
                                  st.session_state["df_diametros"]["Diámetro (mm)"]))
            wn = wntr.network.WaterNetworkModel()
            wn.options.hydraulic.headloss = "H-W"
            wn.add_reservoir(st.session_state["tanque_id"], base_head=st.session_state["tanque_elev"])
            for _, row in df_nodos.iterrows():
                wn.add_junction(row["Nodo"], base_demand=demandas.get(row["Nodo"], 0.0) / 1000.0,
                                 elevation=row["Elevación (msnm)"])
            for _, row in df_tramos.iterrows():
                wn.add_pipe(f"P{row['Tramo']}", row["Nodo 1"], row["Nodo 2"],
                            length=row["Longitud (m)"],
                            diameter=diam_dict.get(row["Tramo"], 25.4) / 1000.0,
                            roughness=st.session_state["hazen_c"], minor_loss=0.0)
            wntr.network.io.write_inpfile(wn, "/tmp/proyecto.inp", units="LPS")
            with open("/tmp/proyecto.inp") as f:
                inp_text = f.read()
            st.download_button("⬇️ Descargar archivo .inp para EPANET",
                                data=inp_text, file_name="proyecto.inp", mime="text/plain")
            st.caption("Ábrelo directamente en EPANET: File → Open → proyecto.inp → Run.")
        except Exception as e:
            st.error(
                f"No se pudo generar el .inp ({e}). Revisa la sección "
                "'Solución de problemas' más abajo en la pestaña de "
                "Verificación hidráulica."
            )


# ===========================================================================
# TAB 7 - VERIFICACIÓN HIDRÁULICA
# ===========================================================================
with tabs[8]:
    st.header("7. Verificación hidráulica (simulación real con EPANET)")
    st.caption(data.NORMATIVA["hidraulica"])
    demandas = st.session_state.get("demandas")
    df_nodos = st.session_state["df_nodos"]
    df_tramos = st.session_state["df_tramos"]

    if not demandas:
        st.warning("Ve primero a la pestaña 'Reparto de caudales'.")
    else:
        diam_dict = dict(zip(st.session_state["df_diametros"]["Tramo"],
                              st.session_state["df_diametros"]["Diámetro (mm)"]))

        if st.button("▶️ Correr simulación hidráulica"):
            with st.spinner("Resolviendo la red (continuidad + Hazen-Williams)..."):
                try:
                    df_sim, presiones = calculos.simular_red(
                        df_nodos, df_tramos, demandas, diam_dict,
                        st.session_state["tanque_id"], st.session_state["tanque_elev"],
                        st.session_state["hazen_c"],
                    )
                    st.session_state["df_sim"] = df_sim
                    st.session_state["presiones"] = presiones
                except Exception as e:
                    st.session_state.pop("df_sim", None)
                    st.error(f"Error en la simulación: {e}")

        if "df_sim" in st.session_state:
            df_sim = st.session_state["df_sim"]
            presiones = st.session_state["presiones"]

            st.subheader("Resultados por tramo")
            st.dataframe(df_sim, use_container_width=True, hide_index=True)

            n_revisar = (df_sim["Velocidad OK"] == "REVISAR").sum()
            if n_revisar == 0:
                st.success("✅ Todos los tramos cumplen la velocidad admisible (0.3-2.5 m/s).")
            else:
                st.error(f"⚠️ {n_revisar} tramo(s) fuera del rango admisible de velocidad.")

            st.subheader("Presión en los nodos")
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("Presión mínima", f"{presiones.min():.2f} m")
                st.metric("Presión máxima", f"{presiones.max():.2f} m")
                st.caption("Criterio usual: presión mínima de servicio 10-15 m.")
            with c2:
                st.bar_chart(presiones)

        with st.expander("🛠️ Solución de problemas: error de 'undefined symbol' o simulación que no corre"):
            st.markdown(
                "Si ves un error como `undefined symbol: _ZTVN10__cxxabiv...` o "
                "`No se pudo generar el .inp`, es un problema de **versión de "
                "Python en Streamlit Cloud**, no de tu código:\n\n"
                "1. Streamlit Community Cloud a veces usa por defecto una "
                "versión de Python muy nueva (3.14) para la que la librería "
                "`wntr` todavía no tiene un binario 100% compatible.\n"
                "2. **Solución:** en tu app dentro de Streamlit Cloud, ve a "
                "los tres puntos (⋮) → *Settings* → *Advanced settings* → "
                "cambia **Python version** a **3.12** → *Save*. Como el "
                "cambio de versión de Python requiere volver a desplegar, "
                "si no aparece la opción, borra la app y créala de nuevo "
                "eligiendo Python 3.12 en 'Advanced settings' antes de "
                "darle a Deploy.\n"
                "3. Verifica que tu `requirements.txt` no fije una versión "
                "de `wntr` demasiado nueva/vieja; con Python 3.12, "
                "`wntr>=1.2,<2` funciona bien."
            )
