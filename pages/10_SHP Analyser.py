import streamlit as st
import geopandas as gpd
import zipfile
import os
import tempfile

def extract_shp_files(uploaded_files):
    """
    Searches through the uploaded files and extracts any .shp files.
    If a ZIP archive is uploaded, it extracts its contents and searches for .shp files.
    Returns a list of paths to the shapefiles.
    """
    shp_paths = []
    # Create a temporary directory to hold files
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
        # Optionally, you can add other file types or folder handling here if needed.

    return shp_paths, temp_dir

st.set_page_config(page_title="Shapefile Content Explorer", layout="centered", page_icon="📍")
st.title("Shapefile Content Explorer")

st.write("Upload a ZIP file containing shapefiles, or individual .shp files.")

# Allow multiple file uploads
uploaded_files = st.file_uploader("Upload files", type=["zip", "shp"], accept_multiple_files=True)

if uploaded_files:
    shp_paths, temp_dir = extract_shp_files(uploaded_files)
    
    if not shp_paths:
        st.error("No shapefile (.shp) was found in the uploaded files.")
    else:
        st.success(f"Found {len(shp_paths)} shapefile(s).")
        for shp in shp_paths:
            st.write(f"**Shapefile Path:** {shp}")
            try:
                # Read the shapefile with geopandas
                gdf = gpd.read_file(shp)
                rows, cols = gdf.shape
                st.write(f"**Rows:** {rows} | **Columns:** {cols}")
                st.write("### Shapefile Data Preview")
                # Display a table with variable names and content (first 10 rows) without the geometry column
                st.dataframe(gdf.drop(columns=["geometry"]).head(100))
                st.write("---")
            except Exception as e:
                st.error(f"Error reading shapefile {shp}: {e}")

    # Clean up temporary directory when done
    temp_dir.cleanup()
