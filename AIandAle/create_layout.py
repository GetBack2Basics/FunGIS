import os
import sys
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsRectangle,
    QgsPrintLayout,
    QgsLayoutItemMap,
    QgsLayoutItemLegend,
    QgsLayoutItemScaleBar,
    QgsLayoutItemLabel,
    QgsLayoutItemPicture,
    QgsLayoutItemAttributeTable,
    QgsLayoutTableColumn,
    QgsLayoutSize,
    QgsLayoutPoint,
    QgsUnitTypes,
    QgsLayoutExporter
)
from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtGui import QColor, QFont, QPainter

def main():
    print("Initializing standalone QgsApplication...")
    qgs = QgsApplication([], False)
    qgs.initQgis()

    project = QgsProject.instance()
    project_path = "C:/Projects/FunGIS/aiandale/aiandale.qgz"
    if not project.read(project_path):
        print(f"Failed to read project: {project_path}")
        qgs.exitQgis()
        return

    # Get heritage sites layer
    layers = project.mapLayersByName("Heritage Sites")
    if not layers:
        print("Heritage Sites layer not found in project.")
        qgs.exitQgis()
        return
    heritage_layer = layers[0]

    # --- 0. Clean & Round Database Attributes ---
    print("Formatting and rounding database attributes for the table...")
    heritage_layer.startEditing()
    for feat in heritage_layer.getFeatures():
        dist = feat["walk_dist_m"]
        if dist > 0:
            feat["walk_dist_m"] = round(dist, 1)
            feat["walk_time_min"] = round(dist / 80.0, 1) # 4.8 km/h walking speed
            heritage_layer.updateFeature(feat)
    heritage_layer.commitChanges()
    print("Database formatting committed successfully.")

    # Remove layout if it already exists
    manager = project.layoutManager()
    existing_layout = manager.layoutByName("Heritage Walk Layout")
    if existing_layout:
        manager.removeLayout(existing_layout)
        print("Removed existing layout.")

    # Create new layout
    layout = QgsPrintLayout(project)
    layout.initializeDefaults() # Sets up A4 landscape
    layout.setName("Heritage Walk Layout")
    manager.addLayout(layout)
    print("Created new Print Layout: Heritage Walk Layout")

    # --- 1. Map Item ---
    print("Adding Map Item...")
    map_item = QgsLayoutItemMap(layout)
    map_item.attemptMove(QgsLayoutPoint(10, 10, QgsUnitTypes.LayoutMillimeters))
    map_item.attemptResize(QgsLayoutSize(170, 190, QgsUnitTypes.LayoutMillimeters))
    
    # Zoom to Cairns BBox
    extent = QgsRectangle(145.65, -17.15, 145.85, -16.75)
    map_item.setExtent(extent)
    
    # Set layers list excluding the Parchment Texture layer to prevent rendering crashes
    project_layers = list(project.mapLayers().values())
    layout_layers = [lyr for lyr in project_layers if lyr.name() != "Parchment Texture"]
    map_item.setLayers(layout_layers)
    layout.addLayoutItem(map_item)

    # --- 2. Attribute Table (Walking Distances) ---
    print("Adding Attribute Table...")
    table = QgsLayoutItemAttributeTable(layout)
    table.setVectorLayer(heritage_layer)

    # Configure columns
    col1 = QgsLayoutTableColumn()
    col1.setAttribute("name")
    col1.setHeading("Heritage Place")
    col1.setWidth(52) # mm width

    col2 = QgsLayoutTableColumn()
    col2.setAttribute("walk_dist_m")
    col2.setHeading("Dist (m)")
    col2.setWidth(20)
    col2.setSortOrder(Qt.AscendingOrder) # Sort by distance ascending!

    col3 = QgsLayoutTableColumn()
    col3.setAttribute("walk_time_min")
    col3.setHeading("Walk (min)")
    col3.setWidth(22)

    table.setColumns([col1, col2, col3])
    table.setSortColumns([col2]) # Force table to sort by walk_dist_m ascending!
    table.setMaximumNumberOfFeatures(11) # Header + top 10 features
    table.setFeatureFilter("walk_dist_m > 0")
    table.setFilterFeatures(True)
    
    # Enable classic styles
    table.setBackgroundColor(QColor("#ffffff"))
    table.setGridColor(QColor("#cccccc"))
    
    # Create QgsLayoutFrame to hold the table
    from qgis.core import QgsLayoutFrame
    frame = QgsLayoutFrame(layout, table)
    frame.attemptMove(QgsLayoutPoint(190, 25, QgsUnitTypes.LayoutMillimeters))
    frame.attemptResize(QgsLayoutSize(97, 95, QgsUnitTypes.LayoutMillimeters))
    
    # Register frame with multi-frame table so it gets drawn and serialized
    table.addFrame(frame)
    
    # Add table and frame to layout
    layout.addMultiFrame(table)
    layout.addLayoutItem(frame)

    # --- 3. Title ---
    print("Adding Title...")
    title = QgsLayoutItemLabel(layout)
    title.setText("Cairns Historical Sites\nWalking Routes")
    title.setMargin(0.0)
    title.setHAlign(Qt.AlignCenter)
    title.attemptMove(QgsLayoutPoint(190, 10, QgsUnitTypes.LayoutMillimeters))
    title.attemptResize(QgsLayoutSize(97, 12, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(title)

    # --- 4. Legend ---
    print("Adding Legend...")
    legend = QgsLayoutItemLegend(layout)
    legend.setLinkedMap(map_item)
    legend.attemptMove(QgsLayoutPoint(190, 125, QgsUnitTypes.LayoutMillimeters))
    legend.attemptResize(QgsLayoutSize(97, 55, QgsUnitTypes.LayoutMillimeters))
    legend.setTitle("Map Legend")
    legend.setFrameEnabled(False) # Turn off border frame for modern clean look
    
    # Auto-update false so we can clean up legend items (hide background and base layers)
    legend.setAutoUpdateModel(False)
    root = legend.model().rootGroup()
    nodes_to_remove = []
    # Keep ONLY Bus Stops and Heritage Sites in the legend
    for child in root.children():
        if child.name() not in ["Bus Stops", "Heritage Sites"]:
            nodes_to_remove.append(child)
    for node in nodes_to_remove:
        root.removeChildNode(node)
        
    layout.addLayoutItem(legend)

    # --- 5. Scale Bar ---
    print("Adding Scale Bar...")
    scalebar = QgsLayoutItemScaleBar(layout)
    scalebar.setLinkedMap(map_item)
    scalebar.setUnits(QgsUnitTypes.DistanceKilometers)
    scalebar.setNumberOfSegments(3)
    scalebar.setStyle("Double Box")
    scalebar.attemptMove(QgsLayoutPoint(15, 182, QgsUnitTypes.LayoutMillimeters))
    scalebar.attemptResize(QgsLayoutSize(50, 10, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scalebar)

    # --- 6. North Arrow Picture ---
    print("Adding North Arrow...")
    picture = QgsLayoutItemPicture(layout)
    svg_dir = "C:/Users/corea/AppData/Local/Programs/OSGeo4W/apps/qgis-ltr/svg/arrows"
    svg_path = ""
    if os.path.exists(svg_dir):
        for f in os.listdir(svg_dir):
            if f.endswith(".svg") and "north" in f.lower():
                svg_path = os.path.join(svg_dir, f).replace("\\", "/")
                break
    
    if not svg_path:
        # Fallback to Arrow_01 if NorthArrow not found
        svg_path = "C:/Users/corea/AppData/Local/Programs/OSGeo4W/apps/qgis-ltr/svg/arrows/Arrow_01.svg"

    if os.path.exists(svg_path):
        picture.setPicturePath(svg_path)
        print(f"Using North Arrow SVG: {svg_path}")
    else:
        print("North Arrow SVG file not found.")

    picture.attemptMove(QgsLayoutPoint(160, 15, QgsUnitTypes.LayoutMillimeters))
    picture.attemptResize(QgsLayoutSize(15, 15, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(picture)

    # --- 7. Attributions ---
    print("Adding Attributions...")
    attribution = QgsLayoutItemLabel(layout)
    attribution.setText("Sources: Queensland Heritage Register, Translink. Base map: ESRI World Hillshade.\nWalking paths network distances computed via OSRM from Esplanade Lagoon.\nRights © 2026 Queensland Government. Cartography: Antigravity.")
    attribution.setHAlign(Qt.AlignLeft)
    attribution.attemptMove(QgsLayoutPoint(190, 185, QgsUnitTypes.LayoutMillimeters))
    attribution.attemptResize(QgsLayoutSize(97, 15, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(attribution)

    # Save QGIS project with layout
    project.write()
    print("Saved QGIS project with print layout.")

    # --- 8. Export Layout to Image ---
    print("Exporting Print Layout to image...")
    exporter = QgsLayoutExporter(layout)
    settings = QgsLayoutExporter.ImageExportSettings()
    settings.dpi = 300 # 300 dpi print quality
    
    export_path = "C:/Projects/FunGIS/aiandale/render_layout.png"
    result = exporter.exportToImage(export_path, settings)
    if result == QgsLayoutExporter.Success:
        print(f"Print Layout successfully exported to {export_path}")
    else:
        print(f"Failed to export Print Layout. Code: {result}")

    qgs.exitQgis()
    print("QgsApplication exited.")

if __name__ == "__main__":
    main()
