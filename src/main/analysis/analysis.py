"""
Analysis module for classifying NDVI images into land cover classes
"""
import os
import sys
import logging
from pathlib import Path
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def read_ndvi(src: rasterio.DatasetReader) -> np.ndarray:
    """Read NDVI from L2A data (already processed)"""
    ndvi = src.read(1).astype('float32')
    logging.info(f"NDVI statistics:")
    logging.info(f"  Min: {np.min(ndvi):.3f}")
    logging.info(f"  Max: {np.max(ndvi):.3f}")
    logging.info(f"  Mean: {np.mean(ndvi):.3f}")
    return ndvi

def classify_ndvi(ndvi_array: np.ndarray) -> np.ndarray:
    """
    Classify NDVI values into land cover classes:
    0 - Unclassified (clouds)
    1 - Water (very low NDVI)
    2 - Built-up/Water (low-mid NDVI)
    3 - Vegetation (high NDVI)
    """
    classified = np.zeros_like(ndvi_array, dtype=np.uint8)
    
    # Thresholds adjusted for better cloud and water/building separation
    cloud_threshold = 0.75    # High reflectance indicates clouds
    water_threshold = 0.015    # Pure water bodies
    buildup_max = 0.39       # Buildings and mixed water pixels
    veg_threshold = 0.39     # Clear vegetation signal

    logging.info(f"Classification thresholds:")
    logging.info(f"  Clouds: NDVI > {cloud_threshold}")
    logging.info(f"  Water: NDVI < {water_threshold}")
    logging.info(f"  Built-up/Water: {water_threshold} ≤ NDVI ≤ {buildup_max}")
    logging.info(f"  Vegetation: NDVI > {veg_threshold}")
    
    # Clouds (unclassified)
    classified = np.where(ndvi_array > cloud_threshold, 0, classified)
    
    # Pure water bodies
    classified = np.where(
        (ndvi_array < water_threshold) & (ndvi_array <= cloud_threshold),
        1,
        classified
    )
    
    # Built-up areas and mixed water
    classified = np.where(
        (ndvi_array >= water_threshold) & (ndvi_array <= buildup_max),
        2,
        classified
    )
    
    # Vegetation (unchanged)
    classified = np.where(
        (ndvi_array > veg_threshold) & (ndvi_array <= cloud_threshold),
        3,
        classified
    )
    
    return classified

def plot_classification(classified: np.ndarray, output_path: Path, filename: str):
    """Create classification plot with legend and statistics"""
    # Define colors and labels
    colors = ['black', 'blue', 'gray', 'green']
    labels = ['Unclassified', 'Water', 'Built-up', 'Vegetation']
    cmap = ListedColormap(colors)
    
    # Create figure
    plt.figure(figsize=(12, 8))
    
    # Plot classification
    im = plt.imshow(classified, cmap=cmap)
    
    # Add title
    plt.title('Land Cover Classification', fontsize=12, pad=20)
    
    # Create custom legend
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=color, label=label)
                      for color, label in zip(colors, labels)]
    plt.legend(handles=legend_elements, 
              loc='center left', 
              bbox_to_anchor=(1, 0.5),
              title='Land Cover Types')
    
    # Calculate and display statistics
    total_pixels = classified.size
    stats = {label: np.sum(classified == i) / total_pixels * 100 
             for i, label in enumerate(labels)}
    
    # Add statistics text box
    stats_text = "Coverage Statistics:\n"
    stats_text += "\n".join(f"{label}: {stats[label]:.1f}%" 
                           for label in labels)
    plt.text(1.5, 0.02, stats_text, 
            transform=plt.gca().transAxes, 
            bbox=dict(facecolor='white', alpha=0.8))
    
    # Adjust layout
    plt.tight_layout()
    
    # Save plot
    output_path.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path / f"{filename}_classified.png", 
                dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Main function to run the analysis"""
    setup_logging()
    
    try:
        input_file = Path(r"C:\Users\fgalassi\Progetti\EO Pipeline\processing-root-folder\data\processed\Sentinel-2\L2A\S2B_MSIL2A_20250404T100029_N0511_R122_T32TQM_20250404T125144_bands_ndvi.tif")
        
        with rasterio.open(input_file) as src:
            ndvi = read_ndvi(src)
            classified = classify_ndvi(ndvi)
            
            # Save classification
            output_dir = input_file.parent.parent.parent / "analysis" / "Sentinel-2" / "L2A"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save GeoTIFF
            profile = src.profile.copy()
            profile.update(dtype=rasterio.uint8, count=1)
            out_tiff = output_dir / f"{input_file.stem}_classified.tif"
            with rasterio.open(out_tiff, 'w', **profile) as dst:
                dst.write(classified, 1)
            
            # Create visualization
            plot_classification(classified, output_dir, input_file.stem)
            
    except Exception as e:
        logging.error(f"Error in processing: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()