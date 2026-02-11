import streamlit as st
import mysql.connector
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inventario Estefania - Soles", layout="wide")

# --- DISEÑO FEMENINO Y FUERTE (CSS PERSONALIZADO) ---
st.markdown("""
    <style>
    /* Fondo y tipografía general */
    .main {
        background-color: #fcf8f8;
    }
    
    /* Estilo para los títulos */
    h1 {
        color: #8e44ad !important; /* Un toque de púrpura real para el liderazgo */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
    }
    
    /* Estilo de los botones (Fuerza y Elegancia) */
    .stButton>button {
        background-color: #d4a373; /* Dorado tierra */
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 25px;
        font-weight: bold;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #b08968;
        border: 1px solid #d4a373;
        transform: scale(1.05);
    }

    /* Tabs (Pestañas) con estilo suave */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f7ebeb;
        padding: 10px;
        border-radius: 15px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 10px;
        background-color: white;
        color: #6d597a;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background-color: #b56576 !important; /* Rosa fuerte protector */
        color: white !important;
    }

    /* Tarjetas de métricas */
    [data-testid="stMetricValue"] {
        color: #b56576;
    }
    
    /* Personalización del buscador */
    .stTextInput>div>div>input {
        border-radius: 15px;
        border: 1px solid #e5d4d4;
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
        st.markdown("<h1 style='text-align: center;'>👑 Estefanía Boutique</h1>", unsafe_allow_html=True)
        st.subheader("Acceso al Sistema")
        with st.form("login_form"):
            user_input = st.text_input("Usuario")
            pass_input = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Entrar con Seguridad")
            
            if submit:
                if user_input == st.secrets["auth"]["usuario"] and pass_input == st.secrets["auth"]["clave"]:
                    st.session_state["logeado"] = True
                    st.rerun()
                else:
                    st.error("❌ Los datos no coinciden, inténtalo de nuevo con calma.")

# --- 3. CONTROL DE SESIÓN ---
if "logeado" not in st.session_state:
    st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    login()
else:
    # Botón lateral para salir
    if st.sidebar.button("🔒 Salir Segura"):
        st.session_state["logeado"] = False
        st.rerun()

    st.title("👗 Sistema Integral - Boutique Estefania (S/.)")
    st.markdown("<p style='color: #6d597a; font-style: italic;'>'Una mujer con visión es imparable'</p>", unsafe_allow_html=True)
    st.markdown("---")

    # --- BUSCADOR ---
    busqueda = st.text_input("🔍 ¿Qué prenda estás buscando hoy? (Tipo, Marca, Modelo):")

    try:
        conn = conectar()
        cursor = conn.cursor()
        
        query = "SELECT id, tipo, marca, modelo, color, talla, inventario, precio_compra, precio_venta, unidades_vendidas, costo_total_compra FROM inventario_general WHERE estado = 'activo'"
        
        if busqueda:
            query += f" AND (tipo LIKE '%{busqueda}%' OR marca LIKE '%{busqueda}%' OR modelo LIKE '%{busqueda}%' OR color LIKE '%{busqueda}%')"
        
        df = pd.read_sql(query, conn)

        if not df.empty:
            st.subheader(f"📊 Tu Inventario Actual ({len(df)} prendas)")

            def resaltar_stock(row):
                if row['inventario'] == 0:
                    return ['background-color: #fad2d2'] * len(row) # Rojo pastel suave
                elif 1 <= row['inventario'] <= 3:
                    return ['background-color: #fdf2d9'] * len(row) # Crema/Naranja suave
                else:
                    return [''] * len(row)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Inventario')
            processed_data = output.getvalue()

            st.download_button(
                label="📥 Respaldar Inventario en Excel",
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
            st.warning("Aún no tienes registros con esas características.")

        st.markdown("---")
        
        tab_add, tab_edit, tab_del, tab_papelera, tab_stats = st.tabs([
            "➕ Nueva Prenda", "📝 Corregir Datos", "🗑️ Mover a Papelera", "♻️ Ver Papelera", "📊 Reportes de Poder"
        ])

        with tab_add:
            st.subheader("Registrar nueva pieza")
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
                    v_stock = st.number_input("¿Cuántas llegaron?:", min_value=0, step=1)
                
                c4, c5 = st.columns(2)
                with c4:
                    v_compra = st.number_input("Precio Compra (S/):", min_value=0.0, format="%.2f")
                with c5:
                    v_venta = st.number_input(f"Precio Sugerido Venta (S/):", value=v_compra * 2, format="%.2f")
                
                if st.form_submit_button("🚀 Añadir con Éxito"):
                    if v_tipo and v_marca:
                        sql = "INSERT INTO inventario_general (tipo, marca, modelo, color, talla, inventario, precio_compra, precio_venta, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'activo')"
                        cursor.execute(sql, (v_tipo.upper(), v_marca.upper(), v_modelo.upper(), v_color.upper(), v_talla.upper(), v_stock, v_compra, v_venta))
                        conn.commit()
                        st.success("✅ ¡Lista para la venta!")
                        st.rerun()

        with tab_edit:
            id_editar = st.number_input("ID de la prenda a editar:", min_value=0, step=1, key="ed")
            if id_editar > 0:
                prod = df[df['id'] == id_editar]
                if not prod.empty:
                    ce1, ce2, ce3 = st.columns(3)
                    with ce1:
                        n_tipo = st.text_input("Tipo:", value=prod.iloc[0]['tipo'])
                        n_marca = st.text_input("Marca:", value=prod.iloc[0]['marca'])
                    with ce2:
                        n_modelo = st.text_input("Modelo:", value=prod.iloc[0]['modelo'])
                        n_color = st.text_input("Color:", value=prod.iloc[0]['color'])
                    with ce3:
                        n_talla = st.text_input("Talla:", value=prod.iloc[0]['talla'])
                        n_stock = st.number_input("Stock Real:", value=int(prod.iloc[0]['inventario']))
                    
                    ce4, ce5 = st.columns(2)
                    with ce4:
                        n_compra = st.number_input("Precio Compra (S/):", value=float(prod.iloc[0]['precio_compra']), format="%.2f")
                    with ce5:
                        n_venta = st.number_input("Precio Venta (S/):", value=float(prod.iloc[0]['precio_venta']), format="%.2f")
                    
                    if st.button("💾 Guardar Cambios"):
                        sql = "UPDATE inventario_general SET tipo=%s, marca=%s, modelo=%s, color=%s, talla=%s, inventario=%s, precio_compra=%s, precio_venta=%s WHERE id=%s"
                        cursor.execute(sql, (n_tipo.upper(), n_marca.upper(), n_modelo.upper(), n_color.upper(), n_talla.upper(), n_stock, n_compra, n_venta, id_editar))
                        conn.commit()
                        st.success("✅ Todo actualizado.")
                        st.rerun()

        with tab_del:
            st.info("ℹ️ Esto ocultará la prenda del stock principal.")
            id_papelera = st.number_input("ID para mover a papelera:", min_value=0, step=1, key="to_pap")
            if st.button("🗑️ Mover"):
                cursor.execute("UPDATE inventario_general SET estado = 'papelera' WHERE id = %s", (id_papelera,))
                conn.commit()
                st.warning(f"La prenda {id_papelera} ha sido movida.")
                st.rerun()

        with tab_papelera:
            st.subheader("♻️ Papelera")
            df_p = pd.read_sql("SELECT id, tipo, marca, modelo, color FROM inventario_general WHERE estado = 'papelera'", conn)
            if not df_p.empty:
                st.table(df_p)
                id_p_accion = st.number_input("ID para actuar:", min_value=0, step=1, key="p_acc")
                c_res, c_elim = st.columns(2)
                with c_res:
                    if st.button("✅ Restaurar"):
                        cursor.execute("UPDATE inventario_general SET estado = 'activo' WHERE id = %s", (id_p_accion,))
                        conn.commit()
                        st.rerun()
                with c_elim:
                    confirmar = st.checkbox("Confirmar borrado definitivo")
                    if st.button("🔥 Eliminar") and confirmar:
                        cursor.execute("DELETE FROM inventario_general WHERE id = %s", (id_p_accion,))
                        conn.commit()
                        st.rerun()

        with tab_stats:
            st.subheader("📊 Cómo va tu negocio")
            query_stats = "SELECT marca, COUNT(*) AS total_prendas, SUM(CASE WHEN precio_venta = 0 THEN 1 ELSE 0 END) AS por_completar FROM inventario_general WHERE estado = 'activo' GROUP BY marca ORDER BY total_prendas DESC;"
            df_stats = pd.read_sql(query_stats, conn)
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Marcas que manejas", len(df_stats))
            col_m2.metric("Prendas en total", df_stats['total_prendas'].sum())
            col_m3.metric("Pendientes de precio", df_stats['por_completar'].sum())

            st.dataframe(df_stats, use_container_width=True, hide_index=True)

        conn.close()
    except Exception as e:
        st.error(f"❌ Error: {e}")
