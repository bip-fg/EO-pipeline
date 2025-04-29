"""
Main orchestrator for Sentinel-2 pipeline
"""
import os
import sys
import logging
from pathlib import Path

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

# Update imports to use src prefix
from src.main.preprocessing.preprocessing import PreprocessingPipeline
from src.main.processing.processing import ProcessingPipeline
from src.main.analysis.analysis import AnalysisPipeline

def setup_logging() -> None:
    """Configure logging"""
    log_dir = project_root / "results" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"
    
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers
    )

def main():
    """Run complete pipeline"""
    try:
        # Setup logging
        setup_logging()
        logging.info("Starting complete pipeline...")
        
        # Step 1: Preprocessing (BOA reflectance + clipping)
        logging.info("\n=== Starting Preprocessing ===")
        preprocessor = PreprocessingPipeline(project_root)
        if not preprocessor.run():
            logging.error("Preprocessing failed")
            return False
            
        # Step 2: Processing (RGB + NDVI generation)
        logging.info("\n=== Starting Processing ===")
        processor = ProcessingPipeline(project_root)
        if not processor.run():
            logging.error("Processing failed")
            return False
            
        # Step 3: Analysis (Land cover classification)
        logging.info("\n=== Starting Analysis ===")
        analyzer = AnalysisPipeline(project_root)
        if not analyzer.run():
            logging.error("Analysis failed")
            return False
            
        logging.info("\nComplete pipeline finished successfully")
        return True
        
    except Exception as e:
        logging.error(f"Pipeline error: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)