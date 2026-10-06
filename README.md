# Sonification Suite
[![Documentation](https://readthedocs.org/projects/sonification-suite/badge/?version=latest)](https://sonification-suite.readthedocs.io/)
![License](https://img.shields.io/github/license/Audio-Universe/sonification-suite)
![Version](https://img.shields.io/badge/version-v1-success)

![Landing Page](docs/landing-page.png)

The Sonification Suite allows you to turn data into sound. Currently we have two separate modules on offer:

- [**For Planetaria:**](https://sonificationsuite.ncl.ac.uk/planetaria) tailor made astronomy datasets and sound design options, for use in a planetarium or other science communication context.
- [**Data Composer:**](https://sonificationsuite.ncl.ac.uk/data-composer) upload any tabulated data, representing any topics, to be turned into sound.


🌐 Live application: https://sonificationsuite.ncl.ac.uk

📖 Documentation: https://sonification-suite.readthedocs.io/en/latest/

## Features
 The *Planetaria* module is designed to make astronomy communication more accessible and immersive. These are a handful of the features available in version 1:

- Search for a star and turn its light into sound
- Enter your location and hear the stars appear around you
- Pick a constellation and play the stars in a custom order
- Create your own custom sound designs

Alternatively, use the *Data Composer* module to upload any data and turn it into sound. 

## Tech Stack

- **Frontend:** React, TypeScript, Vite  
- **Backend:** Python, FastAPI  
- **Astronomy Data:** `astroquery`, `lightkurve`, `skyfield`  
- **Sonification:** `STRAUSS`

## Local Setup

### Prerequisites

- Node.js >= 20  
- Python >= 3.11  
- `pip` package manager  

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/Audio-Universe/sonification-suite.git
```

2. **Setup and run the backend**

```bash
cd sonification-suite

pip install .

cd src/backend

uvicorn main:app
```

The FastAPI server should be running at http://127.0.0.1:8000

You can find the documentation of the API available at http://127.0.0.1:8000/docs

3. **Setup and run the frontend**

Open a new terminal and navigate to the project root, then

```bash
cd src/frontend

npm install

npm run dev
```

Open a web browser window and navigate to http://localhost:5173/

## License

This project is licensed under the GNU GPL v3.0 license. See LICENSE for more details.