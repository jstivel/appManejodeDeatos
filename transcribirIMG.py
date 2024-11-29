import pytesseract
from PIL import Image
import cv2
import pandas as pd
import re
import os

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

#LEE IMAGENES Y EXTRAE COORDENADAS 

def ocr_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"No se puede abrir la imagen en la ruta: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    text = pytesseract.image_to_string(thresh)
    return text

def extract_coordinates(text):
    pattern = r'-?\d+\.\d+'
    coordinates = re.findall(pattern, text)
    return coordinates

def process_images_in_folder(folder_path, excel_path, start=None, end=None):
    data = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.jfif')):
                # Extraer número de archivo para verificar si está en el rango
                try:
                    file_number = int(re.findall(r'\d+', file)[0])  # Extraer número del nombre de archivo
                except IndexError:
                    file_number = None

                # Condición para verificar si el archivo está dentro del rango si se especificó
                if start is not None and end is not None:
                    if file_number is None or not (start <= file_number <= end):
                        continue

                image_path = os.path.join(root, file)
                try:
                    transcribed_text = ocr_image(image_path)
                    coordinates = extract_coordinates(transcribed_text)

                    row_data = {"Nombre de la imagen": file}
                    for idx, coord in enumerate(coordinates):
                        row_data[f"Coordenada {idx + 1}"] = coord

                    data.append(row_data)
                except Exception as e:
                    print(f"Error procesando {file}: {e}")

    df = pd.DataFrame(data)
    df.to_excel(excel_path, index=False)
    print(f"Datos guardados en {excel_path}")

if __name__ == "__main__":
    folder_path = input("Ingresa la ruta de la carpeta con las imágenes: ")
    excel_path = input("Ingresa la ruta donde deseas guardar el archivo de salida (incluye el nombre y .xlsx): ")

    rango = input("¿Deseas ingresar un rango de imágenes? (Sí o No): ").strip().lower()
    if rango == 'sí' or rango == 'si':
        start = int(input("Ingresa el número inicial del rango: "))
        end = int(input("Ingresa el número final del rango: "))
    else:
        start = None
        end = None

    process_images_in_folder(folder_path, excel_path, start, end)
