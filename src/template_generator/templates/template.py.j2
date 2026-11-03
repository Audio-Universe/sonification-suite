from fastapi import APIRouter
from pydantic import BaseModel
from paths import TMP_DIR
from context import session_id_var
import base64, gc

import numpy as np
import matplotlib
matplotlib.use("Agg") 
from matplotlib.figure import Figure
import pandas as pd
from io import BytesIO
from request_models import DataRequest
from utils import resolve_file

router = APIRouter(prefix='/template')

SONI_TYPE = 'template'

class ItemRequest(BaseModel):
    """
    This is a request model we create for the /select-item/ endpoint.
    It is best practice in fastAPI to define one for every type of request you might make, 
    so that it is clear what the frontend should send, and what the backend should expect.
    
    To make one, define a class that inherits from pydantic's BaseModel class, then define 
    attributes with names and expected data types.
    
    The rest of the api endpoints here use request models from elsewhere in the app, which 
    are all defined in request_models.py - I would recommend putting any you make in there too.
    """
    item_name: str
    
class RefineRequest(BaseModel):
    """
    This is the request type for refining the data.
    In this simplified template, it just sends the file reference, and the new x-axis 
    range to trim the data to.
    """
    file_ref: str
    new_range: list[float]
    
    
@router.get('/list/')
def get_data_list():
    """
    Here you would presumably have your own endpoint for getting/returning the list of available data. 
    This might be a search function (like in light_curves.py), in which case you would want to make this 
    a POST request (use fastAPI's @router.post decorator instead of @router.get) so that you could send 
    a search query and some filters in the request.

    Here we just generate and return a list of data names as a placeholder.
    """
    
    return [f'Item {i+1}' for i in range(10)]

@router.post('/plot/')
def plot_item(request: DataRequest):
   
    filepath = resolve_file(request.file_ref)

    img_base64 = plot_and_format(str(filepath))

    return {'image': img_base64}


def plot_and_format(path_or_df: str | pd.DataFrame):
    
    df = pd.read_csv(path_or_df) if isinstance(path_or_df, str) else path_or_df

    x = df['x'].values
    y = df['y'].values
    z = df['z'].values  

    # Plot and format
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)

    ax.plot(
        x,
        y,
        color="#008080",
        linewidth=1.2,
        alpha=0.9,
        label="Y"
    )

    ax.plot(
        x,
        z,
        color="#003E8A",
        linewidth=1.2,
        alpha=0.9,
        label="Z"
    )

    ax.set_xlabel("X")
    ax.set_ylabel("Y / Z")
    ax.legend()

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
def select_item(request: ItemRequest):
    """
    This is a placeholder endpoint where you may want to download the chosen 
    dataset to CSV (if the user hasn't chosen a suggested dataset). 
    
    How you do this and where the data comes from is up to you, but the key thing 
    is to ensure the data is written to CSV format in the user's unique session directory. 
    This directory is automatically created when a new user connects (in core.py /session/), 
    so you just need to get the session ID and write the data to the corresponding directory.
    
    In this placeholder, we just generate a random CSV file for whichever item is chosen.
    """
    
    filename = f'{request.item_name}.csv'
    
    # Get session id from context variable
    session_id = session_id_var.get()
    filepath = TMP_DIR / session_id / filename
    
    # Generate random data using the item number as the seed (reproducible)
    seed = int(request.item_name.split(" ")[1])
    rng = np.random.default_rng(seed)
    
    df = pd.DataFrame({
                        'x': range(20), 
                        'y': rng.integers(0, 100, size=20), 
                        'z': rng.integers(0, 100, size=20) 
                    })
     
    # Write the data to CSV 
    df.to_csv(filepath, index=False)
    
    file_ref = f'session:{filename}'
    
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
    img_base64 = plot_and_format(refined)

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



    
    

