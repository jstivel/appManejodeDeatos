import os
import zipfile
import xml.etree.ElementTree as ET
from openpyxl import Workbook
import utm
import streamlit as st
from io import BytesIO
import tempfile

def main():
    st.title("Extracción de Coordenadas de Archivos KMZ")

    # Botón para volver al menú principal
    if st.button("Volver al Menú Principal"):
        st.session_state.pagina_actual = "principal"

    # Cargar archivo KMZ
    kmz_file = st.file_uploader("Cargar archivo KMZ", type=["kmz"])
    formato_salida = st.selectbox("Seleccionar formato de salida", ["UTM", "GMS", "Decimal"])

    # Botón para procesar el archivo
    if kmz_file and formato_salida:
        if st.button("Generar archivo de coordenadas"):
            try:
                # Extraer coordenadas del archivo KMZ
                coordenadas = extraer_coordenadas_de_kmz(kmz_file, formato_salida)

                # Crear archivo de salida en formato Excel
                with BytesIO() as output:
                    guardar_coordenadas_en_excel(coordenadas, output, formato_salida)
                    output.seek(0)

                    # Descargar archivo generado
                    st.download_button(
                        label="Descargar archivo de coordenadas",
                        data=output,
                        file_name=f"coordenadas_{kmz_file.name}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.success("Archivo generado y listo para descargar.")
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

def extraer_coordenadas_de_kmz(kmz_file, formato_salida):
    # Usar un directorio temporal para descomprimir el KMZ
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(kmz_file, 'r') as kmz:
            kmz.extractall(temp_dir)

        # Buscar el archivo KML dentro del KMZ
        kml_file = [f for f in os.listdir(temp_dir) if f.endswith('.kml')][0]
        kml_path = os.path.join(temp_dir, kml_file)

        tree = ET.parse(kml_path)
        root = tree.getroot()
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}

        coordenadas = []

        # Extraer las coordenadas de los Placemark
        for placemark in root.findall('.//kml:Placemark', ns):
            name = placemark.find('.//kml:name', ns)
            coords = placemark.find('.//kml:coordinates', ns)
            if coords is not None:
                for coord in coords.text.strip().split():
                    x, y, _ = coord.split(',')  # Descartar la altitud
                    x, y = float(x), float(y)

                    # Convertir las coordenadas según el formato solicitado
                    if formato_salida == "UTM":
                        coord_este, coord_norte, zona = convertir_a_utm(x, y)
                        coordenadas.append((name.text if name is not None else "Sin nombre", zona, coord_este, coord_norte))
                    elif formato_salida == "GMS":
                        lat_gms, lon_gms = convertir_a_gms(x, y)
                        coordenadas.append((name.text if name is not None else "Sin nombre", lat_gms, lon_gms))
                    else:
                        coordenadas.append((name.text if name is not None else "Sin nombre", y, x))

    return coordenadas

def convertir_a_utm(lon, lat):
    utm_x, utm_y, zone_number, zone_letter = utm.from_latlon(lat, lon)
    zona = f"{zone_number}{zone_letter}"
    return utm_x, utm_y, zona

def convertir_a_gms(lon, lat):
    def decimal_a_gms(grado_decimal):
        grados = int(grado_decimal)
        minutos = int((grado_decimal - grados) * 60)
        segundos = (grado_decimal - grados - minutos / 60) * 3600
        return f"{grados}° {minutos}' {segundos:.2f}\""

    return decimal_a_gms(lat), decimal_a_gms(lon)

def guardar_coordenadas_en_excel(coordenadas, output, formato_salida):
    workbook = Workbook()
    hoja = workbook.active
    hoja.title = "Coordenadas"

    if formato_salida == "UTM":
        hoja.append(["Nombre", "Zona", "Coordenada Este", "Coordenada Norte"])
        for name, zona, este, norte in coordenadas:
            hoja.append([name, zona, este, norte])
    else:
        hoja.append(["Nombre", "Latitud", "Longitud"])
        for name, lat, lon in coordenadas:
            hoja.append([name, lat, lon])

    workbook.save(output)

# Ejecutar la aplicación
if __name__ == "__main__":
    main()
