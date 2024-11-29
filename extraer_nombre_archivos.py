import os
import pandas as pd

# Función para extraer rutas de archivos
def extract_file_paths(folder_path, output_excel):
    file_data = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_data.append({'FilePath': file_path, 'CurrentName': file, 'NewName': ''})
    
    df = pd.DataFrame(file_data)
    df.to_excel(output_excel, index=False)
    print(f"Rutas de archivos guardadas en {output_excel}")

# Función para renombrar archivos basados en un Excel
def rename_files_from_excel(input_excel):
    df = pd.read_excel(input_excel)
    for index, row in df.iterrows():
        old_path = row['FilePath']
        new_name = row['NewName']
        
        if pd.notna(new_name) and new_name.strip():  # Verifica que haya un nuevo nombre válido
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                print(f"Renombrado: {old_path} -> {new_path}")
            except Exception as e:
                print(f"Error al renombrar {old_path}: {e}")
        else:
            print(f"Sin cambio para: {old_path}")

# Uso del script con entrada por consola
if __name__ == "__main__":
    print("Selecciona una opción:")
    print("1. Extraer rutas de archivos a un Excel")
    print("2. Renombrar archivos desde un Excel modificado")
    
    choice = input("Ingresa tu opción (1/2): ").strip()
    
    if choice == "1":
        folder_path = input("Ingresa la ruta de la carpeta a procesar: ").strip()
        output_excel = input("Ingresa el nombre del archivo Excel de salida (e.g., archivos_rutas.xlsx): ").strip()
        extract_file_paths(folder_path, output_excel)
    elif choice == "2":
        input_excel = input("Ingresa la ruta del archivo Excel modificado: ").strip()
        rename_files_from_excel(input_excel)
    else:
        print("Opción no válida.")
