import os
import zipfile
import ezdxf
from pykml import parser
import requests
import ezdxf
import json


def iter_placemarks(element):
    """Itera sobre todos los <Placemark> del KML sin recursión."""
    queue = [element]  # Cola de elementos por procesar
    while queue:
        current = queue.pop(0)
        if current.tag.endswith("Placemark"):
            yield current
        queue.extend(current.getchildren())  # Añadir hijos a la cola

def kmz_to_dwg(kmz_path, dwg_path, template_dwg, block_name):
    try:
        # Crear un archivo DXF basado en la plantilla
        doc = ezdxf.readfile(template_dwg)
        #doc = ezdxf.new(dxfversion='AC1027')
        msp = doc.modelspace()
        # Eliminar todas las entidades (excepto bloques)
        for entity in doc.modelspace():
            if entity.dxftype() not in ['BLOCK', 'INSERT']:  # Excluir bloques e inserciones
                doc.modelspace().delete_entity(entity)
        

        # Crear listas para almacenar las coordenadas de los puntos
        latitudes = []
        longitudes = []

        # Descomprimir el archivo KMZ
        with zipfile.ZipFile(kmz_path, 'r') as kmz:
            # Buscar el archivo KML en el KMZ
            kml_filename = [name for name in kmz.namelist() if name.endswith('.kml')][0]
            kml_file = kmz.open(kml_filename)

        # Parsear el archivo KML
        kml_tree = parser.parse(kml_file)
        kml_root = kml_tree.getroot()

        # Procesar cada <Placemark>
        for placemark in iter_placemarks(kml_root):
            # Verificar si tiene coordenadas
            if hasattr(placemark, 'Point') and hasattr(placemark.Point, 'coordinates'):
                coords = placemark.Point.coordinates.text.strip()
                lon, lat, _ = map(float, coords.split(','))  # Extraer longitud, latitud
                name = placemark.name.text if hasattr(placemark, 'name') else "Unnamed"

                # Agregar las coordenadas a las listas
                longitudes.append(lon)
                latitudes.append(lat)

                # Conversión básica de coordenadas (lon, lat -> x, y)
                x, y = lon, lat

                # Insertar bloque en las coordenadas
                msp.add_blockref(block_name, (x, y))
                # Agregar texto con el nombre del punto
                msp.add_text(
                    name,
                    dxfattribs={
                        "insert": (x+ 0.0001, y),  # Ajustar posición del texto
                        "height": 0.00004,
                    },
                )
        # Calcular los límites geográficos
        lat_min = (min(latitudes))-0.001
        lat_max = (max(latitudes))+0.001
        lon_min = (min(longitudes))-0.002
        lon_max = (max(longitudes))+0.002
        osm_data = get_osm_data(lat_min, lat_max, lon_min, lon_max)
        convert_osm_to_dxf(msp,osm_data)

        # Guardar el archivo DXF
        doc.saveas(dwg_path)
        print(f"Archivo DWG generado exitosamente: {dwg_path}")
        return lat_min, lat_max, lon_min, lon_max  # Devolver los límites geográficos

    except Exception as e:
        print(f"Error al procesar el archivo KMZ: {e}")
        return None 
#Guarda los datos en un archivo de texto para depuración.
def log_to_file(filename, data):
    
    with open(filename, 'a') as file:
        file.write(data + '\n')
    print(f"Datos guardados en {filename}")
#código consulta la Overpass API para obtener datos (cartografia)

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
    log_to_file("osm_query_log.txt", f"Consulta a la API OSM: {query}")
    
    if response.status_code == 200:
        log_to_file("osm_query_log.txt", f"Respuesta de la API OSM: {json.dumps(response.json(), indent=4)}")
        
        # Extraer todos los IDs de "type": "way"
        way_ids = [element["id"] for element in response.json()["elements"] if element["type"] == "way"]
        
        # Crear la consulta unificada para todos los way_ids
        query_way = "[out:json];" + "".join([f"way({way_id});out geom;" for way_id in way_ids])
        
        response = requests.get(url, params={'data': query_way})
        
        return response.json()
    else:
        
        return None
    


def convert_osm_to_dxf(msp, osm_data):
    for element in osm_data['elements']:
        if element['type'] == 'way':
            # Obtener los IDs de los nodos en el 'way'            
            geometry = element.get('geometry', [])
            
            if geometry:
                # Extraer las coordenadas (lat, lon) de la geometría
                coords = [(point['lon'], point['lat']) for point in geometry]
                
                # Convertir a coordenadas de tipo DXF (en este caso, lat -> y, lon -> x)
                for i in range(len(coords)-1):
                    x1, y1 = coords[i]
                    x2, y2 = coords[i+1]
                    # Dibujar línea en el DXF
                    msp.add_line((x1, y1), (x2, y2))                    
                
        elif element['type'] == 'relation':
            # Puedes manejar relaciones (polígonos, áreas, etc.) aquí si es necesario
            pass

    print("Geometría de OSM añadida al DXF")


# Ejecución
if __name__ == "__main__":
    kmz_path = input("Ingresa la ruta del archivo KMZ: ").strip()
    template_dwg = input("Ingresa la ruta del archivo DWG con el bloque predefinido: ").strip()
    block_name = input("Ingresa el nombre del bloque que deseas insertar: ").strip()
    dwg_path = input("Ingresa el nombre del archivo DWG de salida (e.g., salida.dwg): ").strip()
    kmz_to_dwg(kmz_path, dwg_path, template_dwg, block_name)
