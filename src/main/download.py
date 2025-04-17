#!/usr/bin/env python3

import os
import yaml
import logging
from datetime import datetime
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import boto3
import botocore
from botocore.client import Config as BotoConfig

class CopernicusDataSpaceDownloader:
    def __init__(self, config):
        self.config = config
        self.session = self._create_oauth_session()
        # S3 client for public buckets (unsigned)
        self.s3 = boto3.client(
            's3',
            config=BotoConfig(signature_version=botocore.UNSIGNED)
        )

    def _create_oauth_session(self):
        """Set up OAuth2 session with client_credentials grant and retry."""
        auth_cfg = self.config['auth']
        client = BackendApplicationClient(client_id=auth_cfg['client_id'])
        session = OAuth2Session(client=client)
        token = session.fetch_token(
            token_url=auth_cfg['token_url'],
            client_id=auth_cfg['client_id'],
            client_secret=auth_cfg['client_secret']
        )
        # Attach retry logic for transient errors
        retry_strategy = Retry(
            total=5,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session

    def create_search_query(self):
        """Build the query parameters for mosaic search from the config."""
        geom = self.config['data']['geometry']
        if geom['type'] == 'Point':
            lon, lat = geom['coordinates']
            buffer = self.config['download']['copernicus_mosaic'].get('point_buffer', 0.01)
            minx, miny = lon - buffer, lat - buffer
            maxx, maxy = lon + buffer, lat + buffer
            bbox = f"{minx},{miny},{maxx},{maxy}"
        elif geom['type'] == 'Polygon':
            coords = geom['coordinates'][0]
            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            bbox = f"{min(xs)},{min(ys)},{max(xs)},{max(ys)}"
        else:
            raise ValueError(f"Unsupported geometry type: {geom['type']}")

        dr = self.config['data']['dates']
        datetime_str = f"{dr['start']}T00:00:00Z/{dr['end']}T23:59:59Z"

        return {
            'bbox': bbox,
            'datetime': datetime_str,
            'collections': [self.config['download']['copernicus_mosaic']['collection']],
            'maxCloudCover': self.config['download']['copernicus_mosaic']['max_cloud_cover'],
            'limit': 10
        }

    def _download_asset(self, url: str, out_path: str) -> bool:
        """Download via S3 or HTTP(S), return True on success."""
        if url.startswith("s3://"):
            bucket, key = url[5:].split("/", 1)
            try:
                self.s3.download_file(bucket, key, out_path)
                return True
            except botocore.exceptions.ClientError as e:
                logging.error(f"S3 download error for {url}: {e}")
                return False

        # HTTP(S) download
        try:
            resp = self.session.get(url, stream=True, timeout=60)
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            logging.error(f"HTTP download failed for {url}: {e}")
            return False

    def download_data(self):
        """Perform mosaic search and download all returned assets."""
        query = self.create_search_query()
        search_url = self.config['download']['copernicus_mosaic']['url']

        logging.info(f"Searching for data between {self.config['data']['dates']['start']} and {self.config['data']['dates']['end']}")
        try:
            resp = self.session.get(search_url, params=query, timeout=60)
            resp.raise_for_status()
        except Exception as e:
            logging.error(f"Mosaic search failed: {e}")
            return False

        features = resp.json().get('features', [])
        if not features:
            logging.error("No products found matching the criteria")
            return False

        logging.info(f"Found {len(features)} products")

        out_dir = os.path.join(self.config['processing']['output_folder'], 'sentinel2')
        os.makedirs(out_dir, exist_ok=True)

        success_count = 0
        for feat in features:
            pid = feat.get('id', 'unknown_id')
            assets = feat.get('assets', {})
            # pick the first available asset
            href = next((a.get('href') for a in assets.values() if a.get('href')), None)
            if not href:
                logging.error(f"No download href for product {pid}")
                continue

            out_file = os.path.join(out_dir, f"{pid}.zip")
            logging.info(f"Downloading product {pid} from {href}")
            if self._download_asset(href, out_file):
                logging.info(f"Successfully downloaded: {out_file}")
                success_count += 1
            else:
                logging.error(f"Failed to download: {pid}")

        logging.info(f"Downloaded {success_count} out of {len(features)} products")
        return success_count > 0

def main():
    # Load configuration
    cfg_path = os.path.join("config", "config.yaml")
    with open(cfg_path, "r") as f:
        config = yaml.safe_load(f)

    # Setup logging
    log_file = config.get('logging', {}).get('log_file', 'results/logs/pipeline.log')
    log_level = config.get('logging', {}).get('log_level', 'INFO').upper()
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    downloader = CopernicusDataSpaceDownloader(config)
    if downloader.download_data():
        logging.info("Download completed successfully")
    else:
        logging.error("Download failed")

if __name__ == "__main__":
    main()
