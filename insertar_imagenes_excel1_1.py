import os
from openpyxl import load_workbook
from openpyxl.drawing.image import Image

def insert_images_in_excel(excel_path, output_path, image_folder, start_cells, row_jump, start_image, end_image):
    # Cargar el archivo Excel
    workbook = load_workbook(excel_path)
    hoja = workbook.active  # Usar la hoja activa; se puede cambiar si necesitas una hoja específica
    
    # Altura deseada para las imágenes en puntos
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

            # Probar diferentes extensiones de imagen y buscar en subcarpetas
            imagen_encontrada = False
            for root, dirs, files in os.walk(image_folder):
                for ext in ['.jpeg', '.jpg', '.png', '.jfif']:
                    imagen_path = os.path.join(root, f'{contador}{ext}')
                    
                    if os.path.exists(imagen_path):
                        # Cargar y ajustar la imagen
                        img = Image(imagen_path)
                        proporcion = img.width / img.height
                        img.height = altura_deseada
                        img.width = altura_deseada * proporcion

                        # Insertar la imagen en la celda correspondiente
                        hoja.add_image(img, celda)
                        print(f"Imagen {contador}{ext} insertada en {celda}")
                        
                        imagen_encontrada = True
                        break  # Salir del bucle de extensiones si se encuentra la imagen
                if imagen_encontrada:
                    break  # Salir del bucle de subcarpetas si se encuentra la imagen
            
            if imagen_encontrada:
                contador += 1  # Incrementar el contador solo si se ha insertado la imagen
            else:
                print(f"No se encontró imagen para el número {contador}")
                contador += 1  # Incrementar aunque la imagen no esté encontrada

        # Incrementar la fila para el siguiente grupo de tres imágenes
        fila_inicial += row_jump

    # Guardar los cambios en el archivo Excel de salida
    workbook.save(output_path)
    print(f"Datos guardados en {output_path}")

if __name__ == "__main__":
    # Pedir al usuario la ruta del archivo de entrada y salida
    excel_path = input("Ingresa la ruta del archivo de Excel en el que deseas insertar las imágenes: ")
    output_path = input("Ingresa la ruta donde deseas guardar el archivo de salida (incluye el nombre y .xlsx): ")
    image_folder = input("Ingresa la ruta de la carpeta que contiene las imágenes: ")
    
    # Pedir al usuario las tres celdas iniciales
    start_cell_1 = input("Ingresa la primera celda inicial para la imagen 1 del grupo (por ejemplo, H19): ")
    start_cell_2 = input("Ingresa la segunda celda inicial para la imagen 2 del grupo (por ejemplo, Q19): ")
    start_cell_3 = input("Ingresa la tercera celda inicial para la imagen 3 del grupo (por ejemplo, R19): ")
    start_cells = [start_cell_1, start_cell_2, start_cell_3]

    row_jump = int(input("Ingresa el salto de filas entre grupos de imágenes (por ejemplo, 10): "))
    start_image = int(input("Ingresa el número inicial de la imagen (por ejemplo, 1): "))
    end_image = int(input("Ingresa el número final de la imagen (por ejemplo, 150): "))

    insert_images_in_excel(excel_path, output_path, image_folder, start_cells, row_jump, start_image, end_image)
