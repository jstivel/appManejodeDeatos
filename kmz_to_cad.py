import os
import ezdxf
from pykml import parser
import requests
import tempfile
from io import BytesIO
import streamlit as st
import math
from pyproj import Proj, transform
from coordenadas import extraer_coordenadas_de_kmz,calculate_distances

def convertir_a_magna_sirgas(x, y):
    # Definir el sistema de coordenadas geográficas (WGS84)
    wgs84 = Proj(proj='latlong', datum='WGS84')

     # Definir el sistema de coordenadas MAGNA-SIRGAS / Colombia West zone (EPSG:3116)
    mag_sirg = Proj(init='epsg:3115')

    # Convertir las coordenadas
    x_magna, y_magna = transform(wgs84, mag_sirg, x, y)

    return x_magna, y_magna  

def get_osm_data(lat_min, lat_max, lon_min, lon_max):
   
    query = f"""
    [out:json];
    (
      node({lat_min},{lon_min},{lat_max},{lon_max});
      way({lat_min},{lon_min},{lat_max},{lon_max});
      relation({lat_min},{lon_min},{lat_max},{lon_max});
    );
    out body;
    """
    url = "https://overpass-api.de/api/interpreter"
    response = requests.get(url, params={'data': query})

    # Guardar la consulta y respuesta para análisis    
    
    if response.status_code == 200:       
        
        # Extraer todos los IDs de "type": "way"
        way_ids = [element["id"] for element in response.json()["elements"] if element["type"] == "way"]
        
        # Crear la consulta unificada para todos los way_ids
        query_way = "[out:json];" + "".join([f"way({way_id});out geom;" for way_id in way_ids])
        
        response = requests.get(url, params={'data': query_way})
        
        return response.json()
    else:
        
        return None
    
def convert_osm_to_dxf(msp, osm_data,formato_salida):
    for element in osm_data['elements']:
        if element['type'] == 'way':            
            # Obtener las coordenadas 'way'            
            geometry = element.get('geometry', [])
            #obtener nombre de las calles     
            streetName = element["tags"].get("name", None)
            # Calcula lat min y max del way
            minlat = min(point['lat'] for point in geometry)
            minlon = min(point['lon'] for point in geometry)
            maxlat = max(point['lat'] for point in geometry)
            maxlon = max(point['lon'] for point in geometry)
            if formato_salida == "MAGNA-SIRGAS / Colombia West zone EPSG:3115":
                # Cálculo del punto medio
                x1_magna, y1_magna = convertir_a_magna_sirgas(float(minlon), float(minlat))
                x2_magna, y2_magna = convertir_a_magna_sirgas(float(maxlon), float(maxlat))
                mid_x_magna = (x1_magna + x2_magna) / 2
                mid_y_magna = (y1_magna + y2_magna) / 2
                # Cálculo del ángulo (en grados)
                angle_magna = math.degrees(math.atan2(y2_magna - y1_magna, x2_magna - x1_magna))   
                if streetName:
                    msp.add_text(
                    streetName,
                    dxfattribs={
                    "height": 2,
                    "rotation": angle_magna,  # Rotación del texto
                    "insert":(mid_x_magna, mid_y_magna)
                    })
            # Extraer las coordenadas (lat, lon) de la geometría
            coords = [(point['lon'], point['lat']) for point in geometry]
            if geometry:
                
                # Convertir a coordenadas de tipo DXF (en este caso, lat -> y, lon -> x)
                for i in range(len(coords)-1):
                    x1, y1 = coords[i]
                    x2, y2 = coords[i+1]                    

                    if formato_salida == "MAGNA-SIRGAS / Colombia West zone EPSG:3115":
                        x1_magna, y1_magna = convertir_a_magna_sirgas(float(x1), float(y1))
                        x2_magna, y2_magna = convertir_a_magna_sirgas(float(x2), float(y2))
                        
                     
                        # Dibujar línea en el DXF
                        msp.add_line((x1_magna, y1_magna), (x2_magna, y2_magna)) 
                        # Insertar nombre de calle                        
                        
                    else:
                        # Dibujar línea en el DXF
                        msp.add_line((x1, y1), (x2, y2))  
        elif element['type'] == 'relation':
            # Puedes manejar relaciones (polígonos, áreas, etc.) aquí si es necesario
            pass

    print("Geometría de OSM añadida al DXF")


# Interfaz de Streamlit
def main():
    st.title("Convertir KMZ a DXF")

    kmz_file = st.file_uploader("Cargar archivo KMZ", type=["kmz"])
    template_dwg = st.file_uploader("Cargar plantilla DWG", type=["dxf"])
    block_name = st.text_input("Nombre del bloque a insertar", "DefaultBlock")
    formato_salida = st.selectbox("Seleccionar formato de cordenadas", ["Decimal","MAGNA-SIRGAS / Colombia West zone EPSG:3115"])
    add_cartography = st.checkbox("Agregar base cartográfica", value=False)

    if st.button("Generar archivo DXF"):
        if not kmz_file or not template_dwg:
            st.error("Por favor, cargue ambos archivos (KMZ y plantilla DXF).")
        else:
            
            try:
                
                coordenadas = extraer_coordenadas_de_kmz(kmz_file,formato_salida)
                distancias = calculate_distances(coordenadas)
                solo_distancias = [(distancia[2]) for distancia in distancias]
                print(solo_distancias[0])
                 # Extraer las coordenadas (lat, lon) de la geometría
                coords = [(point[2], point[1]) for point in coordenadas]
                #dxf_output = kmz_to_dwg(kmz_file, template_dwg, block_name, add_cartography,formato_salida)
                with BytesIO() as output:
                # Crear un directorio temporal para manejar el archivo DXF
                    with tempfile.TemporaryDirectory() as temp_dir:
                        dxf_path = os.path.join(temp_dir, template_dwg.name)
                        
                        # Escribimos el contenido del archivo subido en el archivo temporal
                        with open(dxf_path, 'wb') as temp_dxf:
                            temp_dxf.write(template_dwg.getvalue())
                        
                       
                        # Leer el archivo DXF basado en la plantilla
                        doc = ezdxf.readfile(dxf_path)
                        msp = doc.modelspace()
                        
                        # Convertir a coordenadas de tipo DXF (en este caso, lat -> y, lon -> x)
                        if formato_salida == "MAGNA-SIRGAS / Colombia West zone EPSG:3115":
                            coords_sirgas=[]
                            
                           
                            for coord in coords:
                                x,y=coord                                
                                sirgas=convertir_a_magna_sirgas(float(x), float(y))
                                coords_sirgas.append(sirgas) 
                            #calcular punto medio e inserción de distancias
                            for i in range(len(coords_sirgas)-1):
                                x1,y1=coords_sirgas[i]     
                                x2,y2=coords_sirgas[i+1] 
                                mid_x_magna = (x1 + x2) / 2
                                mid_y_magna = (y1 + y2) / 2
                                # Cálculo del ángulo (en grados)
                                angle_magna = math.degrees(math.atan2(y2 - y1, x2 - x1))
                                msp.add_text(
                                str(solo_distancias[i]) + ".0",
                                dxfattribs={
                                "height": 2,
                                "rotation": angle_magna,  # Rotación del texto
                                "insert":(mid_x_magna, mid_y_magna)
                                })   

                            msp.add_lwpolyline(coords_sirgas)  
                        else:
                            msp.add_lwpolyline(coords)  

                        # Crear listas para almacenar las coordenadas de los puntos
                        latitudes = []
                        longitudes = []
                        
                        #coordenadas = extraer_coordenadas_de_kmz(kmz_file,formato_salida)
                        
                        for cordenada in coordenadas:
                            coords = cordenada 
                            longitudes.append(coords[2])
                            latitudes.append(coords[1])    
                            
                            if formato_salida == "MAGNA-SIRGAS / Colombia West zone EPSG:3115":
                                nombre, y, x = coords
                                x_magna, y_magna = convertir_a_magna_sirgas(float(x), float(y))                               
                                # Insertar bloque y texto
                                
                                msp.add_blockref(block_name, (x_magna,y_magna))
                                msp.add_text(
                                    nombre,
                                    dxfattribs={"insert": (x_magna-8, y_magna+2), "height": 2},
                                )
                            else:    
                                     
                                # Insertar bloque y texto
                                msp.add_blockref(block_name, (coords[2], coords[1]))
                                msp.add_text(
                                    coords[0],
                                    dxfattribs={"insert": (coords[2]+ 0.0001, coords[1]), "height": 0.00004},
                                )
                            
                            
                        # Agregar base cartográfica si se seleccionó
                        if add_cartography:
                            lat_min = min(latitudes) - 0.001
                            lat_max = max(latitudes) + 0.001
                            lon_min = min(longitudes) - 0.002
                            lon_max = max(longitudes) + 0.002
                            osm_data = get_osm_data(lat_min, lat_max, lon_min, lon_max)
                            convert_osm_to_dxf(msp, osm_data,formato_salida)
                    
                    # Guardar el archivo DXF procesado en un nuevo archivo temporal
                    with tempfile.TemporaryDirectory() as temp_dir2:
                        nuevo_dxf_path = os.path.join(temp_dir2, "output_final.dxf")
                        doc.saveas(nuevo_dxf_path)
                        print(nuevo_dxf_path)

                        # Leer el contenido del nuevo archivo y cargarlo en el buffer de memoria
                        with open(nuevo_dxf_path, "rb") as nuevo_dxf_file:
                            output.write(nuevo_dxf_file.read())

                        output.seek(0)  # Volver al inicio del buffer
                                  
                    
                    # Crear el botón de descarga en Streamlit
                    st.download_button(
                        label="Descargar archivo DXF",
                        data=output,
                        file_name=f"coordenadas_{template_dwg.name}",  # Nombre del archivo descargado
                        mime="application/dxf"  # Tipo MIME del archivo DXF
                    )    
                    
                
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")
# Botón para volver al menú principal
    if st.button("Volver al Menú Principal"):
        st.session_state.pagina_actual = "principal"

if __name__ == "__main__":
    main()
