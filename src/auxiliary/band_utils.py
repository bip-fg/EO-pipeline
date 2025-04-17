import os
import logging
import pickle
import rasterio
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional

def find_band_file(img_data_dir: Path, band: str, resolution: str) -> Optional[Path]:
    """Find band file using glob pattern matching"""
    # Search for files containing band name in filename
    pattern = f'*{band}*.jp2'
    matches = list(img_data_dir.glob(pattern))
    
    if matches:
        logging.info(f"Found {band} in: {matches[0].name}")
        return matches[0]
    return None

def read_sentinel_bands(l2_dir: str, bands: Optional[List[str]] = None) -> Dict[str, Dict[str, rasterio.DatasetReader]]:
    """
    Read Sentinel-2 bands from L2A products
    
    Args:
        l2_dir: Path to L2 directory containing extracted products
        bands: List of band names to read. Default: ['B02', 'B03', 'B04', 'B08']
    
    Returns:
        dict: Nested dictionary with structure {product_name: {band_name: rasterio.DatasetReader}}
    """
    if bands is None:
        bands = ['B02', 'B03', 'B04', 'B08']
    
    products = {}
    
    for product_dir in Path(l2_dir).glob('*'):
        if not product_dir.is_dir():
            continue
            
        try:
            product_name = product_dir.name
            logging.info(f"Processing product: {product_name}")
            
            # Find IMG_DATA directory
            img_data_dirs = list(product_dir.glob('**/IMG_DATA'))
            if not img_data_dirs:
                logging.warning(f"No IMG_DATA directory found in {product_name}")
                continue
            
            img_data = img_data_dirs[0]
            logging.info(f"Found IMG_DATA directory: {img_data}")
            
            # Read each band
            band_dict = {}
            for band in bands:
                try:
                    # Look for band file in any resolution directory
                    band_file = None
                    for res in ['R10m', 'R20m', 'R60m']:
                        res_dir = img_data / res
                        if res_dir.exists():
                            band_file = find_band_file(res_dir, band, res)
                            if band_file:
                                break
                    
                    if band_file:
                        band_dict[band] = rasterio.open(band_file)
                        logging.info(f"Successfully read {band} from {band_file.name}")
                    else:
                        logging.warning(f"Band {band} not found in any resolution directory")
                        
                except Exception as e:
                    logging.error(f"Error reading band {band}: {str(e)}")
            
            if band_dict:
                products[product_name] = band_dict
                logging.info(f"Successfully read {len(band_dict)} bands for {product_name}")
            else:
                logging.warning(f"No bands were read for {product_name}")
                
        except Exception as e:
            logging.error(f"Error processing {product_dir.name}: {str(e)}")
            continue
    
    return products

def create_bands_dictionary(products: Dict[str, Dict[str, rasterio.DatasetReader]], root_dir: Path) -> bool:
    """
    Create and save a dictionary containing band data
    
    Args:
        products: Dictionary of products and their bands
        root_dir: Project root directory
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Setup output directory with correct path
        output_dir = root_dir / 'data' / 'preprocessed' / 'Sentinel-2' / 'L2A'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        processed_data = {}
        for product_name, bands in products.items():
            logging.info(f"Processing {product_name}")
            
            product_dict = {
                'metadata': {
                    'name': product_name,
                    'crs': next(iter(bands.values())).crs,
                    'transform': next(iter(bands.values())).transform,
                    'timestamp': product_name.split('_')[2][:8]  # Extract date from product name
                },
                'bands': {}
            }
            
            # Read each band's data
            for band_name, band_reader in bands.items():
                product_dict['bands'][band_name] = band_reader.read(1)
                logging.info(f"Read data for band {band_name}")
            
            # Save each product separately
            product_file = output_dir / f"{product_name}_bands.pkl"
            with open(product_file, 'wb') as f:
                pickle.dump(product_dict, f)
            logging.info(f"Saved {product_name} to {product_file}")
            
            processed_data[product_name] = product_dict
        
        # Save the complete dictionary as well
        complete_file = output_dir / 'all_products.pkl'
        with open(complete_file, 'wb') as f:
            pickle.dump(processed_data, f)
        
        logging.info(f"Successfully saved all processed data to {output_dir}")
        return True
        
    except Exception as e:
        logging.error(f"Error creating bands dictionary: {str(e)}")
        return False