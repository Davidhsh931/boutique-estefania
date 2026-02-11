import streamlit as st
import mysql.connector
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inventario Estefania - Soles", layout="wide")

# --- DISEÑO PERSONALIZADO (SENTIMIENTO FEMENINO Y FUERTE) ---
st.markdown("""
    <style>
    /* Fondo y tipografía general */
    .main {
        background-color: #fcf8f8;
    }
    h1 {
        color: #8e44ad; /* Un toque de púrpura para la fuerza */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
    }
    
    /* Personalización de Tarjetas y Métricas */
    div[data-testid="stMetricValue"] {
        color: #d4a373; /* Oro suave */
        font-size: 32px;
    }
    
    /* Botones con estilo elegante */
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #d4a373;
        background-color: #ffffff;
        color: #8e44ad;
        transition: all 0.3s;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #8e44ad;
        color: white;
        border: 1px solid #8e44ad;
    }

    /* Estilo para el botón de descarga */
    .stDownloadButton>button {
        border-radius: 20px;
        background-color: #d4a373 !important;
        color: white !important;
        border: none;
        width: 100%;
    }

    /* Pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f5ecec;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        color: #5d4037;
    }
    .stTabs [aria-selected="true"] {
        background-color: #8e44ad !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. FUNCIÓN DE CONEXIÓN ---
def conectar():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"]["port"]
    )

# --- 2. SISTEMA DE LOGIN ---
def login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #8e44ad;'>✨ Bienvenida, Estefanía</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            user_input = st.text_input("Usuario")
            pass_input = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Entrar con Seguridad")
            
            if submit:
                if user_input == st.secrets["auth"]["usuario"] and pass_input == st.secrets["auth"]["clave"]:
                    st.session_state["logeado"] = True
                    st.rerun()
                else:
                    st.error("❌ Los datos no coinciden. Intenta de nuevo, tú puedes.")

# --- 3. CONTROL DE SESIÓN ---
if "logeado" not in st.session_state:
    st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    login()
else:
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["logeado"] = False
        st.rerun()

    st.title("👗 Sistema Integral - Boutique Estefania (S/.)")
    st.markdown("<p style='color: #a5a5a5;'>Tu esfuerzo construye tu futuro. Cada prenda cuenta.</p>", unsafe_allow_html=True)
    st.markdown("---")

    # --- BUSCADOR ---
    busqueda = st.text_input("🔍 ¿Qué prenda estás buscando hoy?")

    try:
        conn = conectar()
        cursor = conn.cursor()
        
        query = "SELECT id, tipo, marca, modelo, color, talla, inventario, precio_compra, precio_venta, unidades_vendidas, costo_total_compra FROM inventario_general WHERE estado = 'activo'"
        
        if busqueda:
            query += f" AND (tipo LIKE '%{busqueda}%' OR marca LIKE '%{busqueda}%' OR modelo LIKE '%{busqueda}%' OR color LIKE '%{busqueda}%')"
        
        df = pd.read_sql(query, conn)

        if not df.empty:
            st.subheader(f"📊 Tu Inventario Activo ({len(df)} registros)")

            def resaltar_stock(row):
                if row['inventario'] == 0:
                    return ['background-color: #ffcccc'] * len(row)
                elif 1 <= row['inventario'] <= 3:
                    return ['background-color: #fff3cd'] * len(row)
                else:
                    return [''] * len(row)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Inventario')
            processed_data = output.getvalue()

            st.download_button(
                label="📥 Respaldar todo mi Inventario en Excel",
                data=processed_data,
                file_name="inventario_estefania.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.dataframe(
                df.style.apply(resaltar_stock, axis=1).format({
                    "precio_compra": "S/ {:.2f}", 
                    "precio_venta": "S/ {:.2f}", 
                    "costo_total_compra": "S/ {:.2f}"
                }), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.warning("No se encontraron registros activos. ¡Es momento de agregar algo nuevo!")

        st.markdown("---")
        
        tab_add, tab_edit, tab_del, tab_papelera, tab_stats = st.tabs([
            "➕ Agregar Nuevo", 
            "📝 Editar Registro", 
            "🗑️ Mover a Papelera", 
            "♻️ Recuperar",
            "📊 Mi Progreso"
        ])

        with tab_add:
            st.subheader("Registrar nueva prenda con amor")
            with st.form("form_nuevo"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    v_tipo = st.text_input("Tipo:")
                    v_marca = st.text_input("Marca:")
                with c2:
                    v_modelo = st.text_input("Modelo:")
                    v_color = st.text_input("Color:")
                with c3:
                    v_talla = st.text_input("Talla:", value="S/T")
                    v_stock = st.number_input("Cantidad inicial:", min_value=0, step=1)
                
                c4, c5 = st.columns(2)
                with c4:
                    v_compra = st.number_input("Precio Compra (S/):", min_value=0.0, format="%.2f")
                with c5:
                    v_venta = st.number_input(f"Precio Venta (S/):", value=v_compra * 2, format="%.2f")
                
                if st.form_submit_button("🚀 Guardar en mi Sistema"):
                    if v_tipo and v_marca:
                        sql = """INSERT INTO inventario_general (tipo, marca, modelo, color, talla, inventario, precio_compra, precio_venta, estado) 
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'activo')"""
                        cursor.execute(sql, (v_tipo.upper(), v_marca.upper(), v_modelo.upper(), v_color.upper(), v_talla.upper(), v_stock, v_compra, v_venta))
                        conn.commit()
                        st.success("✅ ¡Listo! Prenda registrada con éxito.")
                        st.rerun()

        with tab_edit:
            id_editar = st.number_input("ID del producto a modificar:", min_value=0, step=1, key="ed")
            if id_editar > 0:
                prod = df[df['id'] == id_editar]
                if not prod.empty:
                    ce1, ce2, ce3 = st.columns(3)
                    with ce1:
                        n_tipo = st.text_input("Nuevo Tipo:", value=prod.iloc[0]['tipo'])
                        n_marca = st.text_input("Nueva Marca:", value=prod.iloc[0]['marca'])
                    with ce2:
                        n_modelo = st.text_input("Nuevo Modelo:", value=prod.iloc[0]['modelo'])
                        n_color = st.text_input("Nuevo Color:", value=prod.iloc[0]['color'])
                    with ce3:
                        n_talla = st.text_input("Nueva Talla:", value=prod.iloc[0]['talla'])
                        n_stock = st.number_input("Stock Actualizado:", value=int(prod.iloc[0]['inventario']))
                    
                    ce4, ce5 = st.columns(2)
                    with ce4:
                        n_compra = st.number_input("Nuevo Precio Compra (S/):", value=float(prod.iloc[0]['precio_compra']), format="%.2f")
                    with ce5:
                        n_venta = st.number_input("Nuevo Precio Venta (S/):", value=float(prod.iloc[0]['precio_venta']), format="%.2f")
                    
                    if st.button("💾 Actualizar mis Datos"):
                        sql = """UPDATE inventario_general SET tipo=%s, marca=%s, modelo=%s, color=%s, talla=%s, inventario=%s, precio_compra=%s, precio_venta=%s WHERE id=%s"""
                        cursor.execute(sql, (n_tipo.upper(), n_marca.upper(), n_modelo.upper(), n_color.upper(), n_talla.upper(), n_stock, n_compra, n_venta, id_editar))
                        conn.commit()
                        st.success("✅ Datos actualizados correctamente.")
                        st.rerun()

        with tab_del:
            st.info("ℹ️ Los productos en la papelera no afectan tu stock principal.")
            id_papelera = st.number_input("ID a mover a papelera:", min_value=0, step=1, key="to_pap")
            if st.button("🗑️ Enviar a Papelera"):
                cursor.execute("UPDATE inventario_general SET estado = 'papelera' WHERE id = %s", (id_papelera,))
                conn.commit()
                st.warning(f"Producto {id_papelera} movido.")
                st.rerun()

        with tab_papelera:
            st.subheader("♻️ Tu Papelera de Reciclaje")
            df_p = pd.read_sql("SELECT id, tipo, marca, modelo, color FROM inventario_general WHERE estado = 'papelera'", conn)
            
            if not df_p.empty:
                st.table(df_p)
                id_p_accion = st.number_input("ID para Restaurar o Eliminar:", min_value=0, step=1, key="p_acc")
                c_res, c_elim = st.columns(2)
                with c_res:
                    if st.button("✅ Restaurar a Inventario"):
                        cursor.execute("UPDATE inventario_general SET estado = 'activo' WHERE id = %s", (id_p_accion,))
                        conn.commit()
                        st.success("Producto restaurado con éxito.")
                        st.rerun()
                with c_elim:
                    confirmar = st.checkbox("Confirmar eliminación PERMANENTE")
                    if st.button("🔥 ELIMINAR DEFINITIVAMENTE") and confirmar:
                        cursor.execute("DELETE FROM inventario_general WHERE id = %s", (id_p_accion,))
                        conn.commit()
                        st.error("Producto eliminado para siempre.")
                        st.rerun()
            else:
                st.write("Tu papelera está limpia.")

        with tab_stats:
            st.subheader("📊 Resumen de tu Crecimiento")
            query_stats = """
                SELECT marca, 
                       COUNT(*) AS total_prendas, 
                       SUM(CASE WHEN precio_venta = 0 THEN 1 ELSE 0 END) AS por_completar
                FROM inventario_general 
                WHERE estado = 'activo'
                GROUP BY marca 
                ORDER BY total_prendas DESC;
            """
            df_stats = pd.read_sql(query_stats, conn)
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Marcas Aliadas", len(df_stats))
            col_m2.metric("Total Prendas", df_stats['total_prendas'].sum())
            col_m3.metric("Pendientes por Precio", df_stats['por_completar'].sum())

            st.dataframe(df_stats, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("🛠️ Unificar Nombres (Orden es Poder)")
            
            c_from, c_to = st.columns(2)
            with c_from:
                m_error = st.selectbox("Marca con error:", options=[""] + list(df_stats['marca'].unique()))
            with c_to:
                m_correcta = st.text_input("Nombre correcto:")
            
            if st.button("🔗 Unificar Marcas Ahora"):
                if m_error != "" and m_correcta != "":
                    cursor.execute("UPDATE inventario_general SET marca = %s WHERE marca = %s", (m_correcta.upper().strip(), m_error))
                    conn.commit()
                    st.success(f"✅ ¡Excelente! Todo unificado bajo '{m_correcta.upper()}'.")
                    st.rerun()

        conn.close()
    except Exception as e:
        st.error(f"❌ Un pequeño obstáculo: {e}")
