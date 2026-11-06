# Installation

For local installation and development, follow these instructions.

## Prerequisites

Before getting started, ensure you have the following installed:

- **Git** – for cloning the repository.
- **Python** – for running the backend.
- **Node.js and npm (included with Node.js)** – for running the frontend.

## Clone the repo

Clone the repository from GitHub:

```bash
git clone https://github.com/Audio-Universe/sonification-suite.git
```

Navigate into the project directory:

```bash
cd sonification-suite
```

## Backend setup

The backend dependencies are defined in the root `pyproject.toml` file.

From the project root, install the dependencies:

```bash
pip install .
```

Once the dependencies have been installed, navigate to the backend directory:

```bash
cd src/backend
```

Start the development server:

```bash
uvicorn main:app --reload
```

The backend API will now be available locally. You can access the automatically generated API documentation at:

`http://localhost:8000/docs`

The `--reload` flag automatically restarts the server whenever changes are made to the backend code.

## Frontend setup

Open a separate terminal and navigate to the frontend directory:

```bash
cd src/frontend
```

Install the frontend dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The frontend will typically be available at:

`http://localhost:5173`

Vite provides hot module replacement, meaning changes to the frontend code are reflected in the browser without needing to restart the development server.

## Running the application

Once both servers are running:

1. Ensure the backend server is running.
2. Ensure the frontend development server is running.
3. Open `http://localhost:5173` in your browser.

You should now be able to use the Suite locally.