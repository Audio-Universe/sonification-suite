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

The full documentation for all API endpoints can be found [here](../api-reference).

## Data Layer

Unlike a traditional web app, the Suite does not make use of a database, as the added complexity of a database layer was not deemed necessary for the Suite's original purpose. As the project grows, it would be wise to add a database (e.g. if we want to add user logins/authentication, so that each user has persistent storage), but in its presently deployed state, the disk space on our self-hosted server is a hard limitation. Particularly as WAV files can quickly deplete storage, it was not feasible to allow users to 'save' their sonifications in-app (hence why downloading them is the main option).

The workaround is that we have various directories in the backend for our shared read-only data, such as `suggested_data`, `sound_assets`, and `style_files`. For user-specific data, e.g. datasets they have refined, sonifications they have generated etc., we use the `tmp` directory, using their session ID to create a unique directory to use as a temporary workspace.

!!! info "Sessions"
    When a new user connects (specifically, a new browser or tab), they are given a unique session ID. This is saved in the frontend as a browser cookie, and sent in the header with every request. This way, when the backend receives a request, it will know which user is asking, and therefore which directory in `tmp` to use.

    This isolates one user's work from another, making it safe for multiple users to use the Suite at once.

    In the backend, the session ID is stored as a Python context variable, so it can be accessed from anywhere. See the `@app.middleware` section in `main.py` and the `/session/` endpoint in `core.py` to see how it works.

### File Referencing

You will see `file_ref` used quite a lot in the backend, and `fileRef` or `dataRef`, `styleRef` etc. in the frontend. We use a file referencing system so as to not expose the full filepaths/internal structure of the production server, and to avoid any cross-platform formatting errors (e.g. `/` vs `\`).

We create file refs by replacing slashes with a colon and using `session` as a prefix if the file lives in the user's session directory, e.g. `session:audio_figure.wav`. A file ref for a shared file might be e.g. `style_files:constellations:mallets.yml`. The last element of a file ref is always the file name with suffix e.g. `beta_persei.csv`.

The `resolve_file` function in `utils.py` translates these references into their full filepaths, returning a Path object from [pathlib](https://docs.python.org/3/library/pathlib.html) (which is used often in the app).

### Storage Management

With all of these session directories for each user, disk space on the server quickly gets eaten up. We have a few strategies for dealing with this - none are perfect, but they work within the confines of our self-hosted server.

#### File Naming
Firstly, we make use of identical file names in certain situations to force overwriting to the same file, hence avoiding writing to lots of new files that might only be temporary. This only makes sense where it is safe to do so, I.E. any time a user will only need **one** of something. 

For instance, if a user searches for lightcurves, clicking 'plot' on each one will download the data on server, plot it, and return the image. If each user plots a handful of light curves, and each one is written to its own file, we will quickly bloat the server with data which we don't need. Hence, because each user will only ever need one light curve at a time, we overwrite `light_curves.csv` in the user's unique session directory each time. The same happens for constellations and night sky. 

For Data Composer, each user-uploaded dataset is given a unique ID (as this is a security requirement from the University cyber team) and written to an `uploads` directory in the user's session directory. Each time a user uploads a file, we check the size of their session directory. If uploading the file would take it over the session quota (50 MB) it is rejected. We have a file name for each layer audio (`layer_1.wav`, `layer_2.wav` etc.) and one for the combined 'master' audio `audio_figure.wav`.

#### Storage Manager
We also implement a StorageManager class (`StorageManager.py`) which runs in the background and deletes any session directories older than 1 week (we can likely reduce this in the future, as any one user is unlikely to have a tab open for one week working on the same sonification).

The storage manager also checks the overall disk space on the server, and will trigger a cleanup of the oldest session directories if the disk is over 70% full. If it is over 80% full, a more aggressive cleanup is triggered, which simply means it deletes more session directories to reach a lower target disk usage.

The storage manager runs once every 6 hours to check disk space and clean up any old session directories. It is launched at startup (in `main.py`), and because we use 2 Uvicorn workers on our web server (I.E. two seprate processes), we use a [file lock](https://en.wikipedia.org/wiki/File_locking) to ensure only one process runs the cleanup.

The StorageManager class has several attributes in its constructor which may be tweaked in the future, such as `max_age_days`, `disk_threshold_percent`, `cleanup_interval_hours`, `emergency_threshold_percent`, and `min_free_gb`.


## Frontend

The frontend is built using TypeScript and React. React is a JavaScript framework which facilitates single-page component-based user interfaces, and TypeScript is an extension of the JavaScript language that adds static typing (meaning the data types of variables are known before run time, helping to catch bugs early). 

We also use Vite in development to run the development server and build the frontend (I.E. compile the frontend code into the assets that are ultimately served to the browser).

We use ChakraUI v3 throughout as our component library. This means that all UI elements like buttons, sliders, inputs etc. come from the same place and have a shared style.
