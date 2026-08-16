import os
import sys
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsRectangle,
    QgsLineSymbol,
    QgsFillSymbol,
    QgsMarkerSymbol,
    QgsSingleSymbolRenderer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsRuleBasedRenderer,
    QgsPointClusterRenderer,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsMapSettings,
    QgsMapRendererJob
)
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor, QFont, QPainter

def main():
    print("Initializing standalone QgsApplication...")
    # Initialize QgsApplication in headless mode (GUI = False)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    project = QgsProject.instance()
    project.clear()
    
    project_path = "C:/Projects/FunGIS/aiandale/aiandale.qgz"
    project.setFileName(project_path)
    
    crs = QgsCoordinateReferenceSystem("EPSG:4326")
    project.setCrs(crs)

    # 1. Paths
    data_dir = "C:/Projects/FunGIS/aiandale/data"
    gpkg_path = os.path.join(data_dir, "cairns_infrastructure.gpkg").replace("\\", "/")
    parchment_path = os.path.join(data_dir, "parchment_texture.jpg").replace("\\", "/")
    hillshade_url = "type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}"

    # 2. Load layers
    print("Loading ESRI World Hillshade...")
    hillshade_layer = QgsRasterLayer(hillshade_url, "World Hillshade", "wms")
    if hillshade_layer.isValid():
        project.addMapLayer(hillshade_layer)
    else:
        print("Failed to load Hillshade layer.")

    ordered_vectors = [
        ("cadastre_base", "Cadastre Base Parcels"),
        ("watercourses", "Watercourses"),
        ("roads", "Roads"),
        ("heritage_sites", "Heritage Sites"),
        ("bus_routes", "Bus Routes"),
        ("bus_stops", "Bus Stops")
    ]

    loaded_layers = {}
    for gpkg_name, layer_title in ordered_vectors:
        source_uri = f"{gpkg_path}|layername={gpkg_name}"
        layer = QgsVectorLayer(source_uri, layer_title, "ogr")
        if layer.isValid():
            project.addMapLayer(layer)
            loaded_layers[gpkg_name] = layer
            print(f"Loaded vector layer: {layer_title}")
        else:
            print(f"Failed to load layer: {gpkg_name}")

    print("Loading Parchment Texture...")
    if os.path.exists(parchment_path):
        parchment_layer = QgsRasterLayer(parchment_path, "Parchment Texture")
        if parchment_layer.isValid():
            project.addMapLayer(parchment_layer)
            # Set Multiply Blend Mode
            parchment_layer.setBlendMode(QPainter.CompositionMode_Multiply)
            print("Parchment Texture loaded and set to Multiply blend mode.")
        else:
            print("Parchment Texture layer invalid.")
    else:
        print(f"Parchment file not found at {parchment_path}")

    # 3. Apply Styling
    # Watercourses: Symbolize by size (stream order) and perenniality
    if "watercourses" in loaded_layers:
        water_layer = loaded_layers["watercourses"]
        water_color = "#1c4e80" # Dark indigo blue
        
        # 1. Perennial, Major size
        sym_per_maj = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.7'})
        # 2. Perennial, Medium size
        sym_per_med = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.45'})
        # 3. Perennial, Minor size
        sym_per_min = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.22'})
        
        # 4. Intermittent/Ephemeral/Unknown, Major size (Dashed)
        sym_int_maj = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.7', 'line_style': 'dash'})
        # 5. Intermittent/Ephemeral/Unknown, Medium size (Dashed)
        sym_int_med = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.45', 'line_style': 'dash'})
        # 6. Intermittent/Ephemeral/Unknown, Minor size (Dashed)
        sym_int_min = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.22', 'line_style': 'dash'})
        
        root_rule = QgsRuleBasedRenderer.Rule(None)
        
        rules = [
            (sym_per_maj, "perenniality = 'Perennial' AND (stream_order >= 5 OR hierarchy = 'Major')", "Perennial - Major"),
            (sym_per_med, "perenniality = 'Perennial' AND stream_order IN (3, 4)", "Perennial - Medium"),
            (sym_per_min, "perenniality = 'Perennial' AND (stream_order <= 2 OR stream_order IS NULL OR hierarchy = 'Minor')", "Perennial - Minor"),
            (sym_int_maj, "perenniality != 'Perennial' AND (stream_order >= 5 OR hierarchy = 'Major')", "Intermittent - Major"),
            (sym_int_med, "perenniality != 'Perennial' AND stream_order IN (3, 4)", "Intermittent - Medium"),
            (sym_int_min, "perenniality != 'Perennial' AND (stream_order <= 2 OR stream_order IS NULL OR hierarchy = 'Minor')", "Intermittent - Minor")
        ]
        
        for symbol, filter_exp, label in rules:
            rule = QgsRuleBasedRenderer.Rule(symbol, 0, 0, filter_exp, label)
            root_rule.appendChild(rule)
            
        water_renderer = QgsRuleBasedRenderer(root_rule)
        water_layer.setRenderer(water_renderer)
        print("Watercourses styling applied.")

    # Bus Stops: Point Clustering
    if "bus_stops" in loaded_layers:
        stops_layer = loaded_layers["bus_stops"]
        
        cluster_symbol = QgsMarkerSymbol.createSimple({
            'name': 'circle',
            'color': '#8c510a',      # Sepia brown
            'size': '8.0',
            'outline_color': '#ffffff',
            'outline_width': '0.4'
        })
        
        single_symbol = QgsMarkerSymbol.createSimple({
            'name': 'circle',
            'color': '#dfc27d',      # Soft sepia gold
            'size': '3.0',
            'outline_color': '#8c510a',
            'outline_width': '0.3'
        })
        
        # We must clone stops_layer's single symbol renderer as source
        stops_layer.setRenderer(QgsSingleSymbolRenderer(single_symbol))
        
        cluster_renderer = QgsPointClusterRenderer()
        cluster_renderer.setEmbeddedRenderer(stops_layer.renderer().clone())
        cluster_renderer.setClusterSymbol(cluster_symbol)
        cluster_renderer.setTolerance(12.0)
        
        stops_layer.setRenderer(cluster_renderer)
        print("Bus stops point clustering applied.")

    # Roads: Sepia/Old-map style categorized renderer
    if "roads" in loaded_layers:
        roads_layer = loaded_layers["roads"]
        
        # State controlled: Muted rust red
        sym_state = QgsLineSymbol.createSimple({'color': '#a50f15', 'width': '0.55'})
        # Local controlled: Faded sepia/brown
        sym_local = QgsLineSymbol.createSimple({'color': '#5c3a21', 'width': '0.22'})
        
        cat_state = QgsRendererCategory("T", sym_state, "State Controlled")
        cat_local = QgsRendererCategory("F", sym_local, "Local Controlled")
        cat_unk = QgsRendererCategory("U", sym_local, "Unknown Control")
        
        renderer = QgsCategorizedSymbolRenderer("scr_indicator", [cat_state, cat_local, cat_unk])
        roads_layer.setRenderer(renderer)
        
        # Rule-Based Labels
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = "road_name_full"
        label_settings.isExpression = False
        label_settings.filterExpression = "class IN ('Highway', 'Secondary', 'Connector')"
        label_settings.enabled = True
        
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Georgia", 8))
        text_format.setColor(QColor("#2b2b2b"))
        
        # Beige buffer to blend with parchment texture
        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1.0)
        buffer_settings.setColor(QColor("#f5ecd7"))
        text_format.setBuffer(buffer_settings)
        
        label_settings.setFormat(text_format)
        roads_layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        roads_layer.setLabelsEnabled(True)
        print("Roads styling and labeling applied.")

    # Heritage Sites: Symbolize as gold polygons with brown outlines
    if "heritage_sites" in loaded_layers:
        heritage_layer = loaded_layers["heritage_sites"]
        heritage_symbol = QgsFillSymbol.createSimple({
            'color': '223,194,125,120', # Gold with 120 opacity (out of 255)
            'outline_color': '#8c510a',
            'outline_width': '0.3',
            'style': 'solid'
        })
        heritage_layer.setRenderer(QgsSingleSymbolRenderer(heritage_symbol))
        heritage_layer.triggerRepaint()
        print("Heritage sites styling applied.")

    # Cadastre: Faded thin outline, scale dependent visibility
    if "cadastre_base" in loaded_layers:
        cad_layer = loaded_layers["cadastre_base"]
        cad_symbol = QgsFillSymbol.createSimple({
            'color': '0,0,0,0',
            'outline_color': '#cccccc',
            'outline_width': '0.08'
        })
        cad_layer.setRenderer(QgsSingleSymbolRenderer(cad_symbol))
        cad_layer.setScaleBasedVisibility(True)
        cad_layer.setMinimumScale(25000.0)
        cad_layer.setMaximumScale(0.0)
        print("Cadastre styling and scale visibility applied.")

    # Bus Routes: Thin faded dot line
    if "bus_routes" in loaded_layers:
        routes_layer = loaded_layers["bus_routes"]
        routes_symbol = QgsLineSymbol.createSimple({'color': '#807e7a', 'width': '0.25', 'line_style': 'dot'})
        routes_layer.setRenderer(QgsSingleSymbolRenderer(routes_symbol))
        print("Bus routes styling applied.")

    # 4. Save QGIS Project
    project.write()
    print("Project saved.")

    # 5. Render Canvas
    print("Configuring render settings...")
    # Cairns BBox
    extent = QgsRectangle(145.65, -17.15, 145.85, -16.75)
    
    map_settings = QgsMapSettings()
    map_settings.setDestinationCrs(crs)
    map_settings.setExtent(extent)
    map_settings.setOutputSize(QSize(2000, 2000))
    map_settings.setBackgroundColor(QColor("#f5ecd7")) # Parchment color base

    # Layers ordered from top to bottom in render list
    render_layers = []
    # 1. Parchment texture (if valid)
    if os.path.exists(parchment_path):
        render_layers.append(project.mapLayersByName("Parchment Texture")[0])
    # 2. Bus stops
    if "bus_stops" in loaded_layers:
        render_layers.append(loaded_layers["bus_stops"])
    # 3. Bus routes
    if "bus_routes" in loaded_layers:
        render_layers.append(loaded_layers["bus_routes"])
    # 4. Heritage sites
    if "heritage_sites" in loaded_layers:
        render_layers.append(loaded_layers["heritage_sites"])
    # 5. Roads
    if "roads" in loaded_layers:
        render_layers.append(loaded_layers["roads"])
    # 5. Watercourses
    if "watercourses" in loaded_layers:
        render_layers.append(loaded_layers["watercourses"])
    # 6. Cadastre
    if "cadastre_base" in loaded_layers:
        render_layers.append(loaded_layers["cadastre_base"])
    # 7. World Hillshade
    if hillshade_layer.isValid():
        render_layers.append(hillshade_layer)

    map_settings.setLayers(render_layers)

    from qgis.core import QgsMapRendererSequentialJob
    print("Executing render job...")
    job = QgsMapRendererSequentialJob(map_settings)
    job.start()
    job.waitForFinished()
    
    render_img_path = "C:/Projects/FunGIS/aiandale/render_parchment.png"
    image = job.renderedImage()
    if image.save(render_img_path):
        print(f"Render saved successfully to {render_img_path}")
    else:
        print("Failed to save render image.")

    # 6. Write World File (.pgw)
    pgw_path = "C:/Projects/FunGIS/aiandale/render_parchment.pgw"
    x_size = (145.85 - 145.65) / 2000.0
    y_size = (-16.75 - (-17.15)) / 2000.0
    y_size_neg = -y_size
    ul_x = 145.65 + (x_size / 2.0)
    ul_y = -16.75 - (y_size / 2.0)
    
    with open(pgw_path, "w") as f:
        f.write(f"{x_size:.10f}\n")
        f.write("0.0\n")
        f.write("0.0\n")
        f.write(f"{y_size_neg:.10f}\n")
        f.write(f"{ul_x:.10f}\n")
        f.write(f"{ul_y:.10f}\n")
    print(f"World file saved successfully to {pgw_path}")

    qgs.exitQgis()
    print("Standalone QgsApplication exited.")

if __name__ == "__main__":
    main()
