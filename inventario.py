import streamlit as st
import mysql.connector
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Boutique Estefanía - Gestión con Corazón", layout="wide")

# --- ESTILO FEMENINO Y PROFESIONAL (CSS CUSTOM) ---
st.markdown("""
    <style>
    /* Fondo y tipografía general */
    .main {
        background-color: #fcf8f8;
    }
    /* Títulos con elegancia */
    h1 {
        color: #8e44ad; /* Un toque de púrpura real */
        font-family: 'Playfair Display', serif;
        font-weight: 700;
        text-align: center;
    }
    h2, h3 {
        color: #a04000; /* Bronce/Dorado cálido */
    }
    /* Estilo para los botones */
    .stButton>button {
        background-color: #d2b4de; /* Lavanda suave */
        color: #4a235a;
        border-radius: 20px;
        border: 2px solid #bb8fce;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #bb8fce;
        color: white;
        transform: scale(1.05);
    }
    /* Estilo para el buscador y inputs */
    .stTextInput>div>div>input {
        border-radius: 15px;
        border: 1px solid #ebedef;
    }
    /* Tarjetas decorativas */
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 2px 2px 15px rgba(0,0,0,0.05);
        border-left: 5px solid #d2b4de;
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
        st.markdown("<h1 style='color: #5b2c6f;'>✨ Bienvenida, Estefanía</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #884ea0;'>Tu esfuerzo hoy es el éxito de mañana.</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            user_input = st.text_input("Usuario")
            pass_input = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Entrar con Seguridad")
            
            if submit:
                if user_input == st.secrets["auth"]["usuario"] and pass_input == st.secrets["auth"]["clave"]:
                    st.session_state["logeado"] = True
                    st.rerun()
                else:
                    st.error("❌ Los datos no coinciden. Inténtalo de nuevo, tú puedes.")

# --- 3. CONTROL DE SESIÓN ---
if "logeado" not in st.session_state:
    st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    login()
else:
    # Sidebar delicada
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>👑 Mi Panel</h2>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("Cerrar Sesión"):
            st.session_state["logeado"] = False
            st.rerun()

    st.markdown("<h1>👗 Boutique Estefanía: Inventario Real</h1>", unsafe_allow_html=True)
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
            st.subheader(f"💎 Tus Tesoros en Stock ({len(df)} prendas)")

            def resaltar_stock(row):
                if row['inventario'] == 0:
                    return ['background-color: #fadbd8'] * len(row) # Rosa alerta (Agotado)
                elif 1 <= row['inventario'] <= 3:
                    return ['background-color: #fef9e7'] * len(row) # Crema (Pocas unidades)
                else:
                    return [''] * len(row)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Inventario')
            processed_data = output.getvalue()

            st.download_button(
                label="📥 Respaldar mi Inventario en Excel",
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
            st.warning("No hay registros activos por ahora. ¡Es un buen momento para agregar algo nuevo!")

        st.markdown("---")
        
        # --- PESTAÑAS DE ACCIONES ---
        tab_add, tab_edit, tab_del, tab_papelera, tab_stats = st.tabs([
            "✨ Nueva Prenda", "📝 Editar", "🗑️ Papelera", "♻️ Recuperar", "📊 Mi Progreso"
        ])

        with tab_add:
            st.subheader("🌸 Registrar nueva pieza")
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
                    v_venta = st.number_input("Precio Venta (S/):", value=v_compra * 2, format="%.2f")
                
                if st.form_submit_button("🚀 ¡Añadir al Éxito!"):
                    if v_tipo and v_marca:
                        sql = """INSERT INTO inventario_general (tipo, marca, modelo, color, talla, inventario, precio_compra, precio_venta, estado) 
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'activo')"""
                        cursor.execute(sql, (v_tipo.upper(), v_marca.upper(), v_modelo.upper(), v_color.upper(), v_talla.upper(), v_stock, v_compra, v_venta))
                        conn.commit()
                        st.success("✅ ¡Listo! Una nueva oportunidad de venta.")
                        st.rerun()

        with tab_edit:
            id_editar = st.number_input("ID de la prenda a perfeccionar:", min_value=0, step=1, key="ed")
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
                        n_stock = st.number_input("Stock:", value=int(prod.iloc[0]['inventario']))
                    
                    ce4, ce5 = st.columns(2)
                    with ce4:
                        n_compra = st.number_input("Compra (S/):", value=float(prod.iloc[0]['precio_compra']), format="%.2f")
                    with ce5:
                        n_venta = st.number_input("Venta (S/):", value=float(prod.iloc[0]['precio_venta']), format="%.2f")
                    
                    if st.button("💾 Guardar Cambios"):
                        sql = """UPDATE inventario_general SET tipo=%s, marca=%s, modelo=%s, color=%s, talla=%s, inventario=%s, precio_compra=%s, precio_venta=%s WHERE id=%s"""
                        cursor.execute(sql, (n_tipo.upper(), n_marca.upper(), n_modelo.upper(), n_color.upper(), n_talla.upper(), n_stock, n_compra, n_venta, id_editar))
                        conn.commit()
                        st.success("✅ Datos actualizados correctamente.")
                        st.rerun()

        with tab_del:
            st.info("ℹ️ Mueve aquí lo que ya no está disponible para mantener tu espacio limpio.")
            id_papelera = st.number_input("ID para mover:", min_value=0, step=1, key="to_pap")
            if st.button("🗑️ Mover a la Papelera"):
                cursor.execute("UPDATE inventario_general SET estado = 'papelera' WHERE id = %s", (id_papelera,))
                conn.commit()
                st.warning(f"La prenda {id_papelera} ha sido apartada.")
                st.rerun()

        with tab_papelera:
            st.subheader("♻️ Zona de Recuperación")
            df_p = pd.read_sql("SELECT id, tipo, marca, modelo, color FROM inventario_general WHERE estado = 'papelera'", conn)
            if not df_p.empty:
                st.table(df_p)
                id_p_accion = st.number_input("ID de la prenda:", min_value=0, step=1, key="p_acc")
                c_res, c_elim = st.columns(2)
                with c_res:
                    if st.button("✅ Restaurar"):
                        cursor.execute("UPDATE inventario_general SET estado = 'activo' WHERE id = %s", (id_p_accion,))
                        conn.commit()
                        st.success("¡Vuelve al inventario!")
                        st.rerun()
                with c_elim:
                    confirmar = st.checkbox("Confirmar eliminación definitiva")
                    if st.button("🔥 ELIMINAR") and confirmar:
                        cursor.execute("DELETE FROM inventario_general WHERE id = %s", (id_p_accion,))
                        conn.commit()
                        st.error("Eliminado permanentemente.")
                        st.rerun()
            else:
                st.write("Tu papelera está limpia, como debe ser.")

        with tab_stats:
            st.subheader("📈 Resumen de tu Crecimiento")
            query_stats = """
                SELECT marca, COUNT(*) AS total_prendas, 
                SUM(CASE WHEN precio_venta = 0 THEN 1 ELSE 0 END) AS por_completar
                FROM inventario_general WHERE estado = 'activo'
                GROUP BY marca ORDER BY total_prendas DESC;
            """
            df_stats = pd.read_sql(query_stats, conn)
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Marcas Aliadas", len(df_stats))
            col_m2.metric("Stock Total", int(df_stats['total_prendas'].sum()))
            col_m3.metric("Pendientes", int(df_stats['por_completar'].sum()))

            st.dataframe(df_stats, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("🛠️ Unificar Nombres (Organización)")
            c_from, c_to = st.columns(2)
            with c_from:
                m_error = st.selectbox("Nombre con error:", options=[""] + list(df_stats['marca'].unique()))
            with c_to:
                m_correcta = st.text_input("Corregir por:")
            
            if st.button("🔗 Unificar Marcas"):
                if m_error != "" and m_correcta != "":
                    cursor.execute("UPDATE inventario_general SET marca = %s WHERE marca = %s", (m_correcta.upper().strip(), m_error))
                    conn.commit()
                    st.success(f"✅ ¡Excelente! Todo ordenado bajo '{m_correcta.upper()}'.")
                    st.rerun()

        conn.close()
    except Exception as e:
        st.error(f"❌ Estefanía, hubo un pequeño tropiezo: {e}")

