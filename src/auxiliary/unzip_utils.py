import os
import logging
import zipfile
import shutil
from pathlib import Path
from typing import Dict

def get_short_name(filename: str) -> str:
    """Create a shorter name from Sentinel-2 product identifier"""
    parts = filename.split('_')
    # Use satellite, date, and tile info only
    return f"{parts[0]}_{parts[2][:8]}_{parts[5]}"

def unzip_sentinel_data(zip_path: str, output_dir: str) -> str:
    """
    Unzip Sentinel-2 data in place and return the path to the SAFE directory
    
    Args:
        zip_path: Path to the zip file
        output_dir: Directory where to extract the data
    
    Returns:
        Path to the extracted SAFE directory or empty string if failed
    """
    try:
        zip_path = Path(zip_path)
        output_dir = Path(output_dir)
        
        # Get the expected SAFE directory name
        safe_name = zip_path.stem
        if not safe_name.endswith('.SAFE'):
            safe_name += '.SAFE'
        
        safe_path = output_dir / safe_name
        
        # Remove existing directory if present
        if safe_path.exists():
            logging.info(f"Removing existing directory: {safe_path}")
            shutil.rmtree(safe_path)
        
        # Extract to the output directory
        logging.info(f"Extracting {zip_path} to {output_dir}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        
        logging.info(f"Extraction complete: {safe_path}")
        return str(safe_path)
    
    except Exception as e:
        logging.error(f"Error extracting {zip_path}: {str(e)}")
        return ""