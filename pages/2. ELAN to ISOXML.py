import streamlit as st
import zipfile
import os
import geopandas as gpd
import xml.etree.ElementTree as ET

def process_shapefile(shp_path):
    # Read the shapefile using GeoPandas
    gdf = gpd.read_file(shp_path)
    # Transform the geometries to EPSG:4326 (WGS 84)
    gdf = gdf.to_crs(epsg=4326)

    # Example structure from your provided XML example
    root = ET.Element("ISO11783_TaskData", {
        "VersionMajor": "4",
        "VersionMinor": "0",
        "ManagementSoftwareManufacturer": "Lorenz Bauer",
        "ManagementSoftwareVersion": "01.12.2023",
        "DataTransferOrigin": "1"
    })

    # Adding CTR and FRM elements as static elements, since they seem to be constants
    ctr_element = ET.SubElement(root, "CTR", {"A": "CTR1", "B": "Standard"})
    frm_element = ET.SubElement(root, "FRM", {"A": "FRM1", "B": "Standard", "I": "CTR1"})

    # Create a list to hold all PFD elements
    pfd_elements = []

    for idx, row in gdf.iterrows():
        polygon_name = row['SCHLAGBEZ'].replace(".", "_").replace(" ", "_").replace("(", "").replace(")", "")

        # Create PFD element for each feature
        pfd_element = ET.Element("PFD", {
            "A": f"PFD{idx+1}",
            "C": polygon_name,
            "E": "CTR1",
            "F": "FRM1"
        })

        # Create PLN element
        pln_element = ET.SubElement(pfd_element, "PLN", {
            "A": "1",
            "B": polygon_name
        })

        # Create LSG element
        lsg_element = ET.SubElement(pln_element, "LSG", {"A": "1"})

        # Extracting points from the exterior geometry only (ignoring interiors/holes)
        if row.geometry.geom_type == 'Polygon':
            exterior_coords = row.geometry.exterior.coords
            for i, coord in enumerate(exterior_coords):
                ET.SubElement(lsg_element, "PNT", {
                    "A": "2",
                    "C": str(coord[1]),  # Latitude
                    "D": str(coord[0])   # Longitude
                })
        elif row.geometry.geom_type == 'MultiPolygon':
            # Handle MultiPolygons by taking only the exterior of each polygon
            for polygon in row.geometry:
                exterior_coords = polygon.exterior.coords
                for i, coord in enumerate(exterior_coords):
                    ET.SubElement(lsg_element, "PNT", {
                        "A": "2",
                        "C": str(coord[1]),  # Latitude
                        "D": str(coord[0])   # Longitude
                    })

        # Add the PFD element to the list
        pfd_elements.append(pfd_element)

    # Sort the PFD elements by the value of the "C" attribute (which is the field name)
    pfd_elements.sort(key=lambda x: x.attrib["C"])

    # Add the sorted PFD elements to the root
    for pfd in pfd_elements:
        root.append(pfd)

    # Convert the XML tree to a string
    tree = ET.ElementTree(root)
    return tree, gdf.crs.to_epsg()

def save_xml(tree, output_path):
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

# Streamlit app
st.set_page_config(page_title="AMA to ISOXML Converter", layout="centered", page_icon="📍")
st.title("AMA to ISOXML Converter")


# File uploader
uploaded_zip = st.file_uploader("Hier die zip-Datei von EAMA hochladen", type="zip")

if uploaded_zip is not None:
    # Create a temporary directory
    with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
        zip_ref.extractall("temp_dir")
    
    # Look for the shapefile in the extracted files
    shp_path = None
    for root, _, files in os.walk("temp_dir"):
        for file in files:
            if file.endswith(".shp"):
                shp_path = os.path.join(root, file)
                break
    
    if shp_path is None:
        st.error("No .shp file found in the uploaded ZIP.")
    else:
        st.success(f"Shapefile found: {shp_path}")
        
        # Process the shapefile and convert it to XML, get EPSG code, SCHLAGBEZ values, and geodata
        xml_tree, epsg_code = process_shapefile(shp_path)
        
        # Display the EPSG code
        if epsg_code is not None:
            st.write(f"EPSG Code: {epsg_code}")
        else:
            st.warning("EPSG code could not be determined.")
        
        # Save the XML to a file
        output_xml_path = "TASKDATA.XML"
        save_xml(xml_tree, output_xml_path)
        
        # Allow the user to download the generated XML file
        with open(output_xml_path, "rb") as f:
            st.download_button(
                label="Download XML",
                data=f,
                file_name="TASKDATA.XML",
                mime="application/xml"
            )
    
    # Clean up the temporary directory
    for root, _, files in os.walk("temp_dir"):
        for file in files:
            os.remove(os.path.join(root, file))
        os.rmdir(root)
