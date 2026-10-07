# System Architecture

The Sonification Suite currently runs as a web app, built using a decoupled frontend/backend architecture and deployed on a single self-hosted Linux server.

## Backend

The backend is built with Python, using [FastAPI](https://fastapi.tiangolo.com/) as the web framework for the REST API. The decision to use Python in the backend was purely to allow us to integrate [STRAUSS](https://strauss.readthedocs.io/en/latest/), the sonification engine which powers much of the Suite's functionality.

As with most web apps, the backend handles the vast majority of the logic and data processing, sending data back to the frontend in a format it expects. By default, the API works over HTTPS, and data is sent back and forth in JSON format.

### Backend Structure

The majority of the backend functionality exists in the `src/backend` directory. The entry point for FastAPI is `main.py` - this is where the processes start and where we start the background cleanup task (more on this later).

The API routes are split into different python modules by their functionality or remit. For instance, you will find `light_curves.py` (for API endpoints relating to the light curve sonification type), `constellations.py` (for constellations), `night_sky.py` (for night sky), `data_composer.py` (for data composer), and `core.py` (for core functionality which is shared by all sonification types). Each of these has its own *router* which is then imported in `main.py`. This simply means that the API route for each endpoint is preceded by its router's prefix, e.g. `light-curves/search-lightcurves/` or `constellations/plot/`.

!!! info "Formatting API endpoints"
    Throughout the Suite, we use hyphens (`-`) in place of spaces in all API endpoints, e.g. `light-curves/`. We also use a trailing `/` at the end of each endpoint, e.g. `/search-lightcurves/`. This is purely a stylistic choice, but one used consistently to avoid confusion.

The full API documentation can be found [here](link to API).

## Data Layer

Unlike a traditional web app, the Suite does not make use of a database, as the added complexity of a database layer was not deemed necessary for the Suite's original purpose. As the project grows, it would be wise to add a database (e.g. if we want to add user logins/authentication, so that each user has persistent storage), but in its presently deployed state, the disk space on our self-hosted server is a hard limitation. Particularly as WAV files can quickly deplete storage, it was not feasible to allow users to 'save' their sonifications in-app (hence why downloading them is the main option).

The workaround is that we have various directories in the backend for our shared read-only data, such as `suggested_data`, `sound_assets`, and `style_files`. For user-specific data, e.g. datasets they have refined, sonifications they have generated etc., we use the `tmp` directory, using their session ID to create a unique directory to use as a temporary workspace.

!!! info "Sessions"
    When a new user connects (specifically, a new browser or tab), they are given a unique session ID. This is saved in the frontend as a browser cookie, and sent in the header with every request. This way, when the backend receives a request, it will know which user is asking, and therefore which directory in `tmp` to use.

    This isolates one user's work from another, making it safe for multiple users to use the Suite at once.

    In the backend, the session ID is stored as a Python context variable, so it can be accessed from anywhere. See the `@app.middleware` section in `main.py` and the `/session/` endpoint in `core.py` to see how it works.

### File referencing

You will see `file_ref` used quite a lot in the backend, and `fileRef` or `dataRef`, `styleRef` etc. in the frontend. We use a file referencing system so as to not expose the full filepaths/internal structure of the production server, and to avoid any cross-platform formatting errors (e.g. `/` vs `\`).

We replace slashes with a colon and use `session` as a prefix if the file lives in the user's session directory, e.g. `session:audio_figure.wav`. A file ref for a shared file might be e.g. `style_files:constellations:mallets.yml`.

The `resolve_file` function in `utils.py` translates these references into their full filepaths, returning a Path object from [pathlib](https://docs.python.org/3/library/pathlib.html) (which is used often in the app).