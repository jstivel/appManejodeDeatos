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
import logging  
import config_log
import osmnx as ox
import networkx as nx
import cartografia
from ezdxf.addons import Importer


def convertir_a_magna_sirgas(x, y):
    # Definir el sistema de coordenadas geográficas (WGS84)
    wgs84 = Proj(proj='latlong', datum='WGS84')

     # Definir el sistema de coordenadas MAGNA-SIRGAS / Colombia West zone (EPSG:3116)
    mag_sirg = Proj(init='epsg:3115')
    

    # Convertir las coordenadas
    x_magna, y_magna = transform(wgs84, mag_sirg, x, y)

    return x_magna, y_magna  

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
                
                 # Extraer las coordenadas (lat, lon) de la geometría
                coords = [(point[2], point[1]) for point in coordenadas]
                # Agregar base cartográfica si se seleccionó
                # Crear listas para almacenar las coordenadas de los puntos
                latitudes = []
                longitudes = []
                        
                #coordenadas = extraer_coordenadas_de_kmz(kmz_file,formato_salida)
                        
                for cordenada in coordenadas:
                    cord = cordenada 
                    longitudes.append(cord[2])
                    latitudes.append(cord[1])                                  
                    
                   
                with BytesIO() as output:
                # Crear un directorio temporal para manejar el archivo DXF
                    
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        dxf_path = os.path.join(temp_dir, template_dwg.name)                        
                        final_dxf_path_carto = os.path.join(temp_dir, "manzanas_con_cll.dxf")  

                        # Escribimos el contenido del archivo subido en el archivo temporal
                        with open(dxf_path, 'wb') as temp_dxf:
                            temp_dxf.write(template_dwg.getvalue())   
                        
                        if add_cartography:                            
                            lat_min = min(latitudes) - 0.005
                            lat_max = max(latitudes) + 0.005
                            lon_min = min(longitudes) - 0.005
                            lon_max = max(longitudes) + 0.005 
                            cartografia.catograf(lon_min,lat_min,lon_max,lat_max,final_dxf_path_carto,formato_salida)
                            
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
                        else:
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
                        
                        for cordenada in coordenadas:
                            coords = cordenada 
                                                        
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
                print(f"Error al procesar el archivo: {e}")
                st.error(f"Error al procesar el archivo")
# Botón para volver al menú principal
    if st.button("Volver al Menú Principal"):
        st.session_state.pagina_actual = "principal"

if __name__ == "__main__":
    main()
