import os
import shutil

# MUEVE IMAGENES A CARPETAS INDIVIDUALES
def crear_carpetas_y_mover_imagenes(directorio_origen, directorio_destino, inicio_rango, fin_rango):
    # Crear el directorio de destino si no existe
    if not os.path.exists(directorio_destino):
        os.makedirs(directorio_destino)

    # Crear las carpetas P100, P101, ..., PN en el directorio de destino
    for i in range(inicio_rango, fin_rango + 1):
        carpeta = os.path.join(directorio_destino, f'P{i}')
        os.makedirs(carpeta, exist_ok=True)

    # Recorrer el directorio de origen y sus subcarpetas
    for root, _, files in os.walk(directorio_origen):
        for file in files:
            # Verificar si el nombre del archivo contiene alguno de los números del rango
            for i in range(inicio_rango, fin_rango + 1):
                numero_str = str(i)
                if numero_str in file:
                    ruta_imagen = os.path.join(root, file)
                    ruta_carpeta = os.path.join(directorio_destino, f'P{i}')
                    destino = os.path.join(ruta_carpeta, file)

                    # Manejar conflicto de nombres añadiendo sufijos
                    contador = 1
                    while os.path.exists(destino):
                        base, ext = os.path.splitext(file)
                        destino = os.path.join(ruta_carpeta, f"{base}_{contador}{ext}")
                        contador += 1

                    # Mover la imagen al destino
                    shutil.move(ruta_imagen, destino)
                    print(f"Imagen {file} movida a {ruta_carpeta}")
                    break

if __name__ == "__main__":
    # Solicita las rutas y el rango de carpetas desde la consola
    directorio_origen = input("Ingresa la ruta del directorio de las imágenes: ")
    directorio_destino = input("Ingresa la ruta del directorio de destino: ")
    inicio_rango = int(input("Ingresa el número inicial del rango de carpetas (por ejemplo, 100): "))
    fin_rango = int(input("Ingresa el número final del rango de carpetas (por ejemplo, 201): "))

    # Ejecutar el script
    crear_carpetas_y_mover_imagenes(directorio_origen, directorio_destino, inicio_rango, fin_rango)
