import os
import zipfile
import xml.etree.ElementTree as ET
from geopy.distance import geodesic
import csv

# Función para extraer el archivo KML de un KMZ
def extract_kml(kmz_path):
    with zipfile.ZipFile(kmz_path, 'r') as kmz:
        for file_name in kmz.namelist():
            if file_name.endswith('.kml'):
                kmz.extract(file_name, os.path.dirname(kmz_path))
                return os.path.join(os.path.dirname(kmz_path), file_name)
    return None

# Función para leer los nombres y coordenadas del archivo KML
def get_named_coordinates_from_kml(kml_path):
    # Parsear el archivo KML como XML
    tree = ET.parse(kml_path)
    root = tree.getroot()

    # Espacio de nombres del KML
    namespace = {'kml': 'http://www.opengis.net/kml/2.2'}

    named_coordinates = []
    for placemark in root.findall(".//kml:Placemark", namespace):
        # Extraer el nombre del punto
        name = placemark.find("kml:name", namespace)
        name = name.text.strip() if name is not None else "Sin Nombre"

        # Extraer las coordenadas del punto
        for coord in placemark.findall(".//kml:coordinates", namespace):
            raw_coords = coord.text.strip().split()
            for point in raw_coords:
                lon, lat, *_ = map(float, point.split(','))
                named_coordinates.append((name, (lat, lon)))  # Nombre, (latitud, longitud)
    return named_coordinates

# Función para calcular distancias entre puntos consecutivos
def calculate_distances(named_coords):
    distances = []
    for i in range(len(named_coords) - 1):
        point1_name, point1_coords = named_coords[i]
        point2_name, point2_coords = named_coords[i + 1]
        distance = geodesic(point1_coords, point2_coords).meters
        distances.append((point1_name, point2_name, distance))
    return distances

# Función para guardar las distancias en un archivo CSV
def save_to_csv(data, output_path):
    with open(output_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Punto 1", "Punto 2", "Distancia (m)"])
        for row in data:
            writer.writerow([row[0], row[1], row[2]])

# Ruta del archivo KMZ proporcionada por el usuario
kmz_path = input("Por favor, ingresa la ruta del archivo KMZ: ")
output_csv = "distancias.csv"

if kmz_path.endswith('.kmz'):
    kml_path = extract_kml(kmz_path)
    if kml_path:
        named_coordinates = get_named_coordinates_from_kml(kml_path)
        if named_coordinates:
            distances = calculate_distances(named_coordinates)
            save_to_csv(distances, output_csv)
            print(f"Distancias guardadas en: {output_csv}")
        else:
            print("No se encontraron puntos en el archivo KML.")
        os.remove(kml_path)  # Limpieza del archivo KML extraído
    else:
        print("No se pudo extraer un archivo KML del KMZ.")
else:
    print("El archivo proporcionado no es un KMZ.")
