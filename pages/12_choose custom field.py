import streamlit as st
import geopandas as gpd
import zipfile
import os
import tempfile
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

# --- Function to extract shapefile(s) from uploaded files ---
def extract_shp_files(uploaded_files):
    """
    Searches through the uploaded files and extracts any .shp files.
    If a ZIP archive is uploaded, it extracts its contents and searches for .shp files.
    Returns a list of paths to the shapefiles and the TemporaryDirectory object.
    """
    shp_paths = []
    temp_dir = tempfile.TemporaryDirectory()
    temp_path = temp_dir.name

    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        # If file is a ZIP archive, extract and search for shapefiles
        if filename.lower().endswith('.zip'):
            with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
            # Walk through extracted files to find .shp files
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    if file.lower().endswith('.shp'):
                        shp_paths.append(os.path.join(root, file))
        # If file is a shapefile, save it directly to temp_path
        elif filename.lower().endswith('.shp'):
            file_path = os.path.join(temp_path, filename)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            shp_paths.append(file_path)

    return shp_paths, temp_dir

# --- Function to process the shapefile and generate XML ---
def process_shapefile(shp_path, name_field):
    """
    Reads the shapefile, transforms to EPSG:4326, and generates an XML tree.
    The chosen field (or "id") is used to derive the polygon name.
    Coordinates are rounded to 9 decimal places.
    """
    # Read the shapefile using GeoPandas
    gdf = gpd.read_file(shp_path)
    # Transform geometries to EPSG:4326 (WGS84)
    gdf = gdf.to_crs(epsg=4326)
    
    # Create XML root element with static attributes
    root = ET.Element("ISO11783_TaskData", {
        "VersionMajor": "4",
        "VersionMinor": "0",
        "ManagementSoftwareManufacturer": "Geodata to ISOXML Converter",
        "ManagementSoftwareVersion": "12.09.2024",
        "DataTransferOrigin": "1"
    })
    # Static elements CTR and FRM
    ET.SubElement(root, "CTR", {"A": "CTR1", "B": "Standard"})
    ET.SubElement(root, "FRM", {"A": "FRM1", "B": "Standard", "I": "CTR1"})

    pfd_elements = []

    for idx, row in gdf.iterrows():
        # Choose the name based on the dropdown selection
        if name_field == "id":
            polygon_name = f"PFD{idx+1}"
        else:
            polygon_name = str(row[name_field])
            polygon_name = polygon_name.replace(".", "_").replace(" ", "_").replace("(", "").replace(")", "")
        
        # Create PFD element
        pfd_element = ET.Element("PFD", {
            "A": f"PFD{idx+1}",
            "C": polygon_name,
            "E": "CTR1",
            "F": "FRM1"
        })
        # Create PLN element inside PFD
        pln_element = ET.SubElement(pfd_element, "PLN", {
            "A": "1",
            "B": polygon_name
        })
        # Create LSG element inside PLN
        lsg_element = ET.SubElement(pln_element, "LSG", {"A": "1"})

        # Extract coordinates from geometry
        geom = row.geometry
        if geom.geom_type == 'Polygon':
            exterior_coords = geom.exterior.coords
            for coord in exterior_coords:
                lat = f"{coord[1]:.9f}"
                lon = f"{coord[0]:.9f}"
                ET.SubElement(lsg_element, "PNT", {
                    "A": "2",
                    "C": lat,  # Latitude rounded to 9 decimals
                    "D": lon   # Longitude rounded to 9 decimals
                })
        elif geom.geom_type == 'MultiPolygon':
            # Handle MultiPolygons by processing each polygon's exterior
            for polygon in geom:
                exterior_coords = polygon.exterior.coords
                for coord in exterior_coords:
                    lat = f"{coord[1]:.9f}"
                    lon = f"{coord[0]:.9f}"
                    ET.SubElement(lsg_element, "PNT", {
                        "A": "2",
                        "C": lat,
                        "D": lon
                    })
        # Add element to list
        pfd_elements.append(pfd_element)

    # Sort the PFD elements by the value of the "C" attribute (polygon name)
    pfd_elements.sort(key=lambda x: x.attrib["C"])
    # Append sorted elements to the root
    for pfd in pfd_elements:
        root.append(pfd)

    # Create XML tree
    tree = ET.ElementTree(root)
    return tree, gdf

# --- Function to pretty print and save XML ---
def save_xml(tree, output_path):
    xml_str = ET.tostring(tree.getroot(), encoding="utf-8")
    dom = minidom.parseString(xml_str)
    pretty_xml_as_string = dom.toprettyxml(indent="    ", newl="\n")
    pretty_xml_as_string = "\n".join([line for line in pretty_xml_as_string.splitlines() if line.strip()])
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml_as_string)

# --- Streamlit App Layout ---
st.set_page_config(page_title="Shapefile to ISOXML Converter", layout="centered", page_icon="📍")
st.title("Shapefile to ISOXML Converter")
st.write("Upload a ZIP file containing shapefiles, or individual .shp files.")

# Upload files (ZIP or SHP)
uploaded_files = st.file_uploader("Upload files", type=["zip", "shp"], accept_multiple_files=True)

if uploaded_files:
    shp_paths, temp_dir = extract_shp_files(uploaded_files)
    
    if not shp_paths:
        st.error("No shapefile (.shp) was found in the uploaded files.")
    else:
        st.success(f"Found {len(shp_paths)} shapefile(s).")
        
        # For this example, we take the first shapefile found
        shp_path = shp_paths[0]
        st.write(f"**Shapefile Path:** {shp_path}")
        
        try:
            # Read shapefile using geopandas
            gdf = gpd.read_file(shp_path)
            rows, cols = gdf.shape
            st.write(f"**Rows:** {rows} | **Columns:** {cols}")
            st.write("### Shapefile Data Preview")
            # Display first 100 rows (excluding the geometry column)
            if "geometry" in gdf.columns:
                st.dataframe(gdf.drop(columns=["geometry"]).head(100))
            else:
                st.dataframe(gdf.head(100))
        except Exception as e:
            st.error(f"Error reading shapefile: {e}")

        # List available fields for naming (plus an extra "id" option)
        available_fields = ["id"]
        available_fields.extend([col for col in gdf.columns if col != "geometry"])
        name_field = st.selectbox("Choose a field for naming features", available_fields)
        
        # Button to generate XML
        if st.button("Generate XML"):
            try:
                xml_tree, gdf_transformed = process_shapefile(shp_path, name_field)
                # Save XML to a temporary file
                output_xml_path = os.path.join(temp_dir.name, "TASKDATA.XML")
                save_xml(xml_tree, output_xml_path)
                
                st.success("XML generated successfully!")
                # Option to download the XML file
                with open(output_xml_path, "rb") as f:
                    st.download_button(
                        label="Download XML",
                        data=f,
                        file_name="TASKDATA.XML",
                        mime="application/xml"
                    )
            except Exception as e:
                st.error(f"Error generating XML: {e}")
    
    # Clean up temporary directory
    temp_dir.cleanup()
