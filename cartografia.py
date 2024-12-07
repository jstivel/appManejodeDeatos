import osmnx as ox
import geopandas as gpd
from shapely.ops import polygonize, unary_union
from shapely.geometry import Polygon, MultiPolygon, LineString
import ezdxf
from ezdxf.enums import TextEntityAlignment
import math

def main():
    place = "Cali, Valle del Cauca, Colombia"
    G = ox.graph_from_place(place, network_type="drive", truncate_by_edge=True)

    # Get nodes and edges as GeoDataFrames
    nodes, edges = ox.graph_to_gdfs(G)

    # Rename the 'u' field to something acceptable for DXF (e.g., 'from_node')
    edges = edges.rename(columns={'u': 'from_node'})

    # Simplify geometry to reduce potential duplicate polygons
    edges['geometry'] = edges['geometry'].simplify(tolerance=0.0001) # Adjust tolerance if needed

    # 1. Crear polígonos de manzanas usando offset
    manzanas = []
    for index, row in edges.iterrows():
        line = row['geometry']
        # Calcular offset a ambos lados de la línea
        offset_izquierdo = line.parallel_offset(distance=0.00002, side='left')  # Ajusta la distancia
        offset_derecho = line.parallel_offset(distance=0.00002, side='right') # Ajusta la distancia

        # Intentar crear un polígono con los offsets
        try:
            poligono = Polygon(list(offset_izquierdo.coords) + list(offset_derecho.coords[::-1])) # Invertir coords del offset derecho
            if poligono.is_valid:  # Verificar si el polígono es válido
                manzanas.append(poligono)
        except ValueError:
            pass  # Ignorar polígonos inválidos

    # 2. Unir polígonos y manejar MultiPolígonos
    manzanas_union = unary_union(manzanas)
    if isinstance(manzanas_union, MultiPolygon):
        manzanas_finales = list(manzanas_union)
    else:
        manzanas_finales = [manzanas_union]

    # 3. Crear GeoDataFrame y guardar como GeoPackage
    gdf_manzanas = gpd.GeoDataFrame(geometry=[p.boundary for p in manzanas_finales])  # Agregar .boundary
    #gdf_manzanas = gpd.GeoDataFrame(geometry=manzanas_finales)
    gdf_manzanas.to_file("manzanas_offset.gpkg", driver="GPKG")

    # 4. Convertir a DXF con ogr2ogr
    !ogr2ogr -f DXF manzanas_offset.dxf manzanas_offset.gpkg

    print("Cartografía de manzanas con offset guardada en manzanas_offset.dxf")

    # 5. Agregar calles y direcciones usando ezdxf
    doc = ezdxf.readfile("manzanas_offset.dxf")
    msp = doc.modelspace()

    # Create a set to track processed edges to avoid duplicates:
    processed_edges = set()

    # Agregar direcciones de calles como texto (si está disponible)
    for index, row in edges.iterrows():
        if 'name' in row and row['name']:  # Verificar si la calle tiene nombre
            # Get osmid, handling potential lists:
            osmid = row['osmid']
            if isinstance(osmid, list):
                osmid = tuple(osmid)  # Convert list to tuple (hashable)
            
            if osmid not in processed_edges:
                line = row['geometry']
                # Calculate angle of the line
                x1, y1 = line.coords[0]
                x2, y2 = line.coords[1]
                angle = math.degrees(math.atan2(y2 - y1, x2 - x1))

                # Calculate midpoint of the line
                mid_point = line.interpolate(0.5, normalized=True)
                x, y = mid_point.x, mid_point.y

                # Use TextEntityAlignment.MIDDLE_CENTER for alignment and add rotation
                msp.add_text(row['name'], dxfattribs={'height': 0.00002, 'rotation': angle}).set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)

                # Add edge osmid to processed_edges
                processed_edges.add(osmid)

    # Guardar el DXF final
    doc.saveas("manzanas_con_calles.dxf")

    print("Cartografía de manzanas con calles y direcciones guardada en manzanas_con_calles.dxf")