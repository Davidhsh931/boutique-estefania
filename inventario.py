import streamlit as st
import mysql.connector
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Boutique Estefania", layout="wide")

# --- DISEÑO FEMENINO Y FUERTE (CSS) ---
st.markdown("""
    <style>
    /* Fondo y fuentes */
    .stApp {
        background-color: #fffafb;
    }
    h1 {
        color: #8e44ad; /* Un toque de purpura real */
        font-family: 'Playfair Display', serif;
        font-weight: 700;
        text-align: center;
        border-bottom: 2px solid #e0b0ff;
        padding-bottom: 10px;
    }
    .stSubheader {
        color: #a04058;
        font-weight: 600;
    }
    /* Estilo de botones */
    .stButton>button {
        background-color: #d4a5a5;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 25px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #a04058;
        color: white;
        transform: scale(1.05);
    }
    /* Tarjetas de métricas */
    [data-testid="stMetricValue"] {
        color: #a04058;
    }
    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f8ecec;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        color: #a04058;
    }
    .stTabs [aria-selected="true"] {
        background-color: #d4a5a5 !important;
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
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='border:none;'>🌸 Bienvenida, Estefanía</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("<p style='text-align:center; color: #a04058;'>Tu esfuerzo es el motor de este sueño.</p>", unsafe_allow_html=True)
            user_input = st.text_input("Usuario")
            pass_input = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Iniciar Sesión con Orgullo")
            
            if submit:
                if user_input == st.secrets["auth"]["usuario"] and pass_input == st.secrets["auth"]["clave"]:
                    st.session_state["logeado"] = True
                    st.rerun()
                else:
                    st.error("❌ Los detalles no coinciden, inténtalo de nuevo mujer valiente.")

# --- 3. CONTROL DE SESIÓN ---
if "logeado" not in st.session_state:
    st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    login()
else:
    # Sidebar elegante
    st.sidebar.markdown(f"<h2 style='color:#a04058;'>💖 Boutique Admin</h2>", unsafe_allow_html=True)
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["logeado"] = False
        st.rerun()

    st.title("👗 Mi Legado - Boutique Estefania")
    
    # --- BUSCADOR ---
    with st.container():
        busqueda = st.text_input("🔍 ¿Qué tesoro estamos buscando hoy? (Tipo, Marca, Modelo):")

    try:
        conn = conectar()
        cursor = conn.cursor()
        
        query = "SELECT id, tipo, marca, modelo, color, talla, inventario, precio_compra, precio_venta, unidades_vendidas, costo_total_compra FROM inventario_general WHERE estado = 'activo'"
        if busqueda:
            query += f" AND (tipo LIKE '%{busqueda}%' OR marca LIKE '%{busqueda}%' OR modelo LIKE '%{busqueda}%' OR color LIKE '%{busqueda}%')"
        
        df = pd.read_sql(query, conn)

        if not df.empty:
            # --- SEMÁFORO DE COLORES ---
            def resaltar_stock(row):
                if row['inventario'] == 0:
                    return ['background-color: #fce4ec'] * len(row) # Rosa pálido (Agotado)
                elif 1 <= row['inventario'] <= 3:
                    return ['background-color: #fff9c4'] * len(row) # Crema (Poco stock)
                else:
                    return [''] * len(row)
            
            # --- PREPARACIÓN EXCEL ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Inventario')
            processed_data = output.getvalue()

            col_btn, col_info = st.columns([1, 3])
            with col_btn:
                st.download_button(
                    label="📥 Exportar mi Inventario",
                    data=processed_data,
                    file_name="mi_inventario_estefania.xlsx",
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
            st.warning("Aún no hay registros en esta sección. ¡Vamos a crear algo nuevo!")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- PESTAÑAS ---
        tab_add, tab_edit, tab_del, tab_papelera, tab_stats = st.tabs([
            "✨ Nueva Prenda", "📝 Perfeccionar Datos", "📥 Archivar", "♻️ Recuperar", "📈 Mis Logros"
        ])

        with tab_add:
            st.subheader("Añadir nueva pieza al catálogo")
            with st.form("form_nuevo"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    v_tipo = st.text_input("Categoría:")
                    v_marca = st.text_input("Marca:")
                with c2:
                    v_modelo = st.text_input("Modelo:")
                    v_color = st.text_input("Color:")
                with c3:
                    v_talla = st.text_input("Talla:", value="S/T")
                    v_stock = st.number_input("Cantidad inicial:", min_value=0, step=1)
                
                c4, c5 = st.columns(2)
                with c4:
                    v_compra = st.number_input("Inversión por prenda (S/):", min_value=0.0, format="%.2f")
                with c5:
                    v_venta = st.number_input(f"Precio de Venta Sugerido (S/):", value=v_compra * 2, format="%.2f")
                
                if st.form_submit_button("🚀 Hacer crecer mi negocio"):
                    if v_tipo and v_marca:
                        sql = "INSERT INTO inventario_general (tipo, marca, modelo, color, talla, inventario, precio_compra, precio_venta, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'activo')"
                        cursor.execute(sql, (v_tipo.upper(), v_marca.upper(), v_modelo.upper(), v_color.upper(), v_talla.upper(), v_stock, v_compra, v_venta))
                        conn.commit()
                        st.success("✅ ¡Registrado! Cada paso cuenta.")
                        st.rerun()

        with tab_edit:
            id_editar = st.number_input("ID de la prenda a editar:", min_value=0, step=1)
            if id_editar > 0:
                prod = df[df['id'] == id_editar]
                if not prod.empty:
                    ce1, ce2, ce3 = st.columns(3)
                    with ce1:
                        n_tipo = st.text_input("Categoría:", value=prod.iloc[0]['tipo'])
                        n_marca = st.text_input("Marca:", value=prod.iloc[0]['marca'])
                    with ce2:
                        n_modelo = st.text_input("Modelo:", value=prod.iloc[0]['modelo'])
                        n_color = st.text_input("Color:", value=prod.iloc[0]['color'])
                    with ce3:
                        n_talla = st.text_input("Talla:", value=prod.iloc[0]['talla'])
                        n_stock = st.number_input("Stock:", value=int(prod.iloc[0]['inventario']))
                    
                    if st.button("💾 Guardar Cambios"):
                        sql = "UPDATE inventario_general SET tipo=%s, marca=%s, modelo=%s, color=%s, talla=%s, inventario=%s WHERE id=%s"
                        cursor.execute(sql, (n_tipo.upper(), n_marca.upper(), n_modelo.upper(), n_color.upper(), n_talla.upper(), n_stock, id_editar))
                        conn.commit()
                        st.success("✅ Información actualizada.")
                        st.rerun()

        with tab_del:
            st.info("¿Deseas mover este artículo a la papelera?")
            id_papelera = st.number_input("ID del producto:", min_value=0, step=1, key="to_pap")
            if st.button("🗑️ Mover a Papelera"):
                cursor.execute("UPDATE inventario_general SET estado = 'papelera' WHERE id = %s", (id_papelera,))
                conn.commit()
                st.rerun()

        with tab_papelera:
            st.subheader("♻️ Artículos en reserva")
            df_p = pd.read_sql("SELECT id, tipo, marca, modelo FROM inventario_general WHERE estado = 'papelera'", conn)
            if not df_p.empty:
                st.table(df_p)
                id_p_accion = st.number_input("ID para Restaurar o Eliminar:", min_value=0, step=1)
                c_res, c_elim = st.columns(2)
                with c_res:
                    if st.button("✅ Restaurar"):
                        cursor.execute("UPDATE inventario_general SET estado = 'activo' WHERE id = %s", (id_p_accion,))
                        conn.commit()
                        st.rerun()
                with c_elim:
                    if st.checkbox("Confirmar eliminación final"):
                        if st.button("🔥 Eliminar"):
                            cursor.execute("DELETE FROM inventario_general WHERE id = %s", (id_p_accion,))
                            conn.commit()
                            st.rerun()

        with tab_stats:
            st.subheader("📈 Resumen de mi Crecimiento")
            query_stats = "SELECT marca, COUNT(*) AS total_prendas FROM inventario_general WHERE estado = 'activo' GROUP BY marca ORDER BY total_prendas DESC"
            df_stats = pd.read_sql(query_stats, conn)
            
            c_m1, c_m2 = st.columns(2)
            c_m1.metric("Marcas que manejo", len(df_stats))
            c_m2.metric("Prendas totales", df_stats['total_prendas'].sum())
            st.dataframe(df_stats, use_container_width=True)

        conn.close()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
