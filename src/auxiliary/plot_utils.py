import sys
from pathlib import Path
import logging
import pickle
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
from read_geojson import read_geojson

# Ensure the project root is in sys.path
current_file = Path(__file__).resolve()
for parent in current_file.parents:
    if parent.name == "processing-root-folder":
        project_root = parent
        break
else:
    raise RuntimeError("Project root 'processing-root-folder' not found")
sys.path.append(str(project_root))

def plot_band_from_preprocessed(root_dir: Path, band_name: str = "B02", cmap: str = "viridis") -> bool:
    """
    Plot preprocessed band data with AOI overlay.
    This version adapts to a pickle file structure where the outer dictionary key
    is the product name and its value is the band container.
    """
    try:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        
        preprocessed_dir = root_dir / "data" / "preprocessed"
        logging.info(f"Looking for data in: {preprocessed_dir}")
        
        # Look for pickle files recursively.
        pickle_files = list(preprocessed_dir.rglob("*.pkl"))
        if not pickle_files:
            logging.error(f"No pickle files found in {preprocessed_dir}")
            return False
        
        # Load the first available pickle file.
        data_file = pickle_files[0]
        logging.info(f"Loading data from: {data_file}")
        with open(data_file, "rb") as f:
            products = pickle.load(f)
        
        # Get first product name and its data.
        product_name = list(products.keys())[0]
        product_data = products[product_name]
        
        # If the product data is wrapped under a "bands" key, use it;
        # otherwise assume the product_data itself holds the band arrays.
        if isinstance(product_data, dict) and "bands" in product_data:
            band_container = product_data["bands"]
        else:
            band_container = product_data
        
        if band_name not in band_container:
            available_bands = list(band_container.keys())
            logging.error(f"Band '{band_name}' not found in product '{product_name}'. Available keys: {available_bands}")
            return False
        
        # Retrieve the requested band data.
        band_data = band_container[band_name]
        
        # Load AOI boundary using our reader.
        aoi_path = root_dir / "data" / "external" / "municipio_1_Rome.geojson"
        geojson_data = read_geojson(aoi_path)
        if not geojson_data:
            logging.error("Failed to load AOI boundary")
            return False
        
        aoi = gpd.GeoDataFrame.from_features(geojson_data["features"])
        
        # Create a plot with the band data.
        fig, ax = plt.subplots(figsize=(12, 8))
        normalized_data = np.clip(band_data / np.max(band_data) * 255, 0, 255).astype(np.uint8)
        img = ax.imshow(normalized_data, cmap=cmap)
        plt.colorbar(img, ax=ax, label="Reflectance")
        
        aoi.boundary.plot(ax=ax, color="red", linewidth=2, label="Municipio 1")
        ax.set_title(f"{product_name} - Band {band_name} with AOI Boundary")
        ax.legend()
        
        # Save the plot.
        output_dir = root_dir / "results" / "plots"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{product_name}_{band_name}_with_boundary.png"
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()
        
        logging.info(f"Plot saved to {output_file}")
        return True
        
    except Exception as e:
        logging.error(f"Error plotting band: {str(e)}")
        return False

def plot_separate_figures(root_dir: Path, band_name: str = "B02") -> bool:
    """
    Create two separate figures:
    1. Band data visualization
    2. AOI boundary visualization
    """
    try:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        
        # Load band data
        preprocessed_dir = root_dir / "data" / "preprocessed"
        pickle_files = list(preprocessed_dir.rglob("*.pkl"))
        if not pickle_files:
            logging.error(f"No pickle files found in {preprocessed_dir}")
            return False
        
        data_file = pickle_files[0]
        logging.info(f"Loading band data from: {data_file}")
        with open(data_file, "rb") as f:
            products = pickle.load(f)
        
        # Get first product
        product_name = list(products.keys())[0]
        product_data = products[product_name]
        
        # Get band data
        band_container = product_data.get("bands", product_data)
        if band_name not in band_container:
            logging.error(f"Band {band_name} not found. Available: {list(band_container.keys())}")
            return False
        
        band_data = band_container[band_name]
        
        # Load AOI boundary
        aoi_path = root_dir / "data" / "external" / "municipio_1_Rome.geojson"
        geojson_data = read_geojson(aoi_path)
        if not geojson_data:
            logging.error("Failed to load AOI boundary")
            return False
        
        aoi = gpd.GeoDataFrame.from_features(geojson_data["features"])
        
        # Create output directory
        output_dir = root_dir / "results" / "plots"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Plot 1: Band Data
        fig1, ax1 = plt.subplots(figsize=(10, 8))
        normalized_data = np.clip(band_data / np.max(band_data) * 255, 0, 255).astype(np.uint8)
        img = ax1.imshow(normalized_data, cmap="viridis")
        plt.colorbar(img, ax=ax1, label="Reflectance")
        ax1.set_title(f"{product_name} - Band {band_name}")
        
        # Save band plot
        band_plot = output_dir / f"{product_name}_{band_name}.png"
        fig1.savefig(band_plot, dpi=300, bbox_inches="tight")
        plt.close(fig1)
        logging.info(f"Saved band plot to {band_plot}")
        
        # Plot 2: AOI Boundary
        fig2, ax2 = plt.subplots(figsize=(10, 8))
        aoi.plot(ax=ax2, edgecolor="red", facecolor="none", linewidth=2)
        ax2.set_title("Municipio 1 Boundary")
        
        # Save boundary plot
        boundary_plot = output_dir / "municipio_1_boundary.png"
        fig2.savefig(boundary_plot, dpi=300, bbox_inches="tight")
        plt.close(fig2)
        logging.info(f"Saved boundary plot to {boundary_plot}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error creating plots: {str(e)}")
        return False

if __name__ == "__main__":
    # Determine project root by finding folder named "processing-root-folder"
    for parent in current_file.parents:
        if parent.name == "processing-root-folder":
            root_dir = parent
            break
    else:
        raise RuntimeError("Project root 'processing-root-folder' not found")
    
    plot_band_from_preprocessed(root_dir, "B02")
    plot_separate_figures(root_dir, "B02")