"""
Utilities for clipping Sentinel-2 data to Area of Interest (AOI)
"""

import logging
from pathlib import Path
from typing import Dict, Tuple, Optional
import rasterio
import geopandas as gpd
import numpy as np
from rasterio.mask import mask
from rasterio.warp import transform_geom
from shapely.geometry import box, mapping
import pickle

def clip_to_aoi(bands_data: Dict[str, Dict], aoi_file: Path, product_name: str) -> Tuple[Optional[Dict], Dict]:
    """
    Clip Sentinel-2 bands to Area of Interest using GeoJSON boundary
    """
    try:
        # Read AOI boundary
        aoi = gpd.read_file(aoi_file)
        logging.info(f"Loaded AOI boundary from: {aoi_file.absolute()}")

        # Get sample band for spatial reference
        sample_band_name = next(iter(bands_data['bands'].keys()))
        sample_band = bands_data['bands'][sample_band_name]
        
        # Transform AOI geometry to match raster CRS if needed
        if aoi.crs != bands_data['metadata']['crs']:
            aoi = aoi.to_crs(bands_data['metadata']['crs'])
            logging.info(f"Transformed AOI to match raster CRS: {bands_data['metadata']['crs']}")

        # Get geometry in GeoJSON format
        geom = [mapping(aoi.geometry.iloc[0])]

        # Clip each band
        clipped_bands = {}
        for band_name, band_data in bands_data['bands'].items():
            logging.info(f"Clipping band {band_name}")
            
            # Create temporary raster in memory
            with rasterio.io.MemoryFile() as memfile:
                with memfile.open(
                    driver='GTiff',
                    height=band_data['data'].shape[0],
                    width=band_data['data'].shape[1],
                    count=1,
                    dtype=band_data['data'].dtype,
                    crs=bands_data['metadata']['crs'],
                    transform=band_data['transform']
                ) as dataset:
                    dataset.write(band_data['data'], 1)
                    
                    # Perform the clipping
                    clipped, transform = mask(
                        dataset,
                        geom,
                        crop=True,
                        all_touched=True,
                        nodata=0
                    )

            clipped_bands[band_name] = {
                'data': clipped[0],
                'transform': transform,
                'nodata': 0
            }

        metadata = {
            'product_name': product_name,
            'aoi_name': aoi_file.stem,
            'crs': bands_data['metadata']['crs'],
            'transform': transform,
            'shape': clipped[0].shape,
            'bounds': rasterio.transform.array_bounds(
                clipped[0].shape[0],
                clipped[0].shape[1],
                transform
            )
        }

        return clipped_bands, metadata

    except Exception as e:
        logging.error(f"Error in clip_to_aoi: {str(e)}")
        return None, {}

def save_clipped_data(
    clipped_data: Dict,
    metadata: Dict,
    output_dir: Path
) -> bool:
    """
    Save clipped data and metadata

    Args:
        clipped_data: Dictionary of clipped band data
        metadata: Dictionary of metadata
        output_dir: Directory to save output files

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save each band as GeoTIFF
        for band_name, band_data in clipped_data.items():
            output_file = output_dir / f"{metadata['name']}_{band_name}.tif"
            
            with rasterio.open(
                output_file,
                'w',
                driver='GTiff',
                height=metadata['shape'][0],
                width=metadata['shape'][1],
                count=1,
                dtype=band_data['data'].dtype,
                crs=metadata['crs'],
                transform=band_data['transform']
            ) as dst:
                dst.write(band_data['data'], 1)
                
            logging.info(f"Saved clipped band to {output_file}")

        return True

    except Exception as e:
        logging.error(f"Error saving clipped data: {str(e)}")
        return False

def save_clipped_product(clipped_bands: Dict, metadata: Dict, output_dir: Path) -> bool:
    """
    Save clipped Sentinel-2 data to preprocessed folder
    
    Args:
        clipped_bands: Dictionary of clipped band data
        metadata: Metadata dictionary containing product info
        output_dir: Output directory path
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create output directory
        preprocessed_dir = output_dir / 'data' / 'preprocessed'
        preprocessed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create output filename
        satellite = metadata.get('product_name', '').split('_')[0]  # S2A or S2B
        aoi_name = metadata.get('aoi_name', 'unknown_aoi')
        output_file = preprocessed_dir / f"{satellite}_{aoi_name}_clipped.pkl"
        
        # Log absolute paths
        logging.info(f"Saving clipped product to:\n{output_file.absolute()}")
        
        # Save data
        with open(output_file, 'wb') as f:
            pickle.dump({
                'bands': clipped_bands,
                'metadata': metadata
            }, f)
            
        logging.info(f"Successfully saved clipped product:\n{output_file.name}")
        return True
        
    except Exception as e:
        logging.error(f"Error saving clipped product: {str(e)}\nAttempted save location: {preprocessed_dir.absolute()}")
        return False

def run(self):
    """Run the preprocessing pipeline"""
    try:
        # ...existing steps...

        # Clip to AOI
        logging.info("Clipping to area of interest...")
        aoi_file = Path('data/external/municipio_1_Rome.geojson')
        
        for product_name, bands in bands_data.items():
            clipped_data, metadata = clip_to_aoi(
                bands,
                aoi_file,
                f"{product_name}_AOI"
            )
            
            if clipped_data:
                output_dir = Path('data/processed/Sentinel-2/L2A/AOI')
                save_clipped_data(clipped_data, metadata, output_dir)

        # ...rest of pipeline...
    except Exception as e:
        logging.error(f"Error in preprocessing pipeline: {str(e)}")