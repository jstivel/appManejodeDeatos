import os
import shutil

# Extensiones de imagen permitidas
extensiones_imagen = {'.jpg', '.jpeg', '.png'}

# Solicitar las rutas de las carpetas al usuario
directorio_origen = input("Ingresa la ruta de la carpeta raíz que contiene las subcarpetas con las imágenes: ")
directorio_destino = input("Ingresa la ruta de la carpeta de destino donde se moverán todas las imágenes: ")

# Crear el directorio de destino si no existe
if not os.path.exists(directorio_destino):
    os.makedirs(directorio_destino)

# Recorrer todas las carpetas y subcarpetas en el directorio de origen
for carpeta_raiz, subcarpetas, archivos in os.walk(directorio_origen):
    for archivo in archivos:
        # Comprobar si el archivo tiene una extensión válida
        if any(archivo.lower().endswith(ext) for ext in extensiones_imagen):
            ruta_origen = os.path.join(carpeta_raiz, archivo)
            ruta_destino = os.path.join(directorio_destino, archivo)

            # Asegurarse de no sobrescribir archivos con el mismo nombre
            if os.path.exists(ruta_destino):
                base, ext = os.path.splitext(archivo)
                contador = 1
                while os.path.exists(ruta_destino):
                    ruta_destino = os.path.join(directorio_destino, f"{base}_{contador}{ext}")
                    contador += 1

            # Mover la imagen al directorio de destino
            shutil.move(ruta_origen, ruta_destino)
            print(f"Movida: {ruta_origen} -> {ruta_destino}")

print("Todas las imágenes han sido movidas.")
