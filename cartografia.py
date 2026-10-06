import osmnx as ox
import geopandas as gpd
from shapely.ops import polygonize, unary_union
from shapely.geometry import Polygon, MultiPolygon, LineString
import ezdxf
from ezdxf.enums import TextEntityAlignment
import streamlit as st
import math
import pyogrio
import tempfile
import os
import traceback
import kmz_to_cad

def catograf(lon_min,lat_min,lon_max,lat_max,final_dxf_path_carto,formato_salida):

    # Crear un directorio temporal
    with tempfile.TemporaryDirectory() as temp_dir_carto:
        print("Directorio temporal creado:", temp_dir_carto)

        # Rutas para los archivos temporales
        gpkg_path = os.path.join(temp_dir_carto, "manzanas_offset.gpkg")
        dxf_path = os.path.join(temp_dir_carto, "manzanas_offset.dxf")
        
        #final_dxf_path = os.path.join(final_dxf_path_carto, "manzanas_con_calles.dxf")

        try:
            # Crear el grafo usando el bounding box
            bbox = (lon_min, lat_min, lon_max, lat_max)
            G = ox.graph.graph_from_bbox(bbox, network_type="drive", truncate_by_edge=True)

            if len(list(G.edges)) == 0:
                raise ValueError("No se encontraron vías transitables en el área seleccionada")

            nodes, edges = ox.graph_to_gdfs(G)
            edges = edges[edges.geometry.notnull() & edges.geometry.is_valid]
            edges = edges.rename(columns={'u': 'from_node'})
            edges['geometry'] = edges['geometry'].simplify(tolerance=0.000007)

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
            if manzanas_union.is_empty:
                raise ValueError("No se pudieron generar manzanas a partir de las vías del área seleccionada")
            manzanas_finales = list(manzanas_union.geoms) if isinstance(manzanas_union, MultiPolygon) else [manzanas_union]

            # Crear GeoDataFrame y guardar como GeoPackage
            gdf_manzanas = gpd.GeoDataFrame(geometry=[p.boundary for p in manzanas_finales])
            if gdf_manzanas.crs is None:
                gdf_manzanas.set_crs(epsg=4326, inplace=True)  # Asignar WGS84 si no tiene CRS

            # Transformar a un CRS específico, si es necesario
            if formato_salida == "MAGNA-SIRGAS / Colombia West zone EPSG:3115":
                gdf_manzanas = gdf_manzanas.to_crs(epsg=3115)  # Transformar a MAGNA-SIRGAS / Colombia West Zone

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
                nombre_calle = row.get('name')
                if nombre_calle is None:
                    continue
                if isinstance(nombre_calle, float) and math.isnan(nombre_calle):
                    continue
                if isinstance(nombre_calle, (list, tuple)):
                    nombre_calle = nombre_calle[0] if nombre_calle else None
                    if not nombre_calle:
                        continue
                nombre_calle = str(nombre_calle).strip()
                if not nombre_calle:
                    continue

                osmid = tuple(row['osmid']) if isinstance(row['osmid'], list) else row['osmid']
                if osmid not in processed_edges:
                    line = row['geometry']
                    if formato_salida == "MAGNA-SIRGAS / Colombia West zone EPSG:3115":
                        x1, y1 = line.coords[0]
                        x2, y2 = line.coords[1]

                        x1_magna, y1_magna = kmz_to_cad.convertir_a_magna_sirgas(float(x1), float(y1))
                        x2_magna, y2_magna = kmz_to_cad.convertir_a_magna_sirgas(float(x2), float(y2))

                        angle = math.degrees(math.atan2(y2_magna - y1_magna, x2_magna - x1_magna))
                        mid_x_magna = (x1_magna + x2_magna) / 2
                        mid_y_magna = (y1_magna + y2_magna) / 2

                        msp.add_text(
                            nombre_calle,
                            dxfattribs={
                            "height": 2,
                            "rotation": angle,  # Rotación del texto
                            "insert":(mid_x_magna, mid_y_magna),"layer":"Calles"
                            })
                        processed_edges.add(osmid)

                    else:
                        x1, y1 = line.coords[0]
                        x2, y2 = line.coords[1]
                        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
                        mid_point = line.interpolate(0.5, normalized=True)
                        msp.add_text(nombre_calle, dxfattribs={'height': 0.00002, 'rotation': angle,"layer":"Calles"}).set_placement(
                            (mid_point.x, mid_point.y), align=TextEntityAlignment.MIDDLE_CENTER)
                        processed_edges.add(osmid)

            doc.saveas(final_dxf_path_carto)
            print(f"Archivo final DXF guardado temporalmente en: {final_dxf_path_carto}")
            return True

        except Exception as e:
            print(f"Error durante la ejecución: {e}")
            traceback.print_exc()
            st.error(f"Error al generar la base cartográfica: {e}")
            return False

