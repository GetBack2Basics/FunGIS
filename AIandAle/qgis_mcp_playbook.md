# QGIS MCP Playbook & Cheat Sheet

This playbook explains how to get the QGIS MCP (Model Context Protocol) socket server up and running on Windows, ingest spatial datasets, and execute PyQGIS scripts programmatically over TCP socket port `9876`.

---

## 1. Quick Start Architecture

The QGIS MCP system works by running a TCP socket listener on port `9876` inside QGIS Desktop via a plugin. Python client scripts send length-prefixed JSON payloads to execute code in the QGIS Python environment.

```
+--------------------------+                 +--------------------------+
|  External Python Client  | --(TCP: 9876)-->|   Running QGIS Session   |
|   (run_pyqgis_code.py)   |                 | (qgis_mcp_plugin Active) |
+--------------------------+                 +--------------------------+
```

---

## 2. Launching QGIS with the Project

Always launch QGIS using the included environment launcher to ensure DLLs are resolved correctly:

```powershell
# Detaches from shell so QGIS persists
powershell -Command "Start-Process -FilePath 'C:\projects\fungis\aiandale\launch_qgis.bat' -WindowStyle Hidden"
```

The launcher will:
- Detect the OSGeo4W installation (supports both dev and LTR paths).
- Initialize environments (`o4w_env.bat`, `qt6_env.bat`/`qt5_env.bat`, GDAL/PDAL environments).
- Add `%OSGEO4W_ROOT%\apps\<qgis_app>\bin` to `PATH` (resolves DLL not found errors).
- Launch the QGIS desktop session and automatically load the active project.

---

## 3. General Data Ingestion CLI

Instead of writing custom scripts per dataset, use the generalized ingestion runner [`ingest_spatial_data.py`](file:///C:/projects/fungis/aiandale/ingest_spatial_data.py). 

Run this script under the QGIS Python environment wrapper (`python-qgis-dev.bat` or `python-qgis-ltr.bat`) so it has access to the standalone `qgis.core` environment for writing directly to GeoPackage database files.

### 3.1. Ingest ArcGIS REST Service Layers
Query features within a bounding box and page them automatically into a GeoPackage:
```powershell
# Ingest Queensland Cadastre Base Parcels
C:\OSGeo4W\bin\python-qgis-dev.bat C:\projects\fungis\aiandale\ingest_spatial_data.py `
  --type arcgis `
  --url "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer/8" `
  --bbox "145.65,-17.15,145.85,-16.75" `
  --fields "objectid,lot,plan,tenure,lot_area,parcel_typ" `
  --gpkg "C:\projects\fungis\aiandale\data\cairns_infrastructure.gpkg" `
  --layer-name "cadastre_base"
```

### 3.2. Ingest GTFS Transit Data
Parse bus stops and routes from a Translink GTFS zip:
```powershell
# Ingest GTFS Bus Stops & Routes
C:\OSGeo4W\bin\python-qgis-dev.bat C:\projects\fungis\aiandale\ingest_spatial_data.py `
  --type gtfs `
  --url "https://transitfeeds.com/p/translink/21/latest/download" `
  --gpkg "C:\projects\fungis\aiandale\data\cairns_infrastructure.gpkg"
```

---

## 4. Running Scripts inside QGIS

Use `run_pyqgis_code.py` to send and run any script directly inside the active QGIS session:

```powershell
python C:\projects\fungis\aiandale\run_pyqgis_code.py C:\projects\fungis\aiandale\my_pyqgis_script.py
```

---

## 5. PyQGIS Cheat Sheet

These are the most common and useful PyQGIS snippets discovered during our Cairns mapping project.

### 5.1. Accessing Layers & Project
```python
from qgis.core import QgsProject

project = QgsProject.instance()

# Fetch layer by name
layer = project.mapLayersByName("Roads")[0]

# Add layer from GeoPackage
gpkg_path = "C:/projects/fungis/aiandale/data/cairns_infrastructure.gpkg"
source_uri = f"{gpkg_path}|layername=roads"
roads_layer = QgsVectorLayer(source_uri, "Roads", "ogr")
if roads_layer.isValid():
    project.addMapLayer(roads_layer)
```

### 5.2. Scale-Dependent Visibility (Performance Best Practice)
To prevent QGIS from freezing on startup when loading massive polygon datasets (e.g. 80,000 cadastre parcels):
```python
# Enable scale visibility
cad_layer.setScaleBasedVisibility(True)

# Set minimum scale (only visible when zoomed in closer than 1:25,000)
# MinimumScale represents the maximum scale denominator at which the layer is visible.
cad_layer.setMinimumScale(25000.0)
cad_layer.setMaximumScale(0.0) # 0.0 means no limit on zooming in
```

### 5.3. Categorized Symbology
```python
from qgis.core import QgsLineSymbol, QgsCategorizedSymbolRenderer, QgsRendererCategory

# Create custom line symbols
symbol_state = QgsLineSymbol.createSimple({'color': '#e31a1c', 'width': '0.8'})
symbol_local = QgsLineSymbol.createSimple({'color': '#fb9a99', 'width': '0.3'})

# Map symbols to category values
cat_state = QgsRendererCategory("T", symbol_state, "State Controlled")
cat_local = QgsRendererCategory("F", symbol_local, "Local Controlled")
cat_unk   = QgsRendererCategory("U", symbol_local, "Unknown Control")

renderer = QgsCategorizedSymbolRenderer("scr_indicator", [cat_state, cat_local, cat_unk])
roads_layer.setRenderer(renderer)
roads_layer.triggerRepaint()
```

### 5.4. Rule-Based Labeling with Halos (Text Buffers)
To label roads while avoiding clutter:
```python
from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings
from qgis.PyQt.QtGui import QColor, QFont

label_settings = QgsPalLayerSettings()
label_settings.fieldName = "road_name_full"
label_settings.isExpression = False
# Filter to major roads only
label_settings.filterExpression = "class IN ('Highway', 'Secondary', 'Connector')"
label_settings.enabled = True

text_format = QgsTextFormat()
text_format.setFont(QFont("Arial", 8))
text_format.setColor(QColor("#222222"))

# Add a text halo buffer for visibility over dark background layers
buffer_settings = QgsTextBufferSettings()
buffer_settings.setEnabled(True)
buffer_settings.setSize(1.0)
buffer_settings.setColor(QColor("#ffffff"))
text_format.setBuffer(buffer_settings)

label_settings.setFormat(text_format)
roads_layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
roads_layer.setLabelsEnabled(True)
roads_layer.triggerRepaint()
```

### 5.5. Running Processing Tools (Buffer & Select)
Run native tools inside QGIS using projected metric coordinates for accuracy:
```python
import processing

# Reproject layers to projected CRS (e.g. UTM Zone 55S / GDA2020: EPSG:7855)
proj_stops = processing.run("native:reprojectlayer", {
    'INPUT': stops_layer,
    'TARGET_CRS': 'EPSG:7855',
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']

# Buffer points by 20 meters
buffered_stops = processing.run("native:buffer", {
    'INPUT': proj_stops,
    'DISTANCE': 20,
    'DISSOLVE': True,
    'OUTPUT': 'TEMPORARY_OUTPUT'
})['OUTPUT']
```

### 5.6. Canvas Zoom & Render to Image
```python
# Zoom to combined layer extents
extent = layer1.extent()
extent.combineExtentWith(layer2.extent())
iface.mapCanvas().setExtent(extent)
iface.mapCanvas().refresh()

# Save canvas to PNG file
iface.mapCanvas().saveAsImage("C:/projects/fungis/aiandale/render_enhanced.png")
```
