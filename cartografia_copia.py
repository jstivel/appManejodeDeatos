import osmnx as ox
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon
import ezdxf
from ezdxf.enums import TextEntityAlignment
import math
import pyogrio
import tempfile
import os

def main(lon_min, lat_min, lon_max, lat_max,output_dir):
    # Crear un directorio temporal
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Directorio temporal creado:", temp_dir)

        # Rutas para los archivos temporales
        gpkg_path = os.path.join(temp_dir, "manzanas_offset.gpkg")
        dxf_path = os.path.join(temp_dir, "manzanas_offset.dxf")
        final_dxf_path = os.path.join(output_dir, "manzanas_con_calles.dxf")

        try:
            # Crear el grafo usando el bounding box
            bbox = (lon_min, lat_min, lon_max, lat_max)
            G = ox.graph.graph_from_bbox(bbox, network_type="drive", truncate_by_edge=True)

            nodes, edges = ox.graph_to_gdfs(G)
            edges = edges[edges.geometry.notnull() & edges.geometry.is_valid]
            edges = edges.rename(columns={'u': 'from_node'})
            edges['geometry'] = edges['geometry'].simplify(tolerance=0.0001)

            # Crear polígonos de manzanas usando offset
            manzanas = []
            for _, row in edges.iterrows():
                line = row['geometry']
                try:
                    offset_izq = line.parallel_offset(0.00002, side='left')
                    offset_der = line.parallel_offset(0.00002, side='right')
                    poligono = Polygon(list(offset_izq.coords) + list(offset_der.coords[::-1]))
                    if poligono.is_valid:
                        manzanas.append(poligono)
                except ValueError:
                    continue

            # Unir polígonos y manejar MultiPolígonos
            manzanas_union = unary_union(manzanas)
            manzanas_finales = list(manzanas_union) if isinstance(manzanas_union, MultiPolygon) else [manzanas_union]

            # Crear GeoDataFrame y guardar como GeoPackage
            gdf_manzanas = gpd.GeoDataFrame(geometry=[p.boundary for p in manzanas_finales])
            gdf_manzanas.to_file(gpkg_path, driver="GPKG")
            print(f"Archivo GeoPackage guardado temporalmente en: {gpkg_path}")

            # Convertir a DXF con pyogrio
            pyogrio.write_dataframe(gdf_manzanas, dxf_path, driver="DXF")
            print(f"Archivo DXF guardado temporalmente en: {dxf_path}")

            # Agregar texto con nombres de calles al DXF
            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()
            processed_edges = set()

            for _, row in edges.iterrows():
                if 'name' in row and row['name']:
                    osmid = tuple(row['osmid']) if isinstance(row['osmid'], list) else row['osmid']
                    if osmid not in processed_edges:
                        line = row['geometry']
                        x1, y1 = line.coords[0]
                        x2, y2 = line.coords[1]
                        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
                        mid_point = line.interpolate(0.5, normalized=True)
                        msp.add_text(row['name'], dxfattribs={'height': 0.00002, 'rotation': angle}).set_placement(
                            (mid_point.x, mid_point.y), align=TextEntityAlignment.MIDDLE_CENTER)
                        processed_edges.add(osmid)

            doc.saveas(final_dxf_path)
            print(f"Archivo final DXF guardado temporalmente en: {final_dxf_path}")

            # Retorna la ruta del DXF final para su uso posterior
            return final_dxf_path
        except Exception as e:
            print(f"Error durante la ejecución: {e}")
            return None

if __name__ == "__main__":
    output_directory = "./output"  # Cambia esto a la ruta deseada
    os.makedirs(output_directory, exist_ok=True)  # Crear el directorio si no existe
    dxf_output_path = main(-75.73897, 4.49043, -75.65177, 4.54194,output_directory)
    if dxf_output_path:
        print(f"DXF generado en: {dxf_output_path}")
