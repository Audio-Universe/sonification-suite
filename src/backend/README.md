# Sonification Suite - Backend

The backend for the Sonification Suite uses Python and the FastAPI web framework to handle API requests from the frontend.

It uses Uvicorn under the hood to act as the actual web server.

## Getting Started

### Prerequisites

* Python
* pip

### Installation

All Python dependencies are managed through `pyproject.toml` at the project root.

From the project root, install the project and its dependencies using:

```bash
pip install .
```

### Running in Development

Navigate to the backend directory:

```bash
cd src/backend
```

Start the development server:

```bash
uvicorn main:app --reload
```

The --reload flag ensures the backend automatically reboots if it detects any changes to the backend files.
This is handy in development, but the file watching slows things down, so don't use the --reload flag in production.

### Running in Production

In production, you can also specify the number of uvicorn workers. Each worker is a separate CPU process, so having more workers allows the app to handle multiple simultaneous requests. However, each worker has its own portion of memory allocated, and each loads the entire app, which can strain RAM depending on hardware limitations. A general rule of thumb for choosing the number of workers is (2 * number of CPU cores) + 1, but you should check your server's available RAM before following this blindly.

The command to run the backend in production (with e.g. 3 workers) is: 

```bash
uvicorn main:app --workers 3
```
