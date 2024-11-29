import os
from openpyxl import load_workbook
from openpyxl.drawing.image import Image

def insert_images_from_subfolders(excel_path, image_folder, start_cells, row_jump, start_image, end_image,hoja):
    # Cargar el archivo Excel
    workbook = load_workbook(excel_path)
    hoja = workbook[hoja]  # Usar la hoja activa; se puede cambiar si necesitas una hoja específica
    output_path =excel_path+" output"
    
    # Altura deseada para las imágenes en puntos (puedes ajustar este valor)
    altura_deseada = 330  # Ajusta la altura según tus necesidades

    # Separar las celdas iniciales en columnas y filas
    columnas = [cell[0] for cell in start_cells]
    fila_inicial = int(start_cells[0][1:])  # La fila de inicio es la misma para las tres columnas
    
    contador = start_image

    # Bucle para insertar las imágenes en celdas específicas
    while contador <= end_image:
        for i, columna in enumerate(columnas):
            # Definir la celda específica para cada imagen en el grupo
            celda = f'{columna}{fila_inicial}'

            # Probar diferentes extensiones y subcarpetas para encontrar la imagen
            imagen_encontrada = False
            for root, dirs, files in os.walk(image_folder):  # Recorre las subcarpetas
                for ext in ['.jpeg', '.jpg', '.png', '.jfif']:
                    # Formar los nombres con la numeración y variación (ej., "1.jpg", "1 (2).jpg")
                    imagen_name = f"{contador}{' ' + '(' + str(i + 1) + ')' if i > 0 else ''}{ext}"
                    imagen_path = os.path.join(root, imagen_name)
                    
                    if os.path.exists(imagen_path):
                        # Cargar y ajustar la imagen
                        img = Image(imagen_path)
                        proporcion = img.width / img.height
                        img.height = altura_deseada
                        img.width = altura_deseada * proporcion

                        # Insertar la imagen en la celda correspondiente
                        hoja.add_image(img, celda)
                        print(f"Imagen {imagen_name} insertada en {celda}")
                        
                        imagen_encontrada = True
                        break  # Salir del bucle de extensiones si se encuentra la imagen
                
                if imagen_encontrada:
                    break  # Salir del bucle de subcarpetas si se encontró la imagen

        if not imagen_encontrada:
            print(f"No se encontró imagen para el número {contador}")
        
        # Incrementar la fila para el siguiente grupo de tres imágenes
        fila_inicial += row_jump
        contador += 1

    # Guardar los cambios en el archivo Excel de salida
    workbook.save(output_path)
    print(f"Datos guardados en {output_path}")

if __name__ == "__main__":
    # Pedir al usuario la ruta del archivo de entrada y salida
    excel_path = input("Ingresa la ruta del archivo de Excel en el que deseas insertar las imágenes: ")
    hoja= input("Ingresa el nombre de la hoja: ")
    #output_path = input("Ingresa la ruta donde deseas guardar el archivo de salida (incluye el nombre y .xlsx): ")
    image_folder = input("Ingresa la ruta de la carpeta principal que contiene las imágenes: ")
    
    # Pedir al usuario las tres celdas iniciales
    start_cell_1 = input("Ingresa la primera celda inicial para la imagen 1 del grupo (por ejemplo, A1): ")
    start_cell_2 = input("Ingresa la segunda celda inicial para la imagen 2 del grupo (por ejemplo, H1): ")
    start_cell_3 = input("Ingresa la tercera celda inicial para la imagen 3 del grupo (por ejemplo, Q1): ")
    start_cells = [start_cell_1, start_cell_2, start_cell_3]

    row_jump = int(input("Ingresa el salto de filas entre grupos de imágenes (por ejemplo, 10): "))
    start_image = int(input("Ingresa el número inicial de la imagen (por ejemplo, 1): "))
    end_image = int(input("Ingresa el número final de la imagen (por ejemplo, 10): "))

    insert_images_from_subfolders(excel_path, image_folder, start_cells, row_jump, start_image, end_image,hoja)
