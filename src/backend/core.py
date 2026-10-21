# External imports (from dependencies)
import logging, yaml, os, uuid, traceback, base64, gc, re, shutil, math, tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File, Cookie, Response, Request, BackgroundTasks, Form
from fastapi.responses import FileResponse
from pathlib import Path
from strauss import AudioFigure
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg") 
from matplotlib.figure import Figure
from scipy.io import wavfile
from scipy.signal import spectrogram, resample_poly
from io import BytesIO
from pydub import AudioSegment

# Internal imports (from Suite)
from paths import TMP_DIR, STYLE_FILES_DIR, SUGGESTED_DATA_DIR, SYNTHS_DIR, SAMPLES_DIR
from context import session_id_var
from utils import resolve_file, read_YAML_file, write_YAML_file, is_synth, write_sound_to_style, cleanup_old_layers, is_bot
from sonification_helpers import get_source_names, preprocess_style, place_on_dome, write_mapping_table
from generator_mods import GENERATOR_MODS
from request_models import DataRequest, CustomStyleSettings, SonificationRequest, SoundInfo, VolumeRequest
from param_descriptions import INPUTS, OUTPUTS
from analytics import log_event

router = APIRouter(prefix='/core')

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

# Maximum upload quota per session
UPLOAD_QUOTA_MB = 50
UPLOAD_QUOTA_BYTES = UPLOAD_QUOTA_MB * 1024 * 1024

# Maximum length a sonification can be (in seconds)
MAX_DURATION = 120

@router.get('/session/')
def get_or_create_session(
    connection: Request,
    response: Response,
    session_id: str | None = Cookie(None),
):
    """ Get the session ID for this user. If none exists, this is a new connection, 
        so create a new one. We also log new sessions this in the analytics file 
        (provided we don't think it is bot traffic).

    Args:
        connection (Request): The HTTP connection
        response (Response): the Response object (used to set the session ID in cookie)
        session_id (str | None, optional): The session ID cookie, if present. Defaults to Cookie(None).

    Returns:
        str: session ID
    """
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            # max_age=24*60*60,  # could use this to make sessions persist across days?
            samesite="none",
            secure=True,
            path='/'
        )
        
        # check if the connection might be a bot (and don't log analytics)
        user_agent = connection.headers.get("user-agent", "Unknown")
        
        if not is_bot(user_agent):
            log_event(session_id=session_id, ip=connection.client.host, event='session_start')

        # Create session directory for user's files
        user_dir = TMP_DIR / session_id
        user_dir.mkdir(exist_ok=True)

    return {'session_id': session_id}

def get_uploads_dir_size(uploads_dir: str) -> int:
    """Returns total size in bytes of all files in a session's uploads directory."""
    try:
        return sum(
            f.stat().st_size
            for f in Path(uploads_dir).rglob('*')
            if f.is_file()
        )
    except Exception as e:
        LOG.warning("Could not calculate session size: %s", e)
        return 0


@router.post('/generate-sonification/')
def generate_sonification(request: SonificationRequest, connection: Request):
    """ Generate a sonification, write it to disk, and return the file ref.
     
        This function is the primary function of the entire app, so it is fairly complex. 
        The request contains all the information needed to build the sonification, including 
        the duration (in seconds), the soni type (e.g. is it a constellation, light curve etc.), 
        the audio system, the list of Layers to sonify (often this is just one layer unless using 
        Data Composer feature) and optionally the Observer details (if using Place on Dome feature). 
        The general flow is as follows:
        
        1. Preamble - check the sonification length doesn't exceed max, and create variables for session_id and 
        session_dir (create these outside the loop as they are same for all layers).
        
        2. Initialise the AudioFigure - This is the STRAUSS object which contains the sonifications (and methods 
        to generate/save them etc.)
        
        3. Loop through the Layers - Often there is only one layer (for light curves, constellations, etc). 
        The process in each iteration is layer-specific (I.E. handles each layer's specific data and Style).
        
            3.1. Resolve data and style refs to their full filepaths
            3.2. Convert data to Pandas DataFrame
            3.3. Pre-process Style file by making all necessary edits
            3.4. Initialise the kwargs dict which is given to the AudioFigure's sonify() function
            3.5. Set up 'Place on Dome' feature (if using)
            3.6. Add layer to the AudioFigure by calling sonify()
            3.7. Write the layer's Mapping Table to CSV
            3.8. Write the layer audio to WAV so user can download individual layers
            
            Loop through these steps as many times as there are layers
            
        4. Write the AudioFigure to WAV in user's session directory
        
        5. Log the 'sonification generated' event in the analytics file, and cleanup any old audio files

    Args:
        request (SonificationRequest): the request object, containing all sonification instructions
        connection (Request): the HTTP connection. We use this to get the client IP address which is 
        then used to estimate their country to log in analytics.

    Raises:
        HTTPException: 400 - if requested duration exceeds maximum (this is also prevented in the frontend)
        HTTPException: 400 - if no session ID present
        ValueError: if data file is not CSV
        HTTPException: for any other errors raised during sonification process

    Returns:
        dict: JSON object containing file_ref (the reference to the generated audio file) and 
        alt_az (the altitude and azimuth of the object, if using Place on Dome feature, for the frontend to display)
    """
    
    if request.duration > MAX_DURATION:
            raise HTTPException(status_code=400, detail=f"Sonification too long, maximum length is {MAX_DURATION} seconds.")
        
    session_id = session_id_var.get()
    
    if not session_id:
        raise HTTPException(status_code=400, detail="No session cookie found")
    
    session_dir = TMP_DIR / session_id
    
    # Initialise AudioFigure
    fig = AudioFigure(system=request.system)
    
    for i, layer in enumerate(request.layers, start=1):
        
        # Resolve data and style file names to actual paths in backend
        data_filepath = resolve_file(layer.data_ref)
        style_filepath = resolve_file(layer.style_ref)
        
        try:
            
            # First, validate data format and convert to DataFrame
            data_type = data_filepath.suffix.lower()
                    
            if data_type == '.csv':
                    df = pd.read_csv(str(data_filepath), header=0)
            else:
                    raise ValueError(f'{data_type} file type not suitable for sonification, please use .csv.')
            
            # Make all necessary edits to Style file
            style_dict = preprocess_style(style_filepath, df, request)
            
            # Build dict with keyword arguments for sonification function
            kwargs = {
                'style': str(write_YAML_file(style_dict)),
                'duration': request.duration,
                'angle_unit': 'degrees', # use degrees as standard for azimuth/polar
                'source_names': get_source_names(df, request.soni_type, layer)
            }
            
            # Handle case 'Place on Dome' feature is being used
            if request.observer:
                alt_az = place_on_dome(request.observer, style_dict, kwargs, request.system)
            else:
                alt_az = None
            
            # Add layer to the AudioFigure and sonify
            soni = fig.sonify(df, **kwargs)
            
            if layer.volume != 1:
                # Set initial volume if not 1 (default)
                fig.set_level(name=f'sonification_{i}', level=layer.volume)
            
            # Write the Mapping Table to CSV in user's session directory
            write_mapping_table(fig, style_dict, request.soni_type, request.observer, df, i, session_dir)
            
            if len(request.layers) > 1:
                # Save individual layers so users can download them if desired
                soni.render(progress=False)
                layer_name = f'layer_{i}.wav'
                layer_path = session_dir / layer_name
                soni.save(layer_path)
            
        except HTTPException:
            raise
        
        except Exception as e:
            LOG.error("Error generating sonification:\n" + traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail="Error generating sonification. If error persists, please try again with different Style settings."
            )
    
    filename = 'audio_figure.wav'
    filepath = session_dir / filename
    
    # Set master volume to maximum of all layer volumes
    master_volume = max([layer.volume for layer in request.layers])
    fig.save(filepath, master_volume=master_volume)
    
    log_event(session_id=session_id, ip=connection.client.host, event='sonification_generated', sonification_type=request.soni_type)
    cleanup_old_layers(session_id, len(request.layers))

    file_ref = f'session:{filename}'

    return {'file_ref': file_ref, 'alt_az': alt_az}
    
    
@router.post('/generate-spectrogram/')
def generate_spectrogram(request: DataRequest):

    filepath = resolve_file(request.file_ref)

    try:
  
        sr, data = wavfile.read(str(filepath))
        
        #Frequency parameters
        freq_min = 20
        freq_max = 22000

        # Convert to mono if stereo
        if data.ndim > 1:
            data = data.mean(axis=1)

        # Normalise to float
        data = data.astype(np.float32) / np.iinfo(np.int32).max
        
        target_sr = 22050

        # Downsample
        if sr != target_sr:
            
            gcd = np.gcd(sr, target_sr)
            up = target_sr // gcd
            down = sr // gcd

            data = resample_poly(data, up, down)
            sr = target_sr
            
        freq_max = sr // 2
        
        duration = len(data) / sr
        nperseg = 2048 if duration < 30 else 1024
        noverlap = nperseg // 2

        freqs, times, Sxx = spectrogram(
            data,
            fs=sr,
            window='hann',
            nperseg=nperseg,
            noverlap=noverlap,
            scaling='spectrum'
        )

        # Convert to dB
        Sxx_dB = 10 * np.log10(Sxx / np.max(Sxx) + 1e-12)

        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        
        ax.pcolormesh(
            times,
            freqs,
            Sxx_dB,
            shading='gouraud',
            cmap='gnuplot2',
            vmin=None,
            vmax=None
        )

        ax.set_xlabel('Time (s)')
        ax.set_yscale('log')
        ax.set_ylim(freq_min, freq_max)
        ax.set_ylabel('Frequency (Hz)')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')

        buf.close()
        gc.collect()

    except Exception as e:
        LOG.error("Error generating spectrogram:\n" + traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")
    
    return {'image': img_base64}

@router.get('/audio/{file_ref}')
def get_audio(
    connection: Request, 
    background_tasks: BackgroundTasks, 
    file_ref: str, 
    name: str, 
    audio_format: str = 'wav', 
    volume: float = 1,
    download: bool = False
    ):
    
    audio_format = audio_format.lower()
    
    if audio_format not in {"wav", "mp3"}:
        raise HTTPException(
            status_code=400,
            detail="Audio format must be 'wav' or 'mp3'"
        )
    
    if not 0 <= volume <= 1:
        raise HTTPException(status_code=400, detail="Volume must be between 0 and 1")

    wav_path = str(resolve_file(file_ref))

    # Original file can be returned directly when volume is unchanged
    if volume == 1:
        file_path = wav_path

    else:
        # Create temporary volume-adjusted WAV
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        )
        temp_file.close()

        volume_path = temp_file.name
        apply_volume(wav_path, volume, volume_path)
        
        # Delete temporary audio file once it's served
        background_tasks.add_task(Path(volume_path).unlink, missing_ok=True)
        file_path = volume_path
    
    # Convert to MP3 if requested        
    if audio_format == "mp3":
        mp3_path = convert_to_mp3(file_path)
        background_tasks.add_task(Path(mp3_path).unlink, missing_ok=True) # Delete temp mp3 after serving
        file_path = mp3_path
    
    # Log event in analytics if this is a download
    if download:
        log_event(session_id=session_id_var.get(), ip=connection.client.host, event='audio_download')

    return FileResponse(path=file_path, 
                        filename=f'{name}.{audio_format}',
                        media_type="audio/mpeg" if audio_format == "mp3" else "audio/wav")
    
@router.post('/mix-layer-volumes/')
def mix_layer_volumes(request: VolumeRequest):
    
    if all(vol == 1 for vol in request.volumes):
        # return original master if volumes all reset to 1
        return {'file_ref': 'session:audio_figure.wav'}
    
    is_single_layer = len(request.volumes) == 1
    
    session_id = session_id_var.get()
    session_dir = TMP_DIR / session_id
    audio_figure_path = session_dir / 'audio_figure.wav'
    
    audio_figure = AudioSegment.from_wav(audio_figure_path)
    
    # Create blank audio segment with same attributes as audio figure
    master = AudioSegment.silent(duration=len(audio_figure), frame_rate=audio_figure.frame_rate)
    
    for i, vol in enumerate(request.volumes, start=1):
        
        if vol == 0:
            # Don't add silent layers
            continue
        
        layer_name = "audio_figure.wav" if is_single_layer else f"layer_{i}.wav"
        layer_path = session_dir / layer_name
        layer_audio = AudioSegment.from_wav(layer_path)
        
        gain_db = 20 * math.log10(vol)
        headroom = 5.0 if not is_single_layer else 0.0
        adjusted = layer_audio + gain_db -headroom # Add 5db headroom to avoid clipping
        
        master = master.overlay(adjusted)

    master_path = session_dir / "audio_figure_mixed.wav"
    master.export(master_path, format='wav')
    
    return {'file_ref': 'session:audio_figure_mixed.wav'}
    
def apply_volume(wav_path: str, volume: float, output_path: str) -> None:
    if not 0 <= volume <= 1:
        raise ValueError("Volume must be between 0 and 1")

    audio = AudioSegment.from_wav(wav_path)

    if volume == 0:
        audio = AudioSegment.silent(duration=len(audio), frame_rate=audio.frame_rate)
    else:
        gain_db = 20 * math.log10(volume)
        audio = audio + gain_db

    audio.export(output_path, format="wav")

def convert_to_mp3(wav_file: str) -> str:
    """
    Convert a WAV file to an MP3.

    Args:
        wav_file: Path to the WAV file.

    Returns:
        Path to the temporary MP3 file.

    Raises:
        FileNotFoundError: If the WAV file does not exist.
        ValueError: If the input file is not a WAV.
        RuntimeError: If FFmpeg cannot be found.
    """
    wav_path = Path(wav_file)

    if not wav_path.exists():
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    if wav_path.suffix.lower() != ".wav":
        raise ValueError(f"Expected a .wav file, got {wav_path.suffix}")

    # Find FFmpeg
    system_ffmpeg = shutil.which("ffmpeg")

    if system_ffmpeg:
        # Production/Linux server
        AudioSegment.converter = system_ffmpeg
    else:
        # Development/Windows
        local_ffmpeg = r"C:\Users\ngc133\ffmpeg\bin\ffmpeg.exe"

        if not Path(local_ffmpeg).exists():
            raise RuntimeError(
                "FFmpeg is not installed or could not be found in this environment."
            )

        AudioSegment.converter = local_ffmpeg

    temp_file = tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False,
            )
    temp_file.close()

    mp3_path = temp_file.name
    
    audio = AudioSegment.from_wav(wav_path)

    try:
        audio.export(
            mp3_path,
            format="mp3",
            bitrate="320k"
        )
    except Exception:
        # Remove any partially-created/corrupt MP3
        if mp3_path.exists():
            mp3_path.unlink()
        raise

    return str(mp3_path)
    

@router.get("/download/{file_ref}")
def download_file(file_ref: str, name: str | None = None):

    file_path = str(resolve_file(file_ref))
    file_name = name or file_ref.split(':')[-1]
 
    response = FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/octet-stream",
    )

    # Cache buster
    response.headers["Cache-Control"] = "no-store, max-age=0"

    return response


@router.post('/upload-data/')
async def upload_data(request: Request, file: UploadFile, soni_type: str | None = Form(None)):
    """
    Function for the user to upload their own data to the system, which is then written
    to the tmp directory. The maximum file size is 10mb (this is set in nginx).

    - **upload**: The user-uploaded data file and (optionally) the sonification type.
    - Returns: The filepath of the saved data file.
    """


    # Client details for logging
    ip = request.client.host
    session_id = session_id_var.get()

    LOG.info(
        "Upload attempt | filename=%s | session=%s | ip=%s",
        file.filename,
        session_id,
        ip
    )

    suffixes = Path(file.filename).suffixes

    # Check for multiple extensions
    if len(suffixes) != 1:
        LOG.warning(
            "Upload rejected | filename=%s | reason=multiple_extensions | session=%s | ip=%s",
            file.filename,
            session_id,
            ip
        )
        raise HTTPException(400, "Files with multiple extensions are not allowed")

    ext = suffixes[0].lower()

    if ext != '.csv':
        LOG.warning(
            "Upload rejected | ext=%s | reason=rejected_extension | session=%s | ip=%s",
            ext,
            session_id,
            ip
        )
        raise HTTPException(
            status_code=415,
            detail='Uploaded data must be in .csv format'
        )

    MAX_SIZE = 10 * 1024 * 1024

    contents = await file.read()
    await file.close()

    # Check for empty file
    if not contents:
        LOG.warning(
            "Upload rejected | reason=empty_file | session=%s | ip=%s",
            session_id,
            ip
        )
        raise HTTPException(400, "Uploaded file is empty")

    # Double check the file size isn't > 10mb
    if len(contents) > MAX_SIZE:
        LOG.warning(
            "Upload rejected | size=%d | reason=file_too_large | session=%s | ip=%s",
            len(contents),
            session_id,
            ip
        )
        raise HTTPException(400, "File too large")

    # Check CSV is actually text
    if ext == ".csv":
        try:
            contents.decode('utf-8')
        except UnicodeDecodeError:
            LOG.warning(
            "Upload rejected | reason=invalid_csv | session=%s | ip=%s",
            session_id,
            ip
            )
            raise HTTPException(415, "Invalid CSV file")
        
    
    if soni_type:
        file_ref, import_info = validate_import(contents, soni_type, Path(file.filename).stem)
    else:
        
        # Ensure session directory exists
        session_dir = os.path.join(TMP_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)
            
        # Ensure uploads directory exists
        uploads_dir = os.path.join(session_dir, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Check session's upload quota
        current_usage = get_uploads_dir_size(uploads_dir)
        if current_usage + len(contents) > UPLOAD_QUOTA_BYTES:
            LOG.warning(
                "Upload rejected | reason=quota_exceeded | usage=%d | file_size=%d | session=%s | ip=%s",
                current_usage,
                len(contents),
                session_id,
                ip
            )
            raise HTTPException(429, f"Session upload quota of {UPLOAD_QUOTA_MB}MB exceeded")

        # Create random ID to store file under
        new_name = f"{uuid.uuid4()}.csv"
        filepath = os.path.join(uploads_dir, new_name)
        
        # Write to new csv file
        with open(filepath, "wb") as f:
            f.write(contents)

        LOG.info(
            "Upload success | original=%s | stored=%s | size=%d | session=%s | ip=%s",
            file.filename,
            new_name,
            len(contents),
            session_id,
            ip
        )

        file_ref = f"session:uploads:{new_name}"
        import_info = None

    return {"file_ref": file_ref, "import_info": import_info}


def validate_import(file_contents: bytes, soni_type: str, filename: str):
    
    formatted_types = {
        'light_curves': 'light curve',
        'constellations': 'constellation',
        'night_sky': 'night sky'
    }
    
    if soni_type not in formatted_types.keys():
        raise HTTPException(status_code=400, detail=f"Invalid soni_type: {soni_type}")
    
    df = pd.read_csv(BytesIO(file_contents))
    
    expected_cols = INPUTS[soni_type].keys()
    
    # Check that the basic columns for this soni type are a subset of the imported columns
    if not expected_cols <= set(df.columns):
        raise HTTPException(status_code=400, detail=f"Imported data appears invalid - are you sure this is a {formatted_types[soni_type]} downloaded from the Suite?")

    import_info= {
        'data_name': filename,
    }

    if soni_type == 'night_sky':
        import_info['max_magnitude'] = df['magnitude'].max()
    
    elif soni_type == 'constellations':
        import_info['stick_figure'] = bool(df['stick_figure'].iloc[0])
        import_info['star_count'] = len(df)

        # Get custom order if there is one in imported data
        import_info['custom_order'] = (
            df.sort_values('custom_order')['hip'].tolist()
            if 'custom_order' in df.columns
            else None
        )
        
    session_id = session_id_var.get()
    file_name = f'{soni_type}.csv'
    file_path = TMP_DIR / session_id / file_name
    df.to_csv(file_path, index=False)
    
    file_ref = f'session:{file_name}'
    
    return file_ref, import_info

    

def round_range(range: list, dp: int = 2) -> list:
    return [round(float(v), dp) for v in range]


@router.get('/get-inputs/')
def get_inputs(file_ref: str, soni_type: str):
    
    filepath = str(resolve_file(file_ref))
    
    if not filepath.endswith('.csv'):
        raise HTTPException(status_code=400, detail='File is not CSV, cannot read inputs')
    
    if soni_type == 'data_composer':
        df = pd.read_csv(filepath, header=0)
        
        # Find which columns contain numeric data
        numeric_cols = df.select_dtypes(include="number").columns
            
        inputs = [
            {
                'name': col, 
                'desc': '',
                'key': col,
                'numeric': col in numeric_cols
            }
            for col in df.columns
        ]

    else:   
        inputs = [
            {
                'name': INPUTS[soni_type][col]['name'], 
                'desc': INPUTS[soni_type][col]['desc'],
                'key': col,
                'numeric': True
            }
            for col in INPUTS[soni_type]
        ]
        
        # Add custom order column if user has chosen a custom constellation order
        if soni_type == 'constellations' and 'custom_order' in pd.read_csv(filepath).columns:
            inputs.append(
                    {
                    'name': 'Custom Order',
                    'desc': 'Your chosen star order - map this to Time',
                    'key': 'custom_order',
                    'numeric': True
                    }
            )

    return inputs

@router.get('/get-outputs/')
def get_outputs():
    return [
        {'name': v['name'], 'desc': v['desc'], 'key': k}
        for k, v in OUTPUTS.items()
    ]
        

@router.get('/suggested-data/{soni_type}/')
def get_suggested(soni_type: str):

    data_dir = SUGGESTED_DATA_DIR / soni_type
    
    if not data_dir.exists():
        raise HTTPException(status_code=404, detail=f'Suggested data directory for {soni_type} not found')
    
    data_list = []

    for file in data_dir.glob('*.yml'):
        try:
            with open(file, 'r') as f:
                data = yaml.safe_load(f)
            name = data.get('name', str(file.stem))  # fallback to filename if 'name' missing
            desc = data.get('description')
            ra = data.get('ra', None)
            dec = data.get('dec', None)
            category = data.get('category', None)
        except Exception as e:
            print(f'Failed to read or parse {file}: {e}')
            continue

        filenames = {
            'light_curves': str(file.stem) + '.csv',
            'constellations': 'hyg.csv'
        }

        file_ref = f'suggested_data:{soni_type}:{filenames[soni_type]}'

        data = {'name': name,
                'description': desc,
                'ra': ra,
                'dec': dec,
                'file_ref': file_ref,
                'category': category
                }

        data_list.append(data)
        
    return data_list

@router.get('/styles/{soni_type}')
def get_styles(soni_type: str):

    styles_dir = STYLE_FILES_DIR / soni_type
    if not styles_dir.exists():
        raise HTTPException(status_code=404, detail="Style directory not found")
    
    styles = []

    for file in styles_dir.glob("*.yml"):
        try:
            with open(file, "r") as f:
                data = yaml.safe_load(f)
            style_name = data.get("name", file.stem)  # fallback to filename if 'name' missing
            style_description = data.get("description", "")
        except Exception as e:
            print(f"Failed to read or parse {file}: {e}")
            continue

        file_ref = f'style_files:{soni_type}:{file.name}'

        style = {'name': style_name, 'description': style_description, 'file_ref': file_ref}

        styles.append(style)

    return styles

def get_sounds():
      
    local_sounds = []
    
    for f in SYNTHS_DIR.iterdir():
        if f.is_file():
            composable = f.stem != 'White Noise'
            data_modes = ['continuous', 'discrete']
            sound = SoundInfo(name=f.stem, composable=composable, data_modes=data_modes)
            local_sounds.append(sound)
            
    # List of sound names that are only suitable for Events (discrete) sonifications
    SHORT_SAMPLES = ['Glockenspiel', 'Mallets', 'Harp']

    for f in SAMPLES_DIR.iterdir():
        if f.is_dir():
            name = f.stem
    
            files = [file for file in f.iterdir() if file.is_file()]

            # Composable if:
            # 1) The directory contains a .sf2 file
            # 2) OR the directory contains multiple files
            composable = (
                any(file.suffix == ".sf2" for file in files)
                or len(files) > 1
            )

            # We are essentially hardcoding which sounds are suitable for Events vs Objects,
            # so if more sounds are added in the future, this categorisation may need to change.
            data_modes = ['discrete'] if name in SHORT_SAMPLES else ['continuous']
          
            sound = SoundInfo(name=name, composable=composable, data_modes=data_modes)
            local_sounds.append(sound)
      
    return local_sounds

@router.get('/sound_info/')
def get_sound_info():
    return get_sounds()

@router.post('/preview-style-settings/')
def preview_style_settings(request: DataRequest):

    # Resolve style ref to path and swap sound name for full filepath
    style_path = resolve_file(request.file_ref)
    style_dict = read_YAML_file(style_path)
    style_dict = write_sound_to_style(style_dict)
    
    # Generate synthetic data for previews
    N = 100 if style_dict["sources"] == "objects" else 50
    
    args = []
    
    for mapping in style_dict["map"]:
        output = mapping["output"]

        if output in ["time", "time_evo"]:
            # Use linear function for time
            args.append(np.linspace(0, 1, N))
        else:
            # Sine wave for all other parameters 
            x = np.linspace(0, np.pi, N) 
            args.append(np.sin(x))
    
    style_file = str(write_YAML_file(style_dict))

    try:
        fig = AudioFigure()
        fig.sonify(*args, style=style_file, duration=5)

        id = str(uuid.uuid4().hex)
        ext = '.wav'
        filename = f'preview_{id}{ext}'
        session_id = session_id_var.get()
        filepath = os.path.join(TMP_DIR, session_id, filename)
        fig.save(filepath)

        file_ref = f'session:{filename}'

        return {'file_ref': file_ref}
    except Exception:
        traceback.print_exc()
        raise
    
@router.post('/save-style-settings/')
def save_style_settings(settings: CustomStyleSettings):
    """
    Save sound settings for the sonification.

    - **settings**: The sound settings to be saved.
    - Returns: A filename of the saved settings.
    """
    # Save settings to a yaml file and return the filename
    style = format_style(settings)
    filepath = write_YAML_file(style)

    file_ref = f'session:{filepath.name}'

    # Return the file reference
    return {'file_ref': file_ref}

def format_style(settings: CustomStyleSettings):

    sources = 'objects' if settings.dataMode == 'continuous' else 'events'
    
    for m in settings.map:
        
        # If using custom data, swap 'column 1' etc for 0-indexed column index (e.g. 'column 1' -> 0)
        if re.fullmatch(r"column \d+", m["input"]):
            m["input"] = int(m["input"].split()[-1]) - 1
            
        if m['output'] == 'time':
            if sources == 'objects':
                # Swap time for time_evo if using Objects
                m['output'] = 'time_evo'
            else:
                # Add extra time for Events to play out
                m['input_range'] = ['0%', '110%']
                
        elif m['output'] == 'pitch':
            # Swap pitch for pitch_shift if Objects, or Events with no notes given
            if sources == 'objects' or not settings.notes:
                m['output'] = 'pitch_shift'
                lims = m['output_range'] or [0, 1]
                m['output_range'] = [x*24 for x in lims] # Rescale 0-1 to 0-24 semitones (STRAUSS range for pitch_shift)        
        
    # Set up Generator dictionary
    gen_type, sound_key = (
        ("synthesizer", "preset")
        if is_synth(settings.sound)
        else ("sampler", "sample")
    )
        
    generator = {
        'type': gen_type,
        sound_key: settings.sound
    }

    mods = GENERATOR_MODS.get(settings.sound)
    if mods:
        generator["mods"] = mods
    
    
    # Build final style dict
    style = {
        "name": "Custom",
        "sources": sources,
        "generator": generator,
        "map": settings.map,
        "notes": settings.notes,
        "metadata": settings.metadata.model_dump()
    }
    
    # Add additional fields for Events
    if sources == 'events':
        style['pitch_binning'] = 'uniform'
    
    return style

@router.post("/convert-style-to-settings/")
def convert_style_to_settings(request: DataRequest):
    
    style_path = str(resolve_file(request.file_ref))
    style: dict = read_YAML_file(style_path)
    
    settings = {
        'data_mode': 'continuous' if style['sources'] == 'objects' else 'discrete',
        'sound_name': style['generator'].get('preset') or style['generator'].get('sample'),
    }
    
    for k in ['map', 'notes', 'metadata']:
        settings[k] = style[k]
        
    return settings

@router.post("/upload-style/")
async def upload_style(file: UploadFile = File(...), request: Request = None):

    ip = request.client.host
    session_id = session_id_var.get()

    LOG.info(
        "Style upload attempt | filename=%s | session=%s | ip=%s",
        file.filename,
        session_id,
        ip
    )

    # Check for multiple extensions
    suffixes = Path(file.filename).suffixes
    if len(suffixes) != 1:
        LOG.warning(
            "Style upload rejected | filename=%s | reason=multiple_extensions | session=%s | ip=%s",
            file.filename, session_id, ip
        )
        raise HTTPException(400, "Files with multiple extensions are not allowed")

    ext = suffixes[0].lower()
    if ext not in {'.yaml', '.yml'}:
        LOG.warning(
            "Style upload rejected | ext=%s | reason=rejected_extension | session=%s | ip=%s",
            ext, session_id, ip
        )
        raise HTTPException(415, "Uploaded style must be in .yaml or .yml format")

    MAX_SIZE = 1 * 1024 * 1024  # 1MB limit as style files should be very small

    contents = await file.read()
    await file.close()

    if not contents:
        LOG.warning(
            "Style upload rejected | reason=empty_file | session=%s | ip=%s",
            session_id, ip
        )
        raise HTTPException(400, "Uploaded file is empty")

    if len(contents) > MAX_SIZE:
        LOG.warning(
            "Style upload rejected | size=%d | reason=file_too_large | session=%s | ip=%s",
            len(contents), session_id, ip
        )
        raise HTTPException(400, "File too large")

    # Validate YAML
    try:
        contents.decode('utf-8')
    except UnicodeDecodeError:
        LOG.warning(
            "Style upload rejected | reason=invalid_utf8 | session=%s | ip=%s",
            session_id, ip
        )
        raise HTTPException(415, "File does not appear to be a valid YAML file")

    try:
        parsed_yaml = yaml.safe_load(contents)
        style_name = parsed_yaml.get('name', 'Custom')
        style_description = parsed_yaml.get('description', "")
    except yaml.YAMLError as e:
        LOG.warning(
            "Style upload rejected | reason=invalid_yaml | session=%s | ip=%s",
            session_id, ip
        )
        raise HTTPException(415, f"Invalid YAML: {str(e)}")

    # Ensure session directory exists
    session_dir = os.path.join(TMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    # Ensure uploads directory exists
    uploads_dir = os.path.join(session_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    # Check session quota
    current_usage = get_uploads_dir_size(uploads_dir)
    if current_usage + len(contents) > UPLOAD_QUOTA_BYTES:
        LOG.warning(
            "Style upload rejected | reason=quota_exceeded | usage=%d | file_size=%d | session=%s | ip=%s",
            current_usage, len(contents), session_id, ip
        )
        raise HTTPException(429, f"Session upload quota of {UPLOAD_QUOTA_MB}MB exceeded")

    new_name = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(uploads_dir, new_name)

    with open(filepath, 'wb') as f:
        f.write(contents)

    LOG.info(
        "Style upload success | original=%s | stored=%s | size=%d | session=%s | ip=%s",
        file.filename,
        new_name,
        len(contents),
        session_id,
        ip
    )

    file_ref = f"session:uploads:{new_name}"
    
    return {"file_ref": file_ref, "style_name": style_name, "style_description": style_description}