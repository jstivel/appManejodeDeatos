import openpyxl
from pyproj import Proj, transform
from pyautocad import Autocad, APoint

def leer_coordenadas_excel(archivo_excel):
    # Cargar el archivo Excel
    workbook = openpyxl.load_workbook(archivo_excel)
    hoja = workbook.active  # Usar la primera hoja

    coordenadas = []

    # Leer las coordenadas y los nombres desde el archivo Excel
    for row in hoja.iter_rows(min_row=2, values_only=True):  # Comenzar desde la fila 2
        nombre, x, y = row[0], row[1], row[2]  # Usar la columna B (X) y C (Y)
        coordenadas.append((nombre, x, y))

    return coordenadas

def convertir_a_magna_sirgas(x, y):
    # Definir el sistema de coordenadas geográficas (WGS84)
    wgs84 = Proj(proj='latlong', datum='WGS84')

     # Definir el sistema de coordenadas MAGNA-SIRGAS / Colombia West zone (EPSG:3116)
    mag_sirg = Proj(init='epsg:3115')

    # Convertir las coordenadas
    x_magna, y_magna = transform(wgs84, mag_sirg, x, y)

    return x_magna, y_magna

def crear_bloques_en_autocad(coordenadas,bloque):
    try:
        acad = Autocad(create_if_not_exists=True)
        for coord in coordenadas:
            nombre, x, y = coord
            x_magna, y_magna = convertir_a_magna_sirgas(float(x), float(y))
            p1 = APoint(x_magna, y_magna)
            acad.model.InsertBlock(p1, bloque, 1, 1, 1, 0)
            # Insertar el texto como MText
            longitud_mtext = 100  # Ancho del cuadro de MText
            acad.model.AddMText(p1 + APoint(0, 0.5), longitud_mtext, nombre)  # Ajusta la posición del MText y el ancho del cuadro
            
        print("Bloques insertados correctamente.")
    except Exception as e:
        print(f"Error al insertar bloques: {e}")

def main():
    archivo_excel = input("Ingresa la ruta completa del archivo de coordenadas: ") # Cambia esto por la ruta a tu archivo Excel
    bloque = input("Ingresa el nombre del bloque ") 
    coordenadas = leer_coordenadas_excel(archivo_excel)
    crear_bloques_en_autocad(coordenadas,bloque)

if __name__ == "__main__":
    main()
