import streamlit as st
from io import BytesIO
from coordenadas import main
import coordenadas
import kmz_to_cad
import cartografia

def mostrar_pagina_principal():
    st.title("Menú Principal")

    # Crear botones para navegar entre scripts
    if st.button("Ejecutar Script de Extracción de Coordenadas"):
        st.session_state.pagina_actual = "coordenadas"
    if st.button("Generar cartografia cali"):
        st.session_state.pagina_actual = "cartografia"
        
    elif st.button("Ejecutar Script para generar DXF"):
        st.session_state.pagina_actual = "dxf"
      
        

# Inicializar el estado de la página si no existe
if 'pagina_actual' not in st.session_state:
    st.session_state.pagina_actual = "principal"  # Valor inicial es la página principal

# Mostrar la página correspondiente según el estado
if st.session_state.pagina_actual == "principal":
    mostrar_pagina_principal()
elif st.session_state.pagina_actual == "coordenadas":
    coordenadas.main()  # Ejecutamos solo la función
elif st.session_state.pagina_actual == "dxf":
    kmz_to_cad.main()  # Ejecutamos solo la función
elif st.session_state.pagina_actual == "cartografia":
    cartografia.main()
