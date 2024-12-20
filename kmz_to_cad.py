import os
import pandas as pd
import ezdxf
from pykml import parser
import tempfile
from io import BytesIO
import streamlit as st
import math
from pyproj import Proj, Transformer, transform
from coordenadas import extraer_coordenadas_de_kmz,calculate_distances
import osmnx as ox
import networkx as nx
import cartografia
from ezdxf.addons import Importer


def convertir_a_magna_sirgas(x, y):
    # Definir el sistema de coordenadas geográficas (WGS84)  
    wgs84 = Proj("EPSG:4326")
    # Definir el sistema de coordenadas MAGNA-SIRGAS / Colombia West zone (EPSG:3115)   
    mag_sirg = Proj("EPSG:3115")
    # Convertir las coordenadas
    transformer = Transformer.from_proj(wgs84, mag_sirg)
    y_magna,x_magna = transformer.transform(y, x)
    

    return x_magna, y_magna  

def process_csv(csv_file):
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_csv:
        temp_csv.write(csv_file.read())
        temp_csv_path = temp_csv.name
    df = pd.read_csv(temp_csv_path)
    
    # Convertir los nombres de las columnas a minúsculas
    df.columns = df.columns.str.lower()
    # Crear un array vacío para las coordenadas
    coordenadas = []

    # Recorrer cada fila del DataFrame y extraer los valores
    for _,row in df.iterrows():
        name = row['nombre']     # Asumiendo que la columna de nombre se llama 'nombre'
        latitud = row['latitud'] # Asumiendo que la columna de latitud se llama 'latitud'
        longitud = row['longitud'] # Asumiendo que la columna de longitud se llama 'longitud'
        
        # Agregar la tupla (name, latitud, longitud) al array
        coordenadas.append((name, latitud, longitud))

    return coordenadas

def process_distance_long_lat(coordinates):
    distances = calculate_distances(coordinates)
    distances = [(distance[2]) for distance in distances]
    latitudes = []
    longitudes = []
    for coordinate in coordinates:                     
            longitudes.append(coordinate[2])
            latitudes.append(coordinate[1]) 
    return distances,latitudes, longitudes

def add_mapping(longitudes,latitudes,output_format,dxf_path):
   
    temp_dxf = tempfile.NamedTemporaryFile(delete=False, suffix=".dxf")  # Crea el archivo temporal
    final_dxf_path_carto = temp_dxf.name  # Guardar la ruta del archivo temporal
    
    lat_min = min(latitudes) - 0.005
    lat_max = max(latitudes) + 0.005
    lon_min = min(longitudes) - 0.005
    lon_max = max(longitudes) + 0.005 
    cartografia.catograf(lon_min,lat_min,lon_max,lat_max,final_dxf_path_carto,output_format)
    
    # Leer el archivo DXF basado en la plantilla 
    doc_template = ezdxf.readfile(dxf_path)   
    doc_template.dxfversion = "AC1021"                                               
    doc = ezdxf.readfile(final_dxf_path_carto)
    doc.dxfversion = "AC1021"                        
    msp = doc.modelspace()                                          
    block_names = [block.name for block in doc_template.blocks 
                if not block.name.startswith("*") and 
                block.name not in ('*Model_Space', '*Paper_Space')]
    importer = Importer(doc_template, doc)     
    importer.import_blocks(block_names)  
    importer.finalize() 
    #os.remove(final_dxf_path_carto)
    return  doc,msp,final_dxf_path_carto

def draw_distance(distances,latitudes, longitudes,msp,output_format):

    height = 0.00002
    coordinates=[]
    if output_format == "MAGNA-SIRGAS / Colombia West zone EPSG:3115": 
        height = 2      
        for i in range(len(latitudes)):
            x = longitudes[i]
            y = latitudes[i]                              
            sirgas=convertir_a_magna_sirgas(float(x), float(y))
            coordinates.append(sirgas) 
    else:
        coordinates = tuple(zip(longitudes,latitudes))
        
    #calcular punto medio e inserción de distancias
    for i in range(len(coordinates)-1):
        x1,y1=coordinates[i]     
        x2,y2=coordinates[i+1] 
        mid_x_magna = (x1 + x2) / 2
        mid_y_magna = (y1 + y2) / 2
        # Cálculo del ángulo (en grados)
        angle_magna = math.degrees(math.atan2(y2 - y1, x2 - x1))
        msp.add_text(
        str(distances[i]) + ".0",
        dxfattribs={
        "height": height,
        "rotation": angle_magna,  # Rotación del texto
        "insert":(mid_x_magna, mid_y_magna),"layer":"Distance"
        })
        msp.add_lwpolyline(coordinates) 
    

def draw_blocks (coordinates,msp,output_format,block_name,layer_name):
    for coordinate in coordinates:
        coords = coordinate  
        name, y, x = coords 
        disface_x = 0.00008
        disface_y = 0.00002
        height = 0.00002                                                  
        if output_format == "MAGNA-SIRGAS / Colombia West zone EPSG:3115":   
            height = 2      
            disface_x = 8
            disface_y = 2     
            x, y = convertir_a_magna_sirgas(float(x), float(y))                                        
              
        # Insertar bloque y texto
        msp.add_blockref(block_name, (x, y),dxfattribs={"layer": layer_name})
        msp.add_mtext(
            name,
            dxfattribs={"insert": (x-disface_x, y+disface_y), "char_height": height,"layer":"Text"},
        )  
def trigger(coordinates,add_cartography,layer_name,output_format,block_name,dxf_path,template_dwg):
    try:      
        distances,latitudes, longitudes = process_distance_long_lat(coordinates)             

        with BytesIO() as output:                               
            if add_cartography:                            
                doc,msp,final_dxf_path_carto = add_mapping(longitudes,latitudes,output_format,dxf_path)
            else:  
                msp = doc.modelspace()
            if layer_name not in doc.layers:
                doc.layers.new(name=layer_name, dxfattribs={"color": 5})
            #Dibujamos las ditancias y bloques
            draw_distance(distances,latitudes, longitudes,msp,output_format)  
            draw_blocks(coordinates,msp,output_format,block_name,layer_name)
            # Guardar el archivo DXF procesado en un nuevo archivo temporal
            doc.saveas(dxf_path)
            with open(dxf_path, "rb") as nuevo_dxf_file:
                output.write(nuevo_dxf_file.read())
            os.remove(dxf_path) 
            output.seek(0)
            #os.remove(final_dxf_path_carto)           
            # Crear el botón de descarga en Streamlit
            st.download_button(
                label="Descargar archivo DXF",
                data=output,
                file_name=f"coordenadas_{template_dwg.name}",  # Nombre del archivo descargado
                mime="application/dxf"  # Tipo MIME del archivo DXF
            )    
    except Exception as e:
            st.error(f"Error al procesar el archivo CSV, revise que contenga los campos nombre,latitud y longitud: {e}")
            #print(f"\033[31m{distances}\033[0m")          

# Interfaz de Streamlit
def main():
    st.title("Convertir KMZ a DXF")
    # Dividir la pantalla en dos columnas
    col1, col2 = st.columns(2)
    section1 = col1.empty()
    section2 = col2.empty()
    section3 = st.empty()
    
    with section1.container():     
        coord_in = st.selectbox("Seleccione el origen de coordenadas", ["Archivo kmz","Archivo csv"])
        if coord_in == "Archivo kmz":
            kmz_file = st.file_uploader("Cargar archivo KMZ", type=["kmz"])
            csv_file=0
        else :
            csv_file = st.file_uploader("Cargar archivo CSV", type=["csv"])
            kmz_file=0
    with section2.container(): 
        template_base = st.selectbox("Desea trabajar con dxf base", ["SI","NO"])
        if template_base == "SI":
            template_dwg = st.file_uploader("Cargar plantilla DXF", type=["dxf"])       
          

    output_format = st.selectbox("Seleccionar formato de cordenadas", ["Decimal","MAGNA-SIRGAS / Colombia West zone EPSG:3115"])
    add_cartography = st.checkbox("Agregar base cartográfica", value=False)

    #Mostrar capas y bloques del dxf cargado
    if template_base=="SI":
        if template_dwg:
            try:            
                # Crear un archivo temporal para manejar el archivo DXF
                with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as temp_dxf:
                    temp_dxf.write(template_dwg.read())
                    dxf_path = temp_dxf.name
                # Leer el archivo DXF desde el archivo temporal con ezdxf
                doc = ezdxf.readfile(dxf_path)
                # Obtener las capas
                layers = [layer.dxf.name for layer in doc.layers]
                # Obtener los bloques
                blocks = [block.name for block in doc.blocks 
                                            if not block.name.startswith("*") and 
                                            block.name not in ('*Model_Space', '*Paper_Space')]
                # Mostrar las capas y bloques en el navegador            
                with section3.container():   
                    if blocks:
                        block_name = st.selectbox("Seleccione el bloque que desea insertar",blocks )
                    
                        #list(map(lambda block_name: st.write(f"• {block_name}"), blocks))
                    else:
                        st.write("No se encontraron bloques en el archivo DXF.")
                    if layers:
                        layer_name = st.selectbox("Seleccione la capa en la que desea insertar el bloque",layers )
                    
                    else:
                        st.write("No se encontraron capas en el archivo DXF.")
                    # Eliminar el archivo temporal
                    
            #return temp_dxf_path
            except Exception as e:
                st.error(f"Error al procesar el archivo DXF: {e}")
    
    #Boton para generar archivo de salida
    if st.button("Generar archivo DXF"):  

        if (coord_in == "Archivo kmz" and template_base == "SI") and (not kmz_file or not template_dwg):
            st.error("Por favor, cargue ambos archivos (KMZ y plantilla DXF).")
        elif (coord_in == "Archivo csv" and template_base == "SI") and (not csv_file or not template_dwg):
            st.error("Por favor, cargue ambos archivos (CSV y plantilla DXF).")
        elif csv_file and template_dwg:
            try:
                coordinates= process_csv(csv_file)
                trigger(coordinates,add_cartography,layer_name,output_format,block_name,dxf_path,template_dwg)
            except Exception as e:
                    st.error(f"Error al procesar el archivo CSV: {e}")
                    
        elif kmz_file and template_dwg:               
            try:
               coordinates = extraer_coordenadas_de_kmz(kmz_file,output_format)  
               trigger(coordinates,add_cartography,layer_name,output_format,block_name,dxf_path,template_dwg)
            except Exception as e:
                    st.error(f"Error al procesar el archivo KMZ: {e}")
                    #print(f"\033[31m{distances}\033[0m")                     
            
# Botón para volver al menú principal
    if st.button("Volver al Menú Principal"):
        st.session_state.pagina_actual = "principal"

if __name__ == "__main__":
    main()
