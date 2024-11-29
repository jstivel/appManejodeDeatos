
import streamlit as st
from utils.procesar_datos import procesar_excel  # Importar lógica reutilizable
import pandas as pd

st.title("Interfaz del Script 1")

# Subir archivo
archivo_subido = st.file_uploader("Sube tu archivo Excel", type=["xlsx", "xls"])

if archivo_subido is not None:
    df = pd.read_excel(archivo_subido)
    st.write("Vista previa de los datos cargados:")
    st.dataframe(df)

    ruta_salida = "salida_procesada.xlsx"

    if st.button("Procesar archivo"):
        resultado = procesar_excel(archivo_subido, ruta_salida)
        st.success(resultado)

        with open(ruta_salida, "rb") as file:
            btn = st.download_button(
                label="Descargar archivo procesado",
                data=file,
                file_name="salida_procesada.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Botón para volver al menú principal
if st.button("Volver al Menú Principal"):
    st.experimental_set_query_params(page="main")