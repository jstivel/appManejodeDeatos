import logging
import os

# Crear carpeta para logs si no existe
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='logs/mi_aplicacion.log',
    filemode='w',
    force=True  # Asegura que se aplique la configuración
)


