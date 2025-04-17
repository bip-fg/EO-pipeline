from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import yaml
import logging
import os
from datetime import datetime
import requests
import asyncio

app = FastAPI()

class DownloadRequest(BaseModel):
    start_date: str
    end_date: str
    cloud_cover: int
    polygon: list

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def setup_logging(config):
    log_file = config['logging']['log_file']
    log_level = config['logging']['log_level']
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

async def download_image(url: str, output_path: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(output_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                logging.info(f"Downloaded: {output_path}")
            else:
                logging.error(f"Failed to download {url}")

@app.post("/download/")
async def create_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    config = load_config()
    setup_logging(config)
    
    output_folder = os.path.join(
        config['processing']['output_folder'],
        config['satellite']['copernicus']['platform'],
        config['satellite']['copernicus']['product_level']
    )
    os.makedirs(output_folder, exist_ok=True)
    
    logging.info(f"Starting download for dates: {request.start_date} to {request.end_date}")
    logging.info(f"Cloud cover threshold: {request.cloud_cover}")
    
    # Here you would implement the actual download logic
    # This is a placeholder for the actual implementation
    return {"status": "Download started", "output_folder": output_folder}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)