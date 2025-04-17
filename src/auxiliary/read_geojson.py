import json
import logging
from pathlib import Path
from typing import Dict, Optional

def read_geojson(file_path: Path) -> Optional[Dict]:
    """
    Read a GeoJSON file. If it does not contain a top‐level "type"
    (as sometimes returned by Overpass API), attempt to convert it
    into a valid FeatureCollection.
    
    Args:
        file_path: Path to the GeoJSON file.
    
    Returns:
        A dictionary containing valid GeoJSON data or None on error.
    """
    try:
        file_path = file_path.resolve()
        logging.info(f"Reading GeoJSON from: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # If the file is already a valid GeoJSON, return it.
        if "type" in data:
            if data["type"] == "FeatureCollection" and "features" in data:
                return data
            else:
                return data
        
        # Otherwise, assume it's an Overpass API JSON.
        # It should have an "elements" key.
        if "elements" in data:
            features = []
            for element in data["elements"]:
                geometry = element.get("geometry")
                if geometry:
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "id": element.get("id"),
                            "tags": element.get("tags")
                        },
                        "geometry": {
                            "type": "MultiPolygon",
                            "coordinates": [[
                                [[n["lon"], n["lat"]] for n in geometry]
                            ]]
                        }
                    }
                    features.append(feature)
            if features:
                valid_geojson = {"type": "FeatureCollection", "features": features}
                logging.info("Converted Overpass API JSON to valid GeoJSON")
                return valid_geojson
            else:
                raise ValueError("No features with geometry found in Overpass API JSON.")
        
        raise ValueError("Invalid GeoJSON: missing 'type' field and 'elements' not found.")
    
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format in {file_path}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error reading GeoJSON from {file_path}: {str(e)}")
        return None

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    root = Path(__file__).parents[3]
    geojson_path = root / "data" / "external" / "municipio_1_Rome.geojson"
    geojson_data = read_geojson(geojson_path)
    if geojson_data:
        logging.info("Successfully loaded and validated GeoJSON file.")