"""
Processing module for Sentinel-2 data: RGB and NDVI generation
"""
import os
import logging
from pathlib import Path
import numpy as np
import rasterio
import matplotlib.pyplot as plt

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def process_sentinel_data(input_path: Path, output_path: Path):
    """Process Sentinel-2 data to generate RGB and NDVI images"""
    try:
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all GeoTIFF files
        tiff_files = list(input_path.glob("*.tif"))
        logging.info(f"Found {len(tiff_files)} GeoTIFF files")
        
        for tiff_file in tiff_files:
            logging.info(f"Processing {tiff_file.name}")
            
            with rasterio.open(tiff_file) as src:
                # Read bands (assuming order: B02, B03, B04, B08)
                blue = src.read(1).astype('float32')
                green = src.read(2).astype('float32')
                red = src.read(3).astype('float32')
                nir = src.read(4).astype('float32')
                
                # Get metadata for output files
                profile = src.profile
                
                # Scale to 8-bit RGB
                def scale_to_uint8(arr, lower=0, upper=3000):
                    arr = np.clip(arr, lower, upper)
                    return ((arr - lower) / (upper - lower) * 255).astype('uint8')
                
                rgb = np.stack([
                    scale_to_uint8(red),
                    scale_to_uint8(green),
                    scale_to_uint8(blue)
                ])
                
                # Calculate NDVI
                ndvi = np.where(
                    (nir + red) > 0,
                    (nir - red) / (nir + red),
                    0
                )
                ndvi = np.clip(ndvi, -1, 1)
                
                # Save RGB GeoTIFF
                rgb_profile = profile.copy()
                rgb_profile.update({
                    "driver": "GTiff",
                    "count": 3,
                    "dtype": "uint8",
                    "compress": "lzw"
                })
                
                rgb_path = output_path / f"{tiff_file.stem}_rgb.tif"
                with rasterio.open(rgb_path, "w", **rgb_profile) as dst:
                    dst.write(rgb)
                logging.info(f"Saved RGB image: {rgb_path}")
                
                # Save NDVI GeoTIFF
                ndvi_profile = profile.copy()
                ndvi_profile.update({
                    "driver": "GTiff",
                    "count": 1,
                    "dtype": "float32",
                    "compress": "lzw"
                })
                
                ndvi_path = output_path / f"{tiff_file.stem}_ndvi.tif"
                with rasterio.open(ndvi_path, "w", **ndvi_profile) as dst:
                    dst.write(ndvi, 1)
                logging.info(f"Saved NDVI image: {ndvi_path}")
                
                # Create preview image
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
                
                # RGB preview
                ax1.set_title("RGB True Color")
                ax1.imshow(np.transpose(rgb, (1, 2, 0)))
                ax1.axis('off')
                
                # NDVI preview
                ax2.set_title("NDVI")
                ndvi_plot = ax2.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
                plt.colorbar(ndvi_plot, ax=ax2)
                ax2.axis('off')
                
                preview_path = output_path / f"{tiff_file.stem}_preview.png"
                plt.savefig(preview_path, dpi=300, bbox_inches='tight')
                plt.close()
                logging.info(f"Saved preview: {preview_path}")
                
    except Exception as e:
        logging.error(f"Error processing data: {str(e)}")
        raise

def main():
    # Setup paths
    input_path = Path(r"C:\Users\fgalassi\Progetti\EO Pipeline\processing-root-folder\data\preprocessed\Sentinel-2\L2A")
    output_path = Path(r"C:\Users\fgalassi\Progetti\EO Pipeline\processing-root-folder\data\processed\Sentinel-2\L2A")
    
    # Setup logging
    setup_logging()
    
    # Process data
    logging.info("Starting processing...")
    process_sentinel_data(input_path, output_path)
    logging.info("Processing completed")

if __name__ == "__main__":
    main()