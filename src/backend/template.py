from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from pathlib import Path
from paths import TMP_DIR, STYLE_FILES_DIR, SUGGESTED_DATA_DIR, SAMPLES_DIR
from context import session_id_var
import logging, requests, os, base64, hashlib, json, gc, threading, time

import numpy as np
import asyncio
import matplotlib
matplotlib.use("Agg") 
from matplotlib.figure import Figure
import pandas as pd
from io import BytesIO
from scipy.ndimage import gaussian_filter1d
from request_models import StarQuery, DataRequest, DownloadRequest, PlotRequest, RefineRequest
from utils import resolve_file, is_number


router = APIRouter(prefix='/template')

SONI_TYPE = 'template'

STYLES_DIR = STYLE_FILES_DIR / SONI_TYPE
STARS_DIR = SUGGESTED_DATA_DIR / SONI_TYPE

class ItemRequest(BaseModel):
    item: str

@router.post('/plot/')
def plot_lightcurve(request: DataRequest):
    """
    Download the target light curve (if not already downloaded) and convert it to a png image.
    This function saves the plot to the memory buffer, to increase speed and avoid saving multiple images to disk.

    - **request**: The URI (or file ref) of the light curve.
    - Returns: The image as a base64 string.
    """

    # Check if the requested light curve is from a search (with data URI) or a local file.
    if (request.file_ref.startswith('mast:')):

        filepath = download_lightcurve(request.file_ref)
    else:
        filepath = resolve_file(request.file_ref)

    img_base64 = plot_and_format_lc(str(filepath))

    return {'image': img_base64}


def plot_and_format_lc(path_or_df: str | pd.DataFrame):
    
    df = pd.read_csv(path_or_df) if isinstance(path_or_df, str) else path_or_df

    time = df['time'].values
    flux = df['flux'].values  

    # Plot and format
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)

    ax.plot(
        time,
        flux,
        color="#008080",
        linewidth=1.2,
        alpha=0.9
    )
    
    ax.set_xlabel('Time (Days)')
    ax.set_ylabel('Brightness (Flux)')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # send bytes to buffer
    buf = BytesIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")

    # Clean up memory
    buf.close()
    gc.collect()

    return img_base64

@router.post('/select-item/')
def select_item(request: DataRequest):

    filepath = Path(download_lightcurve(request.data_uri))
    file_ref = f'session:{filepath.name}'
    
    return {'file_ref': file_ref}


@router.post('/get-range/')
def get_range(request: DataRequest):

    filepath = str(resolve_file(request.file_ref))

    df = pd.read_csv(filepath)
    x = df['x'].values
    value_range = [float(min(x)), float(max(x))]

    return{'range': value_range,}


def refine(request: RefineRequest):
    
    filepath = str(resolve_file(request.file_ref))
    
    df = pd.read_csv(filepath)
    
    # Truncate to new range
    new_start, new_end = request.new_range
    df = df[(df['x'] >= new_start) & (df['x'] <= new_end)].copy()
    
    return df


@router.post('/preview-refined/')
def preview_refined(request: RefineRequest):

    refined = refine(request)
       
    # Plot, format, and convert image to Base64
    img_base64 = plot_and_format_lc(refined)

    return{'image': img_base64}


@router.post('/save-refined/')
def save_refined(request: RefineRequest):
    
    session_id = session_id_var.get()
    filename = f'{SONI_TYPE}_refined.csv'
    refined_filepath = TMP_DIR / session_id / filename
    
    df = refine(request)
    df.to_csv(refined_filepath, index=False)
    
    refined_ref = f'session:{filename}'

    return {'file_ref': refined_ref}



    
    

