"""
Preprocessing module for Sentinel-2 data
Handles unzipping, band extraction and data organization
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import rasterio
import numpy as np
from rasterio.warp import transform_bounds
from shapely.geometry import box, shape
from rasterio.mask import mask
import geopandas as gpd
import json
from osgeo import gdal, ogr, osr

# Add project root to Python path
current_file = Path(__file__).resolve()
project_root = None
for parent in current_file.parents:
    if parent.name == "processing-root-folder":
        project_root = parent
        break
if project_root is None:
    raise RuntimeError("Project root 'processing-root-folder' not found")
sys.path.append(str(project_root))

from src.auxiliary.unzip_utils import unzip_sentinel_data
from src.auxiliary.read_geojson import read_geojson

def setup_logging() -> None:
    """Configure logging to results/logs/preprocessing.log"""
    log_dir = project_root / "results" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "preprocessing.log"
    
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )

class PreprocessingPipeline:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        
    def get_safe_paths(self, raw_dir: Path) -> List[Path]:
        """Get paths to SAFE directories, unzipping in place if necessary"""
        safe_paths = []
        
        # Process zip files first
        zip_files = list(raw_dir.glob("*.zip"))
        if zip_files:
            logging.info(f"Found {len(zip_files)} zip files to extract")
            
            for zip_file in zip_files:
                try:
                    # Extract directly in raw directory
                    safe_dir = unzip_sentinel_data(str(zip_file), str(raw_dir))
                    
                    if safe_dir:
                        safe_path = Path(safe_dir)
                        safe_paths.append(safe_path)
                        logging.info(f"Successfully extracted: {safe_path.name}")
                        
                        # Delete zip file after successful extraction
                        zip_file.unlink()
                        logging.info(f"Deleted zip file: {zip_file.name}")
                        
                except Exception as e:
                    logging.error(f"Failed to process {zip_file.name}: {str(e)}", exc_info=True)
                    continue
        
        # Add any existing SAFE directories
        existing_safes = list(raw_dir.glob("*.SAFE"))
        for safe_dir in existing_safes:
            if safe_dir not in safe_paths and (safe_dir / "GRANULE").exists():
                safe_paths.append(safe_dir)
                logging.info(f"Found existing SAFE directory: {safe_dir.name}")
        
        if not safe_paths:
            logging.error("No valid SAFE directories found")
        else:
            logging.info(f"Total SAFE directories to process: {len(safe_paths)}")
            
        return safe_paths

    def process_safe_directory(self, 
                             safe_path: Path, 
                             output_dir: Path,
                             bands_to_process: List[str]) -> bool:
        """Process a single SAFE directory with correct SAFE structure navigation"""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Navigate through correct SAFE structure
            granule_dirs = list(safe_path.glob("GRANULE/*"))
            if not granule_dirs:
                logging.error(f"No GRANULE subdirectories found in {safe_path}")
                return False
                
            granule_dir = granule_dirs[0]  # Use first granule directory
            r10m_path = granule_dir / "IMG_DATA" / "R10m"
            
            if not r10m_path.exists():
                logging.error(f"R10m directory not found in {granule_dir}/IMG_DATA")
                return False
                
            logging.info(f"Processing bands from: {r10m_path}")
            
            # Find band files with correct pattern matching
            band_files = {}
            for band in bands_to_process:
                # Use wider pattern matching for band files
                band_files_found = list(r10m_path.glob(f"*_{band}_*.jp2"))
                if band_files_found:
                    band_files[band] = band_files_found[0]
                    logging.info(f"Found {band}: {band_files_found[0].name}")
                else:
                    logging.warning(f"Band {band} not found in {r10m_path}")
            
            if not band_files:
                logging.error("No bands found to process")
                return False
            
            # Process and save bands
            product_name = safe_path.name.split('.')[0]
            output_path = output_dir / f"{product_name}_bands.tif"
            
            # Read and stack bands
            band_data = []
            band_names = []
            metadata = None
            
            for band_name, band_file in band_files.items():
                with rasterio.open(band_file) as src:
                    if metadata is None:
                        metadata = src.profile
                    band_data.append(src.read(1))
                    band_names.append(band_name)
                    logging.debug(f"Read band {band_name}")
            
            # Stack bands and save
            stacked_data = np.stack(band_data)
            
            metadata.update({
                'count': len(band_data),
                'compress': 'lzw',
                'driver': 'GTiff'
            })
            
            with rasterio.open(output_path, 'w', **metadata) as dst:
                dst.write(stacked_data)
                for idx, name in enumerate(band_names, start=1):
                    dst.set_band_description(idx, name)
            
            logging.info(f"Saved {len(band_data)} bands to {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error processing {safe_path}: {str(e)}", exc_info=True)
            return False

    def validate_overlap(self, geotiff_path: Path, geojson_path: Path) -> bool:
        """
        Validate that the GeoJSON AOI overlaps with the GeoTIFF extent
        
        Args:
            geotiff_path: Path to the GeoTIFF file
            geojson_path: Path to the GeoJSON file
        
        Returns:
            bool: True if there is overlap, False otherwise
        """
        try:
            # Read GeoJSON
            geojson_data = read_geojson(geojson_path)
            if not geojson_data:
                logging.error("Failed to read GeoJSON file")
                return False
                
            # Get GeoJSON geometry
            feature = geojson_data["features"][0]
            aoi_geometry = shape(feature["geometry"])
            
            # Read GeoTIFF bounds
            with rasterio.open(geotiff_path) as src:
                # Get bounds in the same CRS as GeoJSON (assuming EPSG:4326)
                bounds = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
                raster_bbox = box(*bounds)
                
            # Check for intersection
            if aoi_geometry.intersects(raster_bbox):
                overlap_area = aoi_geometry.intersection(raster_bbox).area
                total_area = aoi_geometry.area
                coverage = (overlap_area / total_area) * 100
                
                logging.info(f"AOI coverage: {coverage:.2f}%")
                return True
            else:
                logging.error("No overlap between GeoJSON and GeoTIFF")
                return False
                
        except Exception as e:
            logging.error(f"Error validating overlap: {str(e)}", exc_info=True)
            return False

    def clip_to_aoi(self, geotiff_path: Path, geojson_path: Path) -> bool:
        """Clip GeoTIFF to AOI boundary using GDAL"""
        try:
            logging.info(f"Clipping {geotiff_path.name} to AOI")
            
            # Read GeoJSON and get bounds
            with open(geojson_path) as f:
                geojson = json.load(f)
            
            # Get bounding box from first feature
            feature = geojson["features"][0]
            geom = feature["geometry"]
            geom_ogr = ogr.CreateGeometryFromJson(json.dumps(geom))
            min_x, max_x, min_y, max_y = geom_ogr.GetEnvelope()
            
            # Open source dataset
            src_ds = gdal.Open(str(geotiff_path))
            if src_ds is None:
                logging.error(f"Could not open {geotiff_path}")
                return False
                
            # Get image dimensions and georeference
            cols = src_ds.RasterXSize
            rows = src_ds.RasterYSize
            bands = src_ds.RasterCount
            transform = src_ds.GetGeoTransform()
            
            # Calculate pixel coordinates
            x_origin = transform[0]
            y_origin = transform[3]
            pixel_width = transform[1]
            pixel_height = -transform[5]
            
            # Compute crop coordinates
            i1 = max(0, int((min_x - x_origin) / pixel_width))
            j1 = max(0, int((y_origin - max_y) / pixel_height))
            i2 = min(cols, int((max_x - x_origin) / pixel_width))
            j2 = min(rows, int((y_origin - min_y) / pixel_height))
            
            new_cols = i2 - i1 + 1
            new_rows = j2 - j1 + 1
            
            # Read bands
            band_list = []
            for i in range(bands):
                band = src_ds.GetRasterBand(i + 1)
                data = band.ReadAsArray(i1, j1, new_cols, new_rows)
                band_list.append(data)
            
            # Update geotransform for new extent
            new_x = x_origin + i1 * pixel_width
            new_y = y_origin - j1 * pixel_height
            new_transform = (new_x, transform[1], transform[2], 
                            new_y, transform[4], transform[5])
            
            # Create output dataset
            clip_path = geotiff_path.parent / f"{geotiff_path.stem}_clipped.tif"
            driver = gdal.GetDriverByName("GTiff")
            dst_ds = driver.Create(str(clip_path), new_cols, new_rows, 
                                 bands, gdal.GDT_Float32,
                                 options=['COMPRESS=LZW'])
            
            if dst_ds is None:
                logging.error("Could not create output file")
                return False
            
            # Write bands
            for i, data in enumerate(band_list):
                dst_band = dst_ds.GetRasterBand(i + 1)
                dst_band.WriteArray(data)
                # Copy band description
                src_band = src_ds.GetRasterBand(i + 1)
                dst_band.SetDescription(src_band.GetDescription())
            
            # Set spatial reference
            dst_ds.SetGeoTransform(new_transform)
            dst_ds.SetProjection(src_ds.GetProjection())
            
            # Clean up
            src_ds = None
            dst_ds = None
            
            # Remove original file
            geotiff_path.unlink()
            logging.info(f"Saved clipped raster to: {clip_path}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error clipping to AOI: {str(e)}", exc_info=True)
            return False

    def run(self) -> bool:
        """Run the preprocessing pipeline"""
        try:
            logging.info("Starting preprocessing pipeline...")
            
            # Setup paths
            raw_dir = self.root_dir / "data" / "raw" / "Sentinel-2"
            output_dir = self.root_dir / "data" / "preprocessed" / "Sentinel-2" / "L2A"
            geojson_path = self.root_dir / "data" / "external" / "municipio_1_Rome.geojson"
            
            # Create necessary directories
            raw_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Get all SAFE directories (unzipping if needed)
            safe_paths = self.get_safe_paths(raw_dir)
            if not safe_paths:
                logging.error("No SAFE directories found to process")
                return False
            
            # Step 2: Process each SAFE directory
            bands_to_process = ['B02', 'B03', 'B04', 'B08']
            
            for safe_path in safe_paths:
                logging.info(f"\nProcessing: {safe_path.name}")
                if not self.process_safe_directory(safe_path, output_dir, bands_to_process):
                    logging.error(f"Failed to process {safe_path.name}")
                    continue

            # Step 4: Validate overlap and clip
            logging.info("\nStep 4: Validating overlap with AOI and clipping...")
            
            for geotiff_path in output_dir.glob("*_bands.tif"):
                logging.info(f"Processing: {geotiff_path.name}")
                
                # Check overlap
                if self.validate_overlap(geotiff_path, geojson_path):
                    # Clip to AOI if overlapping
                    if not self.clip_to_aoi(geotiff_path, geojson_path):
                        logging.error(f"Failed to clip {geotiff_path.name}")
                        continue
                else:
                    logging.warning(f"Skipping {geotiff_path.name} - No overlap with AOI")
                    # Optionally remove non-overlapping files
                    geotiff_path.unlink()
                    logging.info(f"Removed non-overlapping raster: {geotiff_path}")

            logging.info("\nPreprocessing pipeline completed")
            return True

        except Exception as e:
            logging.error(f"Pipeline error: {str(e)}", exc_info=True)
            return False

if __name__ == "__main__":
    # Setup logging first
    setup_logging()
    
    try:
        pipeline = PreprocessingPipeline(project_root)
        success = pipeline.run()
        
        if not success:
            logging.error("Pipeline failed")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Critical error: {str(e)}", exc_info=True)
        sys.exit(1)

