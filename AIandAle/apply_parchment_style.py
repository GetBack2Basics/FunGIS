import os
import gc
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsLineSymbol,
    QgsFillSymbol,
    QgsMarkerSymbol,
    QgsSingleSymbolRenderer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsRuleBasedRenderer,
    QgsPointClusterRenderer,
    QgsCoordinateReferenceSystem,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsTextFormat,
    QgsTextBufferSettings
)
from qgis.PyQt.QtGui import QColor, QFont, QPainter

project = QgsProject.instance()

# 1. Paths
data_dir = "C:/Projects/FunGIS/aiandale/data"
gpkg_path = os.path.join(data_dir, "cairns_infrastructure.gpkg").replace("\\", "/")
parchment_path = os.path.join(data_dir, "parchment_texture.jpg").replace("\\", "/")
hillshade_url = "type=xyz&url=https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}"

# 2. Reset and rebuild layer order in QGIS Project
project.clear()
project.setFileName("C:/Projects/FunGIS/aiandale/aiandale.qgz")
project.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))

# Load base raster layers
print("Loading ESRI World Hillshade terrain layer...")
hillshade_layer = QgsRasterLayer(hillshade_url, "World Hillshade", "wms")
if hillshade_layer.isValid():
    project.addMapLayer(hillshade_layer)
else:
    print("Failed to load ESRI World Hillshade.")

# Load vector layers from GPKG bottom-to-top
ordered_vectors = [
    ("cadastre_base", "Cadastre Base Parcels"),
    ("watercourses", "Watercourses"),
    ("roads", "Roads"),
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

# Load Parchment Texture at the very top
print("Loading Parchment Texture overlay...")
if os.path.exists(parchment_path):
    parchment_layer = QgsRasterLayer(parchment_path, "Parchment Texture")
    if parchment_layer.isValid():
        project.addMapLayer(parchment_layer)
        # Set Multiply Blend Mode so it blends with the layers below
        parchment_layer.setBlendMode(QPainter.CompositionMode_Multiply)
        parchment_layer.triggerRepaint()
        print("Parchment Texture loaded and set to Multiply blend mode.")
    else:
        print("Parchment Texture layer invalid.")
else:
    print(f"Parchment file not found at {parchment_path}")

# 3. Apply Styling
# Watercourses: Symbolize by size (stream order) and perenniality
if "watercourses" in loaded_layers:
    water_layer = loaded_layers["watercourses"]
    
    # Create Rule-Based Renderer
    # We will use sepia/dark indigo colors: #053061 (dark indigo) or #3c2d1e (sepia dark)
    water_color = "#1c4e80"
    
    # 1. Perennial, Major size (Order >= 5 or hierarchy = Major)
    sym_per_maj = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.8'})
    # 2. Perennial, Medium size (Order 3, 4)
    sym_per_med = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.5'})
    # 3. Perennial, Minor size (Order <= 2 or None)
    sym_per_min = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.25'})
    
    # 4. Intermittent/Ephemeral/Unknown, Major size (Dashed)
    sym_int_maj = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.8', 'line_style': 'dash'})
    # 5. Intermittent/Ephemeral/Unknown, Medium size (Dashed)
    sym_int_med = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.5', 'line_style': 'dash'})
    # 6. Intermittent/Ephemeral/Unknown, Minor size (Dashed)
    sym_int_min = QgsLineSymbol.createSimple({'color': water_color, 'width': '0.25', 'line_style': 'dash'})
    
    root_rule = QgsRuleBasedRenderer.Rule(None)
    
    # Rules definitions
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
    water_layer.triggerRepaint()
    print("Styled watercourses by Strahler stream order & perenniality.")

# Bus Stops: Point Clustering
if "bus_stops" in loaded_layers:
    stops_layer = loaded_layers["bus_stops"]
    
    # Define a clean warm-sepia brown symbol for clustered marker
    cluster_symbol = QgsMarkerSymbol.createSimple({
        'name': 'circle',
        'color': '#8c510a',      # Sepia brown
        'size': '8.0',
        'outline_color': '#ffffff',
        'outline_width': '0.4'
    })
    
    # Create original point symbol for unclustered single points
    single_symbol = QgsMarkerSymbol.createSimple({
        'name': 'circle',
        'color': '#dfc27d',      # Soft sepia gold
        'size': '3.0',
        'outline_color': '#8c510a',
        'outline_width': '0.3'
    })
    
    # Point cluster renderer
    stops_layer.setRenderer(QgsSingleSymbolRenderer(single_symbol)) # set source renderer
    
    cluster_renderer = QgsPointClusterRenderer()
    cluster_renderer.setSourceRenderer(stops_layer.renderer().clone())
    cluster_renderer.setClusterSymbol(cluster_symbol)
    cluster_renderer.setTolerance(12.0) # Search radius in pixels
    
    stops_layer.setRenderer(cluster_renderer)
    stops_layer.triggerRepaint()
    print("Configured bus stops clustering.")

# Roads: Sepia/Old-map style categorized renderer
if "roads" in loaded_layers:
    roads_layer = loaded_layers["roads"]
    
    # State controlled: Muted rust red
    sym_state = QgsLineSymbol.createSimple({'color': '#a50f15', 'width': '0.6'})
    # Local controlled: Faded sepia/brown
    sym_local = QgsLineSymbol.createSimple({'color': '#5c3a21', 'width': '0.25'})
    
    cat_state = QgsRendererCategory("T", sym_state, "State Controlled")
    cat_local = QgsRendererCategory("F", sym_local, "Local Controlled")
    cat_unk = QgsRendererCategory("U", sym_local, "Unknown Control")
    
    renderer = QgsCategorizedSymbolRenderer("scr_indicator", [cat_state, cat_local, cat_unk])
    roads_layer.setRenderer(renderer)
    
    # Rule-Based Labels: serif font Georgia, warm beige/parchment buffer halo
    label_settings = QgsPalLayerSettings()
    label_settings.fieldName = "road_name_full"
    label_settings.isExpression = False
    label_settings.filterExpression = "class IN ('Highway', 'Secondary', 'Connector')"
    label_settings.enabled = True
    
    text_format = QgsTextFormat()
    text_format.setFont(QFont("Georgia", 8))
    text_format.setColor(QColor("#2b2b2b"))
    
    # Warm beige/parchment color halo to blend with background
    buffer_settings = QgsTextBufferSettings()
    buffer_settings.setEnabled(True)
    buffer_settings.setSize(1.0)
    buffer_settings.setColor(QColor("#f5ecd7"))
    text_format.setBuffer(buffer_settings)
    
    label_settings.setFormat(text_format)
    roads_layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
    roads_layer.setLabelsEnabled(True)
    roads_layer.triggerRepaint()
    print("Styled and labeled roads.")

# Cadastre: Faded thin outline, invisible above 1:25,000
if "cadastre_base" in loaded_layers:
    cad_layer = loaded_layers["cadastre_base"]
    cad_symbol = QgsFillSymbol.createSimple({
        'color': '0,0,0,0',
        'outline_color': '#cccccc',
        'outline_width': '0.08'
    })
    cad_layer.setRenderer(QgsSingleSymbolRenderer(cad_symbol))
    
    # Scale dependent visibility
    cad_layer.setScaleBasedVisibility(True)
    cad_layer.setMinimumScale(25000.0)
    cad_layer.setMaximumScale(0.0)
    cad_layer.triggerRepaint()
    print("Styled and set scale visibility for cadastre.")

# Bus Routes: Thin faded sepia line
if "bus_routes" in loaded_layers:
    routes_layer = loaded_layers["bus_routes"]
    routes_symbol = QgsLineSymbol.createSimple({'color': '#807e7a', 'width': '0.3', 'line_style': 'dot'})
    routes_layer.setRenderer(QgsSingleSymbolRenderer(routes_symbol))
    routes_layer.triggerRepaint()
    print("Styled bus routes.")

# Zoom map canvas to the layers
if loaded_layers:
    extent = None
    for name, layer in loaded_layers.items():
        if name == "cadastre_base" or name == "watercourses":
            continue # Don't zoom to the entire cadastre or watercourses extent
        ext = layer.extent()
        if extent is None:
            extent = ext
        else:
            extent.combineExtentWith(ext)
            
    import qgis.utils
    if extent and qgis.utils.iface is not None:
        qgis.utils.iface.mapCanvas().setExtent(extent)
        qgis.utils.iface.mapCanvas().refresh()
        print("Canvas extent reset and refreshed.")

# Save QGIS project
project.write()
print("QGIS project file saved successfully.")
