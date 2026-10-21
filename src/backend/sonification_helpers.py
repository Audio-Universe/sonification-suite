"""
The helper functions in this module are all called by the generate_sonification() function in core.py.
They all perform a specific, smaller task which is part of the larger sonification generation process.
"""

from request_models import SonificationRequest
from pathlib import Path
from utils import read_YAML_file, write_YAML_file, write_sound_to_style, is_time_series
from night_sky import handle_observer
from strauss import AudioFigure

import pandas as pd

def get_source_names(df, soni_type, layer):
    
    # Add identifier column for mapping table if necessary
    if soni_type == 'data_composer' and layer.id_column:
        source_names = df[layer.id_column].to_list()
    elif soni_type in ['constellations', 'night_sky']:
        source_names = df['display_name'].to_list()
    else:
        source_names = None
        
    return source_names

def preprocess_style(style_filepath: Path, df: pd.DataFrame, request: SonificationRequest):
    
    style_dict = read_YAML_file(style_filepath)
    
    # Replace base sound name with filepath to the sound
    style_dict = write_sound_to_style(style_dict)
        
    # Determine whether it is safe to downsample the data
    if is_time_series(df, style_dict):
            style_dict['max_notes_per_sec'] = style_dict.get('max_notes_per_sec') or 10
    
    # Overwrite any time mappings if using a custom star order for constellations
    if request.soni_type == 'constellations' and 'custom_order' in df.columns:
        for m in style_dict['map']:
            if m['output'] == 'time':
                m['input'] = 'custom_order'
                m['function'] = None # Remove any previous invert functions
                break
        
    return style_dict

def place_on_dome(observer_info: dict, style: dict, kwargs: dict, audio_system: str):
    
    # First, get position of object relative to observer
    position_info = handle_observer(observer_info)
    
    # Add fixed values to kwargs
    if audio_system == 'stereo':
        # Use pan
        kwargs['fix_pan'] = position_info['STRAUSS_inputs']['pan']
    elif audio_system in ['5.1', '7.1']:
        # Use Azimuth and Polar
        for param in ['azimuth', 'polar']:
            kwargs[f'fix_{param}'] = position_info['STRAUSS_inputs'][param]
    else:
        raise ValueError("Place on Dome feature not available for mono audio")
    
    # Get altitude and azimuth values in degrees to send to the frontend to display    
    alt_az = [position_info['display_values'][value] for value in ['altitude', 'azimuth']]
    
    # Finally, remove any existing spatial mappings from style, and rewrite to kwargs
    style['map'] = [mapping for mapping in style['map'] 
                        if mapping['output'] not in ['azimuth', 'polar', 'pan']]

    kwargs['style'] = str(write_YAML_file(style))
    
    return alt_az

def write_mapping_table(fig: AudioFigure, style_dict: dict, soni_type: str, observer: dict | None, df: pd.DataFrame, layer_index: int, session_dir: Path):
    # Get the mapping table(s)
    source_name = 'source_0' if style_dict['sources'].lower() == 'objects' else None
    table: pd.DataFrame = fig.get_table(name=f'sonification_{layer_index}', source=source_name)
    
    # if we are sonifying star data, add star names in mapping table
    if soni_type in ['constellations', 'night_sky']:
        table.rename(columns={'Source': 'Star Name'}, inplace=True)
        # Add Hipparcos IDs
        table['HIP'] = table['Star Name'].map(
            df.set_index('display_name')['hip']
        )
        
        # Move the column next to display name
        cols = list(table.columns)
        cols.remove(('HIP', ''))
        cols.insert(cols.index(('Star Name', '')) + 1, ('HIP', ''))
        table = table[cols]
        
    if observer:
        fixed_table = fig.get_fixed_table(name=f'sonification_{layer_index}', source=source_name)
        # Add each fixed parameter as a column in main mapping table
        for _, row in fixed_table.iterrows():
            parameter = row['parameter']
            value = row['value']
            unit = row['unit']
            unit_header = f'[{unit}]' if unit else ''
            table[(parameter, unit_header)] = value
    
    # Save mapping table to CSV
    table_path = session_dir / f'mapping_table_{layer_index}.csv'
    table.to_csv(table_path, index=False)