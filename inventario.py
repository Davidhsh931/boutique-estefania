import streamlit as st
import mysql.connector
import pandas as pd
from io import BytesIO

# --- 1. CONFIGURACIÓN Y ESTILO CUSTOM ---
st.set_page_config(page_title="Boutique Estefania - Admin", layout="wide", page_icon="👗")

# CSS para personalizar botones y fuentes
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    .stDownloadButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #28a745;
        color: white;
    }
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNCIONES CORE ---
def conectar():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"]["port"]
    )

def login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3050/3050239.png", width=100) # Icono de login
        st.title("🔐 Acceso Boutique")
        with st.form("login_form"):
            user_input = st.text_input("Usuario")
            pass_input = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar al Sistema"):
                if user_input == st.secrets["auth"]["usuario"] and pass_input == st.secrets["auth"]["clave"]:
                    st.session_state["logeado"] = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

# --- 3. LÓGICA DE NAVEGACIÓN ---
if "logeado" not in st.session_state:
    st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    login()
else:
    # Sidebar mejorada
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1164/1164620.png", width=100)
        st.title("Menú")
        st.write(f"Bienvenido, **{st.secrets['auth']['usuario'].capitalize()}**")
        if st.button("🚪 Cerrar Sesión"):
            st.session_state["logeado"] = False
            st.rerun()
        st.markdown("---")
        st.info("Sistema de Gestión v2.0")

    # Cuerpo Principal
    st.title("👗 Control de Inventario - Boutique Estefania")
    
    try:
        conn = conectar()
        df_all = pd.read_sql("SELECT * FROM inventario_general WHERE estado = 'activo'", conn)

        # KPIs arriba para impacto visual rápido
        c_kpi1, c_kpi2, c_kpi3, c_kpi4 = st.columns(4)
        with c_kpi1:
            st.metric("Prendas en Stock", int(df_all['inventario'].sum()))
        with c_kpi2:
            st.metric("Total Inversión", f"S/ { (df_all['inventario'] * df_all['precio_compra']).sum():,.2f}")
        with c_kpi3:
            st.metric("Venta Potencial", f"S/ { (df_all['inventario'] * df_all['precio_venta']).sum():,.2f}")
        with c_kpi4:
            st.metric("Modelos Activos", len(df_all))

        st.markdown("---")

        # Buscador y Tabla
        col_bus, col_btn = st.columns([3, 1])
        with col_bus:
            busqueda = st.text_input("🔍 Buscar por Marca, Tipo o Modelo...", placeholder="Ej: Vestido Gala")
        
        df_filtrado = df_all[df_all.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)] if busqueda else df_all

        # Colorear stock
        def color_stock(row):
            if row['inventario'] == 0: return ['background-color: #ff7675; color: white'] * len(row)
            if row['inventario'] <= 3: return ['background-color: #ffeaa7'] * len(row)
            return [''] * len(row)

        with col_btn:
            st.write("") # Espacio
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtrado.to_excel(writer, index=False)
            st.download_button("📥 Exportar Excel", output.getvalue(), "inventario.xlsx")

        st.dataframe(
            df_filtrado.style.apply(color_stock, axis=1).format({"precio_compra": "S/ {:.2f}", "precio_venta": "S/ {:.2f}", "costo_total_compra": "S/ {:.2f}"}),
            use_container_width=True, hide_index=True
        )

        # Pestañas con iconos
        st.markdown("<br>", unsafe_allow_html=True)
        t1, t2, t3, t4 = st.tabs(["✨ Nuevo Producto", "📝 Editar", "🗑️ Papelera", "📈 Análisis"])
        
        with t1:
            # Tu código de agregar producto aquí (se mantiene igual pero dentro de esta pestaña)
            st.subheader("Registrar mercadería nueva")
            # ... (resto de tu código de formularios)
            
        # ... (Resto de funciones de editar y borrar)

        conn.close()
    except Exception as e:
        st.error(f"Error de sistema: {e}")
