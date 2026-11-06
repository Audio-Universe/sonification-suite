""" 
This module contains all of the logic for generating the required code to add a sonification type to the Suite.

The generator is intended to be interacted with via the command line, so if you'd like to add a sonificaiton 
type to the Suite, please run this script directly and follow the instructions given.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import pandas as pd
import numpy as np
import yaml, re

# Paths
GENERATOR_DIR = Path(__file__).parent
TEMPLATE_DIR = GENERATOR_DIR / "templates"
FRONTEND_DIR = GENERATOR_DIR.parent / "frontend"
BACKEND_DIR = GENERATOR_DIR.parent / "backend"

# Configure Jinja2
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    variable_start_string="[[", # Note we use square brackets to identify variables.
    variable_end_string="]]", # This is because the default curly braces clash with certain syntax in TSX.
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)

def generate_api(soni_type: str):
    """ Generate a basic API module in the backend. """
    
    template = env.get_template("api.py.j2")
    
    api_route = soni_type.replace('_','-')
    
    generated_code = template.render(
        soni_type=soni_type,
        api_route=api_route
    )

    output_path = BACKEND_DIR / f"{soni_type}.py"

    if output_path.exists():
        raise FileExistsError(f"{output_path} already exists")

    output_path.write_text(generated_code, encoding="utf-8")

    print(f"\033[32mCreated {soni_type} API: {output_path}\033[0m")

def generate_landing_page(
    component_name: str,
    soni_type: str,
    api_variable: str,
    heading: str,
):
    """ Generate the landing page for a new sonification type. """

    template = env.get_template("landing_page.tsx.j2")

    generated_code = template.render(
        component_name=component_name,
        soni_type=soni_type,
        api_variable=api_variable,
        heading=heading,
    )

    output_path = FRONTEND_DIR / "src" / "components" / "pages" / f"{component_name}.tsx"

    if output_path.exists():
        raise FileExistsError(f"{output_path} already exists")

    output_path.write_text(generated_code, encoding="utf-8")

    print(f"\033[32mCreated {component_name} landing page: {output_path}\033[0m")
    
def generate_refine_menu(
    component_name: str,
    soni_type: str,
    api_variable: str,
):
    """ Generate the refine menu for a new sonification type. """

    template = env.get_template("refine_menu.tsx.j2")

    generated_code = template.render(
        component_name=component_name,
        soni_type=soni_type,
        api_variable=api_variable,
    )

    output_path = FRONTEND_DIR / "src" / "components" / "refine_menus" / f"{soni_type}.tsx"

    if output_path.exists():
        raise FileExistsError(f"{output_path} already exists")

    output_path.write_text(generated_code, encoding="utf-8")

    print(f"\033[32mCreated {soni_type} refine menu: {output_path}\033[0m")
    
def add_suggested_data(soni_type: str):
    """ Create the new sugggested data directory and Write some random data 
        to CSV files as placeholders. Also create the yaml files used to display 
        info about the suggestions on the landing page (e.g. description).
    """
    
    data_dir = BACKEND_DIR / "suggested_data" / soni_type
    data_dir.mkdir()
    
    for i in range(4):
        
        data_path = data_dir / f"suggestion{i+1}.csv"
        
        # Write random integers to y and z columns (steadily increasing x)
        df = pd.DataFrame({
            'x': range(20),
            'y': np.random.randint(0, 100, size=20),
            'z': np.random.randint(0, 100, size=20)
        })
     
        # Write the data to CSV 
        df.to_csv(data_path, index=False)
        
        # Write placeholder names and descriptions to a yml file for each suggestion 
        metadata = {
            'name': f'Suggestion {i+1}',
            'description': f'Add names/descriptions in suggested_data/{soni_type}/suggestion{i+1}.yml'
        }
        
        yaml_path = data_dir / f"suggestion{i+1}.yml"
        
        with yaml_path.open("w") as file:
            file.write(f"# You can also add things here like ra/dec (if {soni_type} is compatible with Place on Dome).\n# For light curves, we also add 'category' to split suggestions into tabs.\n")
            yaml.safe_dump(metadata, file)
            
    print(f"\033[32mCreated suggested data directory and added placeholder data: {data_dir}\033[0m")
            
def add_style_file(soni_type: str):
    """ Create directory for style files and add placeholder style """
    
    style_dir = BACKEND_DIR / "style_files" / soni_type
    style_dir.mkdir()
    
    style_path = style_dir / "style.yml"
    
    style = {
        'name': 'My Style',
        'description': f'Add your own description in {str(style_path)}',
        'generator': {
            'type': 'synthesizer',
            'preset': 'White Noise'
        },
        'map': [
            {
                'input': 'x',
                'output': 'time'
            },
            {
                'input': 'y',
                'output': 'cutoff',
                'output_range': [0.4, 0.75]
            }
        ],
        'sources': 'objects',
        'notes': ['A3']
    }
    
    with style_path.open("w") as file:
        yaml.safe_dump(style, file)
    
    print(f"\033[32mCreated style files directory and added placeholder style: {style_dir}\033[0m")
    
    
def add_api_config(soni_type: str, api_variable: str):
    """ Update frontend/src/apiConfig.ts with the new API route address. """
    
    path = FRONTEND_DIR / "src" / "apiConfig.ts"

    content = path.read_text(encoding="utf-8")

    marker = "// Generated sonification APIs - DO NOT REMOVE THIS COMMENT"

    if marker not in content:
        raise ValueError("Could not find API configuration insertion point")

    if f"export const {api_variable}" in content:
        raise ValueError(f"API configuration for '{soni_type}' already exists")

    new_export = f'export const {api_variable} = `${{apiUrl}}/{soni_type.replace('_','-')}`;'

    # Add in the new API address below the marker
    content = content.replace(
        marker,
        f"{marker}\n{new_export}",
    )

    path.write_text(content, encoding="utf-8")
    
    print(f"\033[32mAdded API address in frontend: {path}\033[0m")
    
def add_route(soni_type: str, component_name: str):
    """ Add generated landing page component and route to App.tsx """
     
    path = FRONTEND_DIR / "src" / "App.tsx"
    
    content = path.read_text(encoding="utf-8")
    
    import_marker = "// Generated page imports - DO NOT REMOVE THIS COMMENT"

    if import_marker not in content:
        raise ValueError(f"Could not find import marker in {path}")
    
    new_import = f'import {component_name} from "./components/pages/{component_name}";'

    if new_import in content:
        raise ValueError(f"Component import for '{soni_type}' already exists")

    content = content.replace(
        import_marker,
        f"{import_marker}\n{new_import}",
    )
    
    route_marker = "{/* Generated routes - DO NOT REMOVE THIS COMMENT */}"
    if route_marker not in content:
            raise ValueError(f"Could not find route marker in {path}")
    
    route_path = soni_type.replace("_", "-")
    
    new_route = f'<Route path="{route_path}" element={{<{component_name} />}} />'
    if new_route in content:
            raise ValueError(f"Route for '{soni_type}' already exists")
        
    content = content.replace(
            route_marker,
            f"{route_marker}\n{new_route}",
        )

    path.write_text(content, encoding="utf-8")
    
    print(f"\033[32mCreated route to new landing page and added to app: {path}\033[0m")
    
def add_api_router(soni_type: str):
    
    path = BACKEND_DIR / 'main.py'
    
    content = path.read_text(encoding="utf-8")
        
    import_marker = "# Generated router imports - DO NOT REMOVE THIS COMMENT"

    if import_marker not in content:
        raise ValueError(f"Could not find import marker in {path}")
    
    router_alias = f'{soni_type}_router'
    new_import = f'from {soni_type} import router as {router_alias}'

    if new_import in content:
        raise ValueError(f"Router import for '{soni_type}' already exists")

    content = content.replace(
        import_marker,
        f"{import_marker}\n{new_import}",
    )
    
    inclusion_marker = "# Generated router inclusions - DO NOT REMOVE THIS COMMENT"
    if inclusion_marker not in content:
            raise ValueError(f"Could not find inclusion marker in {path}")
    
    new_inclusion = f'app.include_router({router_alias})'
    if new_inclusion in content:
            raise ValueError(f"Router for '{soni_type}' already included in main.py")
        
    content = content.replace(
            inclusion_marker,
            f"{inclusion_marker}\n{new_inclusion}",
        )

    path.write_text(content, encoding="utf-8")
    
    print(f"\033[32mAdded API router to app in backend: {path}\033[0m")
    
def add_soni_type_metadata(soni_type: str, label: str, description: str):
    
    path = FRONTEND_DIR / "src" / "types" / "soniTypes.ts"
    
    content = path.read_text(encoding="utf-8")
    
    marker = "// Generated soniTypes - DO NOT REMOVE THIS COMMENT"
    
    if marker not in content:
        raise ValueError(f"Could not find marker in {path}")
    
    page = soni_type.replace('_','-')
    
    new_entry = f'''{{
      key: "{soni_type}",
      label: "{label}",
      description: "{description}",
      page: "{page}",
      /* If you want an image to display on the Planetaria landing page, 
      add a .jpg image in the src/assets/images folder, and use the key 
      above as the filename. If using an image, you should update the 
      alt text below so an image description is read out by screen readers.
      
      Alternatively, you could use an icon (like the one on the Data Composer 
      card). To do this, import your desired icon from Lucide (the icon names 
      all start with 'Lu' - see top of this file for example) and then add 
      'icon: [icon name]' below. It should render on the Planetaria page 
      using the same colours/animation as the Data Composer and Suggestions/Examples cards.
      */
      imgAltText: "An image of {soni_type}",
    }},'''
    
    if new_entry in content:
        raise ValueError(f'Entry for {soni_type} already in {path}')
    
    content = content.replace(
        marker,
        f"{marker}\n{new_entry}"
    )
        
    path.write_text(content, encoding="utf-8")
        
    print(f"\033[32mAdded soniType metadata in frontend: {path}\033[0m")
    
def update_validate_import(soni_type: str, formatted_soni_type: str):
    """ Update the validate_import function in core.py with the new soni_type. 
        This will add a blank 'elif' branch so that you can write custom code to 
        set up the refine page (in the case that user has imported data). 
        
        It will also add the formatted soni_type to display in an error message if 
        the imported data doesn't seem to be of that soni_type (e.g. "are you sure 
        this is a ____ downloaded from the Suite?").
    """
    
    path = BACKEND_DIR / "core.py"
        
    content = path.read_text(encoding="utf-8")
    
    formatted_marker = "# Formatted string marker - DO NOT REMOVE THIS COMMENT"
    if formatted_marker not in content:
        raise ValueError(f"Could not find formatted string marker in {path}")
    
    # Have to ensure same indentation as the existing code
    new_dict_entry = f"        '{soni_type}': '{formatted_soni_type}',"
    if new_dict_entry in content:
        raise ValueError(f"Formatted string for {soni_type} already in validate_import function in core.py")
    
    content = content.replace(
        formatted_marker,
        f"{formatted_marker}\n{new_dict_entry}"
    )
    
    import_info_marker = "# Import info marker - DO NOT REMOVE THIS COMMENT"
    if import_info_marker not in content:
        raise ValueError(f"Could not find import info marker in {path}")
    
    new_elif_branch = f"""    elif soni_type == '{soni_type}':
        # Add things you might want to set up/limit your refine menu here
        # See above for examples of what we send for other soni_types
        pass
    """
    
    if new_elif_branch in content:
        raise ValueError(f"Elif branch for {soni_type} already in validate_import function in core.py")
    
    content = content.replace(
        import_info_marker,
        f"{import_info_marker}\n{new_elif_branch}"
    )
    
    path.write_text(content, encoding="utf-8")
            
    print(f"\033[32mUpdated validate_import function: {path}\033[0m")
    
def add_inputs(soni_type: str):
    """ Add the placeholder parameter names and decriptions for the new soni_type's 
        inputs in inputs_outputs.py in the backend.
    """
    
    path = BACKEND_DIR / "inputs_outputs.py"
    content = path.read_text(encoding="utf-8")
    
    marker = "# Generated inputs - DO NOT REMOVE THIS COMMENT"
    if marker not in content:
        raise ValueError(f"Could not find marker in {path}")
    
    new_entry = f"""'{soni_type}':
        {{
            # Here we just use x, y, and z as placeholders (same as the suggested data), but you should replace them
            # The keys correspond to the column headers in your soni_type's data - make sure they match!
            'x':
                {{
                    'name': 'X',
                    'desc': 'Add your own names and descriptions in inputs_outputs.py'
                }},
            'y':
                {{
                    'name': 'Y',
                    'desc': 'Add your own names and descriptions in inputs_outputs.py'
                }},
            'z':
                {{
                    'name': 'Z',
                    'desc': 'Add your own names and descriptions in inputs_outputs.py'
                }}
        }},
    """
    
    if new_entry in content:
        raise ValueError(f"INPUTS already contains an entry for {soni_type} in inputs_outputs.py")
    
    content = content.replace(
        marker,
        f"{marker}\n{new_entry}"
    )
    
    path.write_text(content, encoding="utf-8")
    
    print(f"\033[32mAdded placeholder input descriptions: {path}\033[0m")
    
def generate(
    soni_type: str,
    component_name: str,
    label: str,
    lowercase_singular: str,
    description: str,
    api_variable: str
):
    # Generate backend code
    print("\nGenerating backend code...\n")
    generate_api(soni_type=soni_type)
    add_api_router(soni_type=soni_type)
    add_suggested_data(soni_type=soni_type)
    add_style_file(soni_type=soni_type)
    add_inputs(soni_type=soni_type)
    update_validate_import(soni_type=soni_type, formatted_soni_type=lowercase_singular)
    
    # Generate frontend code
    print("\nGenerating frontend code...\n")
    add_api_config(soni_type=soni_type, api_variable=api_variable)
    generate_landing_page(
        component_name=component_name,
        soni_type=soni_type,
        api_variable=api_variable,
        heading=label,
    )
    generate_refine_menu(
        component_name=component_name,
        soni_type=soni_type,
        api_variable=api_variable
    )
    add_soni_type_metadata(soni_type=soni_type, label=label, description=description)
    add_route(soni_type=soni_type, component_name=component_name)
    

def normalise_name(name: str) -> str:
    """Convert user provided sonification type into snake_case."""
    name = name.strip().lower()
    name = re.sub(r"[\s-]+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")
    

if __name__ == "__main__":
    
    print('Welcome to the template generator!\n')
    
    while True:
        # Get the sonification type name
        name = input("Enter the name of your new sonification type (e.g. Exoplanets): ")

        soni_type = normalise_name(name)

        if not soni_type:
            print("Please enter a valid name.\n")
            continue

        # Generate naming variations
        words = soni_type.split("_")

        component_name = "".join(word.capitalize() for word in words)
        label = " ".join(word.capitalize() for word in words)

        # Convert snake_case to camelCase for the API variable
        camel_case = words[0] + "".join(word.capitalize() for word in words[1:])
        api_variable = f"{camel_case}API"
        
        # Ask for description
        print('\nNext, we need a description to display on the Planetaria landing page.')
        print("\nE.g. 'Listen to an exoplanet system orbit around you.'")
        description = input("\nEnter description (you can edit this later in frontend/src/types/soniTypes.ts): ")
        
        # Ask for the singular form
        print('\nNow we need the singular form of the noun. This is used to write error messages correctly.')
        lowercase_singular = input(
            "\nEnter the singular form (e.g. 'exoplanet' for 'Exoplanets'): "
        ).strip().lower()

        # Display summary
        print("\n" + "-" * 45)
        print("Please check the generated values:")
        print("-" * 45)

        print(f"Sonification type:  {soni_type}")
        print(f"Display name:       {label}")
        print(f"Singular form:      {lowercase_singular}")
        print(f"Description:        {description}")

        print("-" * 45)

        confirmation = input("\nProceed with template generation? (y/n): ").strip().lower()

        if confirmation in ("y", "yes"):
            break

        if confirmation in ("n", "no"):
            print("\nLet's try again.\n")
            continue

        print("\nPlease enter y or n.\n")

    # Generate the new sonification type
    generate(
        soni_type=soni_type,
        component_name=component_name,
        label=label,
        lowercase_singular=lowercase_singular,
        description=description,
        api_variable=api_variable
    )
    
    print(f"\n\033[1;32mGeneration complete!\033[0m")
    print("You can now run the app, and your new sonification type will be available.")
    
    print("\n" + "-" * 45 + "\n")
    print("NEXT STEPS:\n")
    print("The templates have been generated and wired up to the app.")
    print("The next step is customising your sonification type.\n")
    print("For full instructions, please visit: ")
    print("https://sonification-suite.readthedocs.io/en/latest/developer-guide/building-extensions/#customising-your-extension")
    print("\n" + "-" * 45 + "\n")
    
    