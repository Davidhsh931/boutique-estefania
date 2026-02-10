import streamlit as st
import mysql.connector
import pandas as pd

# --- CONEXIÓN A LA NUBE (CLEVER CLOUD) ---
def conectar():
    return mysql.connector.connect(
        host="b36qibv5gsdzkaheh8ur-mysql.services.clever-cloud.com",
        user="ukqcyv38ljdothuh",
        password="N1JQSHXWVAKn8DI1dZO5", # <--- Pon la clave de Clever Cloud aquí
        database="b36qibv5gsdzkaheh8ur",
        port=3306
    )

# ... El resto de tu código Streamlit sigue igual ...

st.set_page_config(page_title="Inventario Estefania - Soles", layout="wide")

st.title("👗 Sistema Integral - Boutique Estefania (S/.)")
st.markdown("---")

# --- BUSCADOR ---
busqueda = st.text_input("🔍 Buscar en el Inventario Activo (Tipo, Marca, Modelo, Color):")

try:
    conn = conectar()
    cursor = conn.cursor()
    
    # 1. CONSULTA PRINCIPAL (Solo registros activos)
    query = "SELECT id, tipo, marca, modelo, color, talla, inventario, precio_compra, precio_venta, unidades_vendidas, costo_total_compra FROM inventario_general WHERE estado = 'activo'"
    
    if busqueda:
        query += f" AND (tipo LIKE '%{busqueda}%' OR marca LIKE '%{busqueda}%' OR modelo LIKE '%{busqueda}%' OR color LIKE '%{busqueda}%')"
    
    df = pd.read_sql(query, conn)

    if not df.empty:
        st.subheader(f"📊 Stock Actual ({len(df)} registros)")
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
        "➕ Agregar Nuevo", 
        "📝 Editar Existente", 
        "🗑️ Mover a Papelera", 
        "♻️ Ver Papelera",
        "📊 Reportes y Limpieza"
    ])

    # --- 1. AGREGAR NUEVO ---
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
                    sql = """INSERT INTO inventario_general (tipo, marca, modelo, color, talla, inventario, precio_compra, precio_venta, estado) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'activo')"""
                    cursor.execute(sql, (v_tipo.upper(), v_marca.upper(), v_modelo.upper(), v_color.upper(), v_talla.upper(), v_stock, v_compra, v_venta))
                    conn.commit()
                    st.success("✅ Agregado con éxito!")
                    st.rerun()

    # --- 2. EDITAR EXISTENTE ---
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
                
                if st.button("💾 Actualizar Datos"):
                    sql = """UPDATE inventario_general SET tipo=%s, marca=%s, modelo=%s, color=%s, talla=%s, inventario=%s, precio_compra=%s, precio_venta=%s WHERE id=%s"""
                    cursor.execute(sql, (n_tipo.upper(), n_marca.upper(), n_modelo.upper(), n_color.upper(), n_talla.upper(), n_stock, n_compra, n_venta, id_editar))
                    conn.commit()
                    st.success("✅ Cambios guardados.")
                    st.rerun()

    # --- 3. MOVER A PAPELERA ---
    with tab_del:
        st.info("ℹ️ Al mover a la papelera, el producto dejará de aparecer en el inventario activo.")
        id_papelera = st.number_input("ID a mover a papelera:", min_value=0, step=1, key="to_pap")
        if st.button("🗑️ Mover a Papelera"):
            cursor.execute("UPDATE inventario_general SET estado = 'papelera' WHERE id = %s", (id_papelera,))
            conn.commit()
            st.warning(f"Producto {id_papelera} enviado a la papelera.")
            st.rerun()

    # --- 4. PAPELERA DE RECICLAJE ---
    with tab_papelera:
        st.subheader("♻️ Papelera de Reciclaje")
        df_p = pd.read_sql("SELECT id, tipo, marca, modelo, color FROM inventario_general WHERE estado = 'papelera'", conn)
        
        if not df_p.empty:
            st.table(df_p)
            id_p_accion = st.number_input("ID para Restaurar o Eliminar:", min_value=0, step=1, key="p_acc")
            c_res, c_elim = st.columns(2)
            with c_res:
                if st.button("✅ Restaurar a Inventario"):
                    cursor.execute("UPDATE inventario_general SET estado = 'activo' WHERE id = %s", (id_p_accion,))
                    conn.commit()
                    st.success("Producto restaurado.")
                    st.rerun()
            with c_elim:
                confirmar = st.checkbox("Confirmar eliminación PERMANENTE")
                if st.button("🔥 ELIMINAR DE VERDAD") and confirmar:
                    cursor.execute("DELETE FROM inventario_general WHERE id = %s", (id_p_accion,))
                    conn.commit()
                    st.error("Producto eliminado definitivamente.")
                    st.rerun()
        else:
            st.write("La papelera está vacía.")

    # --- 5. REPORTES Y HERRAMIENTA DE LIMPIEZA ---
    with tab_stats:
        st.subheader("📊 Resumen General por Marcas")
        
        # Consulta de estadísticas
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
        col_m1.metric("Marcas Distintas", len(df_stats))
        col_m2.metric("Prendas Totales", df_stats['total_prendas'].sum())
        col_m3.metric("Faltan Precios", df_stats['por_completar'].sum())

        st.dataframe(df_stats, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🛠️ Unificar Marcas (Corrección de Nombres)")
        st.write("Selecciona un nombre mal escrito y escribe el nombre original para unificarlos.")
        
        c_from, c_to = st.columns(2)
        with c_from:
            m_error = st.selectbox("Marca con error (Ej: PIONER):", options=[""] + list(df_stats['marca'].unique()))
        with c_to:
            m_correcta = st.text_input("Cambiar por Nombre Original (Ej: PIONIER):")
        
        if st.button("🔗 Unificar Ahora"):
            if m_error != "" and m_correcta != "":
                cursor.execute(
                    "UPDATE inventario_general SET marca = %s WHERE marca = %s",
                    (m_correcta.upper().strip(), m_error)
                )
                conn.commit()
                st.success(f"✅ ¡Hecho! Todos los registros de '{m_error}' ahora son '{m_correcta.upper()}'.")
                st.rerun()
            else:
                st.error("Por favor, selecciona una marca y escribe el nombre correcto.")

    conn.close()
except Exception as e:
    st.error(f"❌ Error: {e}")