"""
OpenStreetMap utilities for downloading and processing boundary data
"""

import os
import logging
from pathlib import Path
import requests
import json
from typing import Optional

# Configure logging
logging.basicConfig(
    filename='results/logs/osm_download.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def download_osm_boundary(
    relation_id: str, 
    output_name: str, 
    root_dir: Optional[Path] = None
) -> bool:
    """
    Download OpenStreetMap boundary data using Overpass API
    
    Args:
        relation_id: OSM relation ID
        output_name: Name for the output file
        root_dir: Project root directory (optional)
    
    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        # Setup paths
        if root_dir is None:
            root_dir = Path(__file__).parents[2]  # Go up 2 levels from auxiliary folder
        
        output_dir = root_dir / 'data' / 'external'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Overpass API query for relation boundary
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:25];
        relation({relation_id});
        out body;
        >;
        out skel qt;
        """
        
        logging.info(f"Downloading OSM data for relation {relation_id}")
        
        # Make API request
        response = requests.post(overpass_url, data=query)
        response.raise_for_status()
        
        # Save response as GeoJSON
        output_file = output_dir / f"{output_name}.geojson"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)
            
        logging.info(f"Successfully saved boundary to {output_file}")
        return True
        
    except Exception as e:
        logging.error(f"Error downloading OSM data: {str(e)}")
        return False

if __name__ == "__main__":
    logging.info("Starting OSM boundary download...")
    
    success = download_osm_boundary(
        relation_id="1458218",
        output_name="municipio_1_Rome"
    )
    
    if success:
        logging.info("Download completed successfully")
    else:
        logging.error("Download failed")
        exit(1)