import requests

def reverse_geocode(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }
    headers = {
        "User-Agent": "mi_aplicacion_prueba/1.0 (email@ejemplo.com)"
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "address" in data:
            return data["display_name"]
        else:
            return "No se encontró dirección"
    else:
        return f"Error en la solicitud: {response.status_code}"

latitud =   4.627680
longitud = -74.466371
direccion = reverse_geocode(latitud, longitud)
print("Dirección:", direccion)
