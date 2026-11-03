from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

# Paths
GENERATOR_DIR = Path(__file__).parent
TEMPLATE_DIR = GENERATOR_DIR / "templates"
FRONTEND_DIR = GENERATOR_DIR.parent / "frontend"
BACKEND_DIR = GENERATOR_DIR.parent / "backend"

# Configure Jinja2
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    variable_start_string="[[",
    variable_end_string="]]",
    undefined=StrictUndefined,
    keep_trailing_newline=True,
)

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
        soniType=soni_type,
        api_variable=api_variable,
        heading=heading,
    )

    output_path = FRONTEND_DIR / "src" / "components" / "pages" / f"{component_name}.tsx"

    if output_path.exists():
        raise FileExistsError(f"{output_path} already exists")

    output_path.write_text(generated_code, encoding="utf-8")

    print(f"Created {component_name} landing page: {output_path}")
    
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
    
    print(f"Added API address in frontend: {path}")
    
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
    
    print(f"Created route to new landing page and added to app: {path}")
    
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
    
    print(f"Added API router to app in backend: {path}")
    
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
        
    print(f"Added soniType metadata in frontend: {path}")


if __name__ == "__main__":
    
    soni_type = 'black_holes'
    component_name = 'BlackHoles'
    heading = 'Black Holes'
    
    # Convert snake case (light_curves) to camel case (lightCurves) for consistency in frontend
    words = soni_type.split('_')
    camel_case = words[0] + ''.join(word.capitalize() for word in words[1:])

    api_variable = f"{camel_case}API"
    
    add_api_router(soni_type=soni_type)
    
    add_api_config(soni_type=soni_type, api_variable=api_variable)
    
    generate_landing_page(
        component_name=component_name,
        soni_type=soni_type,
        api_variable=api_variable,
        heading="Exoplanets",
    )
    
    add_route(soni_type=soni_type, component_name=component_name)