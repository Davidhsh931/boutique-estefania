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
            
            # --- FUNCIÓN PARA COLOREAR STOCK ---
            def resaltar_stock(row):
                if row['inventario'] == 0:
                    return ['background-color: #ffcccc'] * len(row) # Rojo: Agotado
                elif 1 <= row['inventario'] <= 3:
                    return ['background-color: #fff3cd'] * len(row) # Amarillo: Crítico
                else:
                    return [''] * len(row)

            # --- BOTÓN DE EXCEL ---
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

            # --- VISTA DE TABLA ---
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

        with tab_edit:
            id_editar = st.number_input("ID del producto a modificar:", min_value=0, step=1)
            if id_editar > 0 and not df.empty:
                prod = df[df['id'] == id_editar]
                if not prod.empty:
                    with st.form("form_edit"):
                        ce1, ce2 = st.columns(2)
                        n_stock = ce1.number_input("Nuevo Stock:", value=int(prod.iloc[0]['inventario']))
                        n_venta = ce2.number_input("Nuevo Precio Venta (S/):", value=float(prod.iloc[0]['precio_venta']))
                        if st.form_submit_button("💾 Guardar Cambios"):
                            cursor = conn.cursor()
                            cursor.execute("UPDATE inventario_general SET inventario=%s, precio_venta=%s WHERE id=%s", (n_stock, n_venta, id_editar))
                            conn.commit()
                            st.success("Actualizado")
                            st.rerun()

        with tab_del:
            id_borrar = st.number_input("ID para mover a papelera:", min_value=0, step=1, key="del_id")
            if st.button("🗑️ Confirmar Movimiento"):
                cursor = conn.cursor()
                cursor.execute("UPDATE inventario_general SET estado='papelera' WHERE id=%s", (id_borrar,))
                conn.commit()
                st.rerun()

        with tab_papelera:
            df_pap = pd.read_sql("SELECT id, tipo, marca, modelo FROM inventario_general WHERE estado='papelera'", conn)
            st.table(df_pap)
            id_res = st.number_input("ID para restaurar:", min_value=0, step=1)
            if st.button("♻️ Restaurar"):
                cursor = conn.cursor()
                cursor.execute("UPDATE inventario_general SET estado='activo' WHERE id=%s", (id_res,))
                conn.commit()
                st.rerun()

        with tab_stats:
            st.subheader("💰 Resumen Financiero")
            total_inv = (df['inventario'] * df['precio_compra']).sum()
            potencial = (df['inventario'] * df['precio_venta']).sum()
            st.metric("Inversión Total en Stock", f"S/ {total_inv:,.2f}")
            st.metric("Venta Potencial Total", f"S/ {potencial:,.2f}")

        conn.close()
    except Exception as e:
        st.error(f"❌ Error: {e}")
