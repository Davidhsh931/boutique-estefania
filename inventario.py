import streamlit as st
import mysql.connector
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inventario Estefania - Soles", layout="wide")

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
        st.title("🔐 Acceso al Sistema")
        with st.form("login_form"):
            user_input = st.text_input("Usuario")
            pass_input = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Entrar")
            
            if submit:
                if user_input == st.secrets["auth"]["usuario"] and pass_input == st.secrets["auth"]["clave"]:
                    st.session_state["logeado"] = True
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")

# --- 3. CONTROL DE SESIÓN ---
if "logeado" not in st.session_state:
    st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    login()
else:
    # Botón lateral para salir
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["logeado"] = False
        st.rerun()

    st.title("👗 Sistema Integral - Boutique Estefania (S/.)")
    st.markdown("---")

    # --- BUSCADOR ---
    busqueda = st.text_input("🔍 Buscar en el Inventario Activo (Tipo, Marca, Modelo, Color):")

    try:
        conn = conectar()
        
        # 1. CONSULTA PRINCIPAL
        query = "SELECT id, tipo, marca, modelo, color, talla, inventario, precio_compra, precio_venta, unidades_vendidas, costo_total_compra FROM inventario_general WHERE estado = 'activo'"
        
        if busqueda:
            query += f" AND (tipo LIKE '%{busqueda}%' OR marca LIKE '%{busqueda}%' OR modelo LIKE '%{busqueda}%' OR color LIKE '%{busqueda}%')"
        
        df = pd.read_sql(query, conn)

        if not df.empty:
            st.subheader(f"📊 Stock Actual ({len(df)} registros)")
            
            # --- BOTÓN DE EXCEL ---
            # Preparamos el archivo en memoria
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Inventario')
            processed_data = output.getvalue()

            st.download_button(
                label="📥 Descargar Inventario en Excel",
                data=processed_data,
                file_name="inventario_estefania.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.dataframe(df.style.format({
                "precio_compra": "S/ {:.2f}", 
                "precio_venta": "S/ {:.2f}", 
                "costo_total_compra": "S/ {:.2f}"
            }), use_container_width=True, hide_index=True)
        else:
            st.warning("No se encontraron registros activos.")

        st.markdown("---")
        
        # --- PESTAÑAS DE ACCIONES ---
        tab_add, tab_edit, tab_del, tab_papelera, tab_stats = st.tabs([
            "➕ Agregar Nuevo", "📝 Editar Existente", "🗑️ Mover a Papelera", "♻️ Ver Papelera", "📊 Reportes"
        ])

        with tab_add:
            st.subheader("Registrar nueva prenda")
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
                    v_compra = st.number_input("Precio Compra Unitario (S/):", min_value=0.0, format="%.2f")
                with c5:
                    v_venta = st.number_input(f"Precio Venta (S/):", value=v_compra * 2, format="%.2f")
                
                if st.form_submit_button("🚀 Registrar en Inventario"):
                    if v_tipo and v_marca:
                        cursor = conn.cursor()
                        sql = """INSERT INTO inventario_general (tipo, marca, modelo, color, talla, inventario, precio_compra, precio_venta, estado) 
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'activo')"""
                        cursor.execute(sql, (v_tipo.upper(), v_marca.upper(), v_modelo.upper(), v_color.upper(), v_talla.upper(), v_stock, v_compra, v_venta))
                        conn.commit()
                        st.success("✅ Agregado con éxito!")
                        st.rerun()

        # (El resto de las pestañas Editar, Papelera y Stats se mantienen igual que antes...)
        # Nota: Por espacio omití el detalle interno, pero asegúrate de mantener 
        # las mismas funciones de UPDATE y DELETE que ya tenías funcionando.

        conn.close()
    except Exception as e:
        st.error(f"❌ Error: {e}")
