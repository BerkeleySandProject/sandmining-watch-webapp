#!/usr/bin/env python3

from fastapi import FastAPI, Path
import frontend
import folium
import json
import requests

import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import pyproj

import os

app = FastAPI()

dataset_path = "public/dataset.json"
colorbar_path = "public/colorbar_r.png"

with open(dataset_path) as f:
    dataset = json.load(f)
    #print(dataset)

@app.get("/")
def read_root():
    return os.getcwd()

@app.get("/download-cloud-object/{item_uri:path}")
def download_cloud_object(item_uri: str = Path(description="The URL of the gcloud item you want to download.")):
    labels = item_uri.split("/")[3:]
    bucket_name = labels[0]
    blob_name = "/".join(labels[1:])
    filename = f"{blob_name.replace(r'/', '_')}.tif"
    def download_chunks_concurrently(
        bucket_name, blob_name, filename, chunk_size=32 * 1024 * 1024, workers=8
    ):
        """Download a single file in chunks, concurrently in a process pool."""

        # The ID of your GCS bucket
        # bucket_name = "your-bucket-name"

        # The file to be downloaded
        # blob_name = "target-file"

        # The destination filename or path
        # filename = ""

        # The size of each chunk. The performance impact of this value depends on
        # the use case. The remote service has a minimum of 5 MiB and a maximum of
        # 5 GiB.
        # chunk_size = 32 * 1024 * 1024 (32 MiB)

        # The maximum number of processes to use for the operation. The performance
        # impact of this value depends on the use case, but smaller files usually
        # benefit from a higher number of processes. Each additional process occupies
        # some CPU and memory resources until finished. Threads can be used instead
        # of processes by passing `worker_type=transfer_manager.THREAD`.
        # workers=8

        from google.cloud.storage import Client, transfer_manager

        storage_client = Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        transfer_manager.download_chunks_concurrently(
            blob, filename, chunk_size=chunk_size, max_workers=workers
        )

        print("Downloaded {} to {}.".format(blob_name, filename))

    download_chunks_concurrently(bucket_name=bucket_name, blob_name=blob_name,
                                     filename=filename)

    return {"data": "success"}

@app.get("/convert-tif-to-mercator/{tif_filename}")
def convert_tif_to_mercator(tif_filename: str = Path(description="Reproject a GeoTIFF file to the Mercator projection for Folium.")):
    dst_crs = 'EPSG:3857'

    with rasterio.open(tif_filename) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        # Specify compression options
        compress = 'deflate'  # You can choose the compression method (e.g., 'deflate', 'lzw', 'jpeg', 'packbits', etc.)
        dest_file_name = 'RGB.byte.wgs84_compressed.tif'
        with rasterio.open(dest_file_name, 'w', **kwargs, compress='deflate') as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)
    return {"data": dest_file_name}

@app.get("/get-bounds-from-raster/{tif_filename}")
def get_bounds_from_raster(tif_filename:str = Path(description="Get the bottom left and top right lat-long coords from a raster.")):
    tif_filename = os.path.join(os.getcwd(), tif_filename.strip())
    with rasterio.open(tif_filename) as src:
        # Get the geographic bounds of the raster
        bounds = src.bounds
        # Define the EPSG codes
        epsg3857 = pyproj.CRS('EPSG:3857')  # Web Mercator
        wgs84 = pyproj.CRS('EPSG:4326')
        # Create a transformer to convert from EPSG 3857 to EPSG 4326
        transformer = pyproj.Transformer.from_crs(epsg3857, wgs84)
        # Define the bottom-left and top-right coordinates in EPSG 3857
        bottom_left = (bounds.left, bounds.bottom)  # Replace x_min and y_min with your values
        top_right = (bounds.right, bounds.top)    # Replace x_max and y_max with your values
        # Convert the coordinates to geographic (latitude and longitude)
        lon_min, lat_min = transformer.transform(bottom_left[0], bottom_left[1])
        lon_max, lat_max = transformer.transform(top_right[0], top_right[1])
    return {"data": 
                {"bounds": ((lon_min, lat_min), (lon_max, lat_max))}
            }

frontend.init(app)

if __name__ == "__main__":
    print(
        'Please start the app with the "uvicorn" command as shown in the start.sh script'
    )
