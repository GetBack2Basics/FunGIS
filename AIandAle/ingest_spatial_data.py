#!/usr/bin/env python3
"""
Generalized Spatial Data Ingestion CLI Tool
Supported Sources:
1. ArcGIS REST Feature/Map Server Layer (downloads polygons/lines/points in bbox and pages dynamically)
2. Translink GTFS ZIP (parses bus stops and routes)

Uses PyQGIS standalone API (must be run under OSGeo4W Python environment).
"""

import os
import sys
import json
import time
import zipfile
import urllib.request
import urllib.parse
import argparse

# ---------------------------------------------------------------------------
# Core Utilities
# ---------------------------------------------------------------------------
def urlopen_with_retry(url_or_req, timeout=40, retries=5, delay=4):
    last_exc = None
    for attempt in range(retries):
        try:
            req = url_or_req
            if isinstance(req, str):
                req = urllib.request.Request(req, headers={'User-Agent': 'Mozilla/5.0'})
            return urllib.request.urlopen(req, timeout=timeout)
        except Exception as e:
            last_exc = e
            print(f"  Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    raise last_exc

# ---------------------------------------------------------------------------
# 1. ArcGIS REST Downloader
# ---------------------------------------------------------------------------
def fetch_arcgis_data(service_url, bbox_str, out_geojson, fields_str="*", batch_size=1000):
    print(f"Querying ArcGIS REST service: {service_url}")
    
    # Get ID list first
    params = {
        'where': '1=1',
        'geometry': bbox_str,
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326',
        'returnIdsOnly': 'true',
        'f': 'json'
    }
    url = f"{service_url}/query?{urllib.parse.urlencode(params)}"
    
    try:
        with urlopen_with_retry(url, timeout=30) as response:
            id_data = json.loads(response.read().decode('utf-8'))
            if 'error' in id_data:
                print(f"Error querying object IDs: {id_data['error']}")
                return False
            
            oid_field = id_data.get('objectIdFieldName', 'objectid')
            object_ids = id_data.get('objectIds', [])
            if object_ids is None:
                object_ids = []
            
            print(f"Found {len(object_ids)} features matching bounding box.")
            if not object_ids:
                # Save empty GeoJSON
                empty_fc = {"type": "FeatureCollection", "features": []}
                with open(out_geojson, 'w', encoding='utf-8') as f:
                    json.dump(empty_fc, f)
                return True
    except Exception as e:
        print(f"Failed to query layer IDs: {e}")
        return False

    # Query features in pages/batches
    features = []
    total_batches = -(-len(object_ids) // batch_size) # ceiling division
    
    for idx in range(0, len(object_ids), batch_size):
        batch_ids = object_ids[idx:idx+batch_size]
        where_clause = f"{oid_field} IN ({','.join(map(str, batch_ids))})"
        
        batch_params = {
            'where': where_clause,
            'outSR': '4326',
            'outFields': fields_str,
            'f': 'geojson'
        }
        batch_url = f"{service_url}/query?{urllib.parse.urlencode(batch_params)}"
        print(f"  Fetching batch {idx//batch_size + 1} / {total_batches}...")
        
        try:
            with urlopen_with_retry(batch_url, timeout=40) as batch_resp:
                batch_data = json.loads(batch_resp.read().decode('utf-8'))
                batch_features = batch_data.get('features', [])
                if batch_features:
                    features.extend(batch_features)
        except Exception as e:
            print(f"Failed to fetch batch starting index {idx}: {e}")
            return False
            
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    with open(out_geojson, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f)
        
    print(f"Saved {len(features)} features to temporary file {out_geojson}")
    return True

# ---------------------------------------------------------------------------
# 2. GTFS ZIP Parser
# ---------------------------------------------------------------------------
def fetch_gtfs_transit(gtfs_url_or_file, out_stops_json, out_routes_json):
    zip_path = "temp_gtfs.zip"
    
    if gtfs_url_or_file.startswith("http"):
        print(f"Downloading GTFS ZIP from: {gtfs_url_or_file}")
        try:
            with urlopen_with_retry(gtfs_url_or_file, timeout=60) as response:
                with open(zip_path, 'wb') as f:
                    f.write(response.read())
        except Exception as e:
            print(f"Failed to download GTFS ZIP: {e}")
            return False
    else:
        zip_path = gtfs_url_or_file
        print(f"Using local GTFS ZIP: {zip_path}")
        
    if not os.path.exists(zip_path):
        print(f"GTFS ZIP file does not exist: {zip_path}")
        return False
        
    # Extract to a temp directory
    temp_extract_dir = "temp_gtfs_extracted"
    os.makedirs(temp_extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as ref:
        ref.extractall(temp_extract_dir)
        
    # Parse stops.txt
    print("Parsing GTFS stops...")
    stops_features = []
    stops_file = os.path.join(temp_extract_dir, "stops.txt")
    if os.path.exists(stops_file):
        with open(stops_file, 'r', encoding='utf-8-sig') as f:
            headers = [h.strip() for h in f.readline().split(',')]
            for line in f:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) < len(headers):
                    continue
                row = dict(zip(headers, parts))
                try:
                    lat = float(row['stop_lat'])
                    lon = float(row['stop_lon'])
                    stops_features.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {
                            "stop_id": row.get("stop_id"),
                            "stop_name": row.get("stop_name"),
                            "stop_code": row.get("stop_code")
                        }
                    })
                except ValueError:
                    continue
        with open(out_stops_json, 'w', encoding='utf-8') as f:
            json.dump({"type": "FeatureCollection", "features": stops_features}, f)
        print(f"  Parsed {len(stops_features)} stops.")
    else:
        print("  stops.txt not found in ZIP!")
        
    # Parse shapes.txt and routes.txt to reconstruct routes
    print("Reconstructing GTFS routes...")
    shapes_file = os.path.join(temp_extract_dir, "shapes.txt")
    routes_file = os.path.join(temp_extract_dir, "routes.txt")
    trips_file = os.path.join(temp_extract_dir, "trips.txt")
    
    if os.path.exists(shapes_file) and os.path.exists(routes_file) and os.path.exists(trips_file):
        # 1. Load shape coordinates
        shapes_coords = {}
        with open(shapes_file, 'r', encoding='utf-8-sig') as f:
            headers = [h.strip() for h in f.readline().split(',')]
            for line in f:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) < len(headers): continue
                row = dict(zip(headers, parts))
                shape_id = row['shape_id']
                lat, lon = float(row['shape_pt_lat']), float(row['shape_pt_lon'])
                seq = int(row['shape_pt_sequence'])
                shapes_coords.setdefault(shape_id, []).append((seq, lon, lat))
                
        # 2. Map route IDs to names
        route_names = {}
        with open(routes_file, 'r', encoding='utf-8-sig') as f:
            headers = [h.strip() for h in f.readline().split(',')]
            for line in f:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) < len(headers): continue
                row = dict(zip(headers, parts))
                route_names[row['route_id']] = row.get('route_short_name', row.get('route_long_name'))
                
        # 3. Map shape IDs to route IDs
        shape_routes = {}
        with open(trips_file, 'r', encoding='utf-8-sig') as f:
            headers = [h.strip() for h in f.readline().split(',')]
            for line in f:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) < len(headers): continue
                row = dict(zip(headers, parts))
                shape_id = row.get('shape_id')
                if shape_id:
                    shape_routes[shape_id] = row['route_id']
                    
        # 4. Generate line features
        routes_features = []
        for shape_id, points in shapes_coords.items():
            sorted_pts = [ (p[1], p[2]) for p in sorted(points, key=lambda x: x[0]) ]
            route_id = shape_routes.get(shape_id)
            route_name = route_names.get(route_id, "Unknown Route")
            routes_features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": sorted_pts},
                "properties": {
                    "shape_id": shape_id,
                    "route_id": route_id,
                    "route_name": route_name
                }
            })
        with open(out_routes_json, 'w', encoding='utf-8') as f:
            json.dump({"type": "FeatureCollection", "features": routes_features}, f)
        print(f"  Reconstructed {len(routes_features)} route tracks.")
    else:
        print("  shapes.txt, routes.txt, or trips.txt missing!")

    # Clean up temp files
    try:
        if gtfs_url_or_file.startswith("http") and os.path.exists(zip_path):
            os.remove(zip_path)
        for root, dirs, files in os.walk(temp_extract_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(temp_extract_dir)
    except Exception as e:
        print(f"Warning during cleanup: {e}")
        
    return True

# ---------------------------------------------------------------------------
# 3. GeoPackage Writer (standalone PyQGIS)
# ---------------------------------------------------------------------------
def write_to_geopackage(geojson_path, gpkg_path, layer_name):
    # Initialize QGIS Standalone Context
    from qgis.core import QgsProject, QgsApplication, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateTransformContext
    
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    print(f"Saving layer '{layer_name}' into GeoPackage...")
    temp_layer = QgsVectorLayer(geojson_path, layer_name, "ogr")
    if not temp_layer.isValid():
        print(f"[ERROR] Failed to load parsed layer: {geojson_path}")
        qgs.exitQgis()
        return False
        
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = layer_name
    
    # Overwrite if exists, otherwise create
    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    
    err = QgsVectorFileWriter.writeAsVectorFormatV3(
        temp_layer,
        gpkg_path.replace("\\", "/"),
        QgsCoordinateTransformContext(),
        options
    )
    
    if err[0] == QgsVectorFileWriter.NoError:
        print(f"Successfully saved '{layer_name}' inside {gpkg_path}")
        success = True
    else:
        print(f"[ERROR] Failed to write to GPKG: {err}")
        success = False
        
    temp_layer = None
    qgs.exitQgis()
    return success

# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generalized Spatial Ingestion CLI Tool.")
    parser.add_argument("--type", required=True, choices=["arcgis", "gtfs"], help="Source data type")
    parser.add_argument("--url", required=True, help="ArcGIS Service Layer URL or GTFS ZIP URL")
    parser.add_argument("--bbox", default="145.65,-17.15,145.85,-16.75", help="Bounding box (xmin,ymin,xmax,ymax)")
    parser.add_argument("--gpkg", required=True, help="Path to output GeoPackage database")
    parser.add_argument("--layer-name", help="Output GeoPackage layer name (required for arcgis type)")
    parser.add_argument("--fields", default="*", help="ArcGIS query fields (comma-separated, default: *)")
    parser.add_argument("--batch-size", type=int, default=1000, help="ArcGIS query batch size (default: 1000)")
    
    args = parser.parse_args()
    
    # Ensure data directory exists
    gpkg_dir = os.path.dirname(os.path.abspath(args.gpkg))
    os.makedirs(gpkg_dir, exist_ok=True)
    
    temp_geojson = "temp_ingestion_layer.geojson"
    temp_stops = "temp_stops.geojson"
    temp_routes = "temp_routes.geojson"
    
    success = False
    
    if args.type == "arcgis":
        if not args.layer_name:
            print("[ERROR] --layer-name is required for type=arcgis", file=sys.stderr)
            sys.exit(1)
            
        ok = fetch_arcgis_data(args.url, args.bbox, temp_geojson, args.fields, args.batch_size)
        if ok:
            success = write_to_geopackage(temp_geojson, args.gpkg, args.layer_name)
            if os.path.exists(temp_geojson):
                os.remove(temp_geojson)
                
    elif args.type == "gtfs":
        ok = fetch_gtfs_transit(args.url, temp_stops, temp_routes)
        if ok:
            success1 = write_to_geopackage(temp_stops, args.gpkg, "bus_stops")
            success2 = write_to_geopackage(temp_routes, args.gpkg, "bus_routes")
            success = success1 and success2
            
            if os.path.exists(temp_stops): os.remove(temp_stops)
            if os.path.exists(temp_routes): os.remove(temp_routes)
            
    if success:
        print("\nIngestion completed successfully!")
    else:
        print("\nIngestion failed.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
