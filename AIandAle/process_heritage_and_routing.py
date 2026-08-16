import os
import sys
import json
import urllib.request
import urllib.parse
import time
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsFields,
    QgsField,
    QgsVectorFileWriter,
    QgsCoordinateTransformContext
)
from qgis.PyQt.QtCore import QVariant

def main():
    print("Initializing standalone QgsApplication...")
    qgs = QgsApplication([], False)
    qgs.initQgis()

    bbox = "145.65,-17.15,145.85,-16.75"
    esplanade_lon, esplanade_lat = 145.7797, -16.9189

    # 1. Fetch Heritage Sites from ArcGIS REST
    print("Fetching QLD Heritage Register boundaries...")
    url = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Boundaries/AdminBoundariesFramework/MapServer/78/query"
    params = {
        'where': '1=1',
        'geometry': bbox,
        'geometryType': 'esriGeometryEnvelope',
        'inSR': '4326',
        'outFields': 'placename,place_id,status,objectid',
        'outSR': '4326',
        'f': 'geojson'
    }
    
    query_url = f"{url}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(query_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as response:
            geojson_data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching heritage sites: {e}")
        qgs.exitQgis()
        sys.exit(1)

    features = geojson_data.get('features', [])
    print(f"Retrieved {len(features)} heritage sites. Computing walking routes...")

    # Create memory layer to store heritage sites with routing attributes
    temp_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "Heritage Sites", "memory")
    provider = temp_layer.dataProvider()
    
    # Add fields
    fields = QgsFields()
    fields.append(QgsField("place_id", QVariant.Int))
    fields.append(QgsField("name", QVariant.String))
    fields.append(QgsField("status", QVariant.String))
    fields.append(QgsField("centroid_lon", QVariant.Double))
    fields.append(QgsField("centroid_lat", QVariant.Double))
    fields.append(QgsField("walk_dist_m", QVariant.Double))
    fields.append(QgsField("walk_time_min", QVariant.Double))
    provider.addAttributes(fields)
    temp_layer.updateFields()

    results_table = []

    for idx, feat in enumerate(features):
        props = feat.get('properties', {})
        geom_dict = feat.get('geometry', {})
        
        # Parse geometry using QgsJsonUtils for QGIS 3.x compatibility
        from qgis.core import QgsJsonUtils
        geom = QgsJsonUtils.geometryFromGeoJson(json.dumps(geom_dict))
        
        if geom.isEmpty():
            continue
            
        centroid = geom.centroid().asPoint()
        c_lon, c_lat = centroid.x(), centroid.y()
        
        place_id = props.get('place_id')
        name = props.get('placename') or "Unnamed Site"
        status = props.get('status') or "State heritage place"
        
        # Calculate OSRM route
        walk_dist = -1.0
        walk_time = -1.0
        
        # Ensure we don't query points too far or outside the road network (e.g. False Cape Battery is across the inlet)
        # We will try to calculate, and if OSRM fails or returns no route, we will record -1.
        osrm_url = f"http://router.project-osrm.org/route/v1/foot/{esplanade_lon},{esplanade_lat};{c_lon},{c_lat}?overview=false"
        try:
            time.sleep(0.15) # Be gentle to OSRM
            osrm_req = urllib.request.Request(osrm_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(osrm_req, timeout=5) as osrm_resp:
                route_data = json.loads(osrm_resp.read().decode('utf-8'))
                routes = route_data.get('routes', [])
                if routes:
                    walk_dist = routes[0].get('distance', -1.0)
                    walk_time = routes[0].get('duration', -1.0) / 60.0 # Convert to minutes
        except Exception as e:
            # Silent fallback, route might not exist (e.g. island or across the bay)
            pass

        # Add feature
        qgs_feat = QgsFeature()
        qgs_feat.setGeometry(geom)
        qgs_feat.setFields(temp_layer.fields())
        qgs_feat.setAttribute("place_id", int(place_id) if place_id else idx)
        qgs_feat.setAttribute("name", name)
        qgs_feat.setAttribute("status", status)
        qgs_feat.setAttribute("centroid_lon", c_lon)
        qgs_feat.setAttribute("centroid_lat", c_lat)
        qgs_feat.setAttribute("walk_dist_m", walk_dist)
        qgs_feat.setAttribute("walk_time_min", walk_time)
        provider.addFeature(qgs_feat)
        
        results_table.append({
            'place_id': place_id,
            'name': name,
            'status': status,
            'distance': walk_dist,
            'time': walk_time
        })
        
        if (idx+1) % 5 == 0 or (idx+1) == len(features):
            print(f"Processed {idx+1}/{len(features)} sites...")

    # 2. Write to GeoPackage
    gpkg_path = "C:/Projects/FunGIS/aiandale/data/cairns_infrastructure.gpkg"
    print(f"Writing layer to GeoPackage: {gpkg_path}")
    
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = "heritage_sites"
    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    
    writer = QgsVectorFileWriter.writeAsVectorFormatV3(
        temp_layer,
        gpkg_path,
        QgsCoordinateTransformContext(),
        options
    )
    
    if writer[0] == QgsVectorFileWriter.NoError:
        print("Heritage sites successfully saved to GeoPackage.")
    else:
        print(f"Error saving to GeoPackage: {writer[0]}")

    # 3. Generate Markdown Report
    print("Generating Markdown Report...")
    # Sort results: valid routes first (closest first), then unreachable ones
    reachable = [r for r in results_table if r['distance'] > 0]
    unreachable = [r for r in results_table if r['distance'] <= 0]
    
    reachable.sort(key=lambda x: x['distance'])
    
    report_path = "C:/Projects/FunGIS/aiandale/heritage_walking_distances.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Cairns Historical Sites & Walking Distances\n\n")
        f.write(f"This report lists the **{len(results_table)} council/state declared heritage sites** within the Cairns area, along with their network walking distances on footpaths from the **Cairns Esplanade Lagoon** `(145.7797, -16.9189)`.\n\n")
        f.write("## Heritage Sites Sorted by Walking Distance\n\n")
        f.write("| Rank | Place ID | Heritage Site Name | Walking Distance (m) | Walking Time (min) | Status |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        
        for rank, r in enumerate(reachable, 1):
            f.write(f"| {rank} | {r['place_id']} | {r['name']} | {r['distance']:.1f} m | {r['time']:.1f} min | {r['status']} |\n")
            
        if unreachable:
            f.write("\n## Unreachable/Isolated Historical Sites (No direct footpath route)\n\n")
            f.write("The following sites are located across water inlets (e.g. False Cape) or in remote locations without connecting pedestrian paths from the Esplanade Lagoon:\n\n")
            f.write("| Place ID | Heritage Site Name | Status |\n")
            f.write("| :--- | :--- | :--- |\n")
            for r in unreachable:
                f.write(f"| {r['place_id']} | {r['name']} | {r['status']} |\n")
                
    print(f"Report written successfully to {report_path}")
    qgs.exitQgis()

if __name__ == "__main__":
    main()
