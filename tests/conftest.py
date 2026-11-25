import sys
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from skyfield.api import load
from skyfield.data import hipparcos
from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1] / "src" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# night_sky loads remote catalogue and ephemeris data at import time.
catalogue_values = [""] * len(hipparcos._COLUMN_NAMES)
for column, value in {
    "HIP": "1",
    "Vmag": "1.0",
    "RAdeg": "10.0",
    "DEdeg": "20.0",
    "Plx": "10.0",
    "pmRA": "1.0",
    "pmDE": "1.0",
    "B-V": "0.65",
}.items():
    catalogue_values[hipparcos._COLUMN_NAMES.index(column)] = value
catalogue = ("|".join(catalogue_values) + "\n").encode()
loader_type = type(load)
original_open = loader_type.open
original_call = loader_type.__call__
loader_type.open = lambda loader, url: BytesIO(catalogue)
loader_type.__call__ = lambda loader, filename: {"earth": object()}
try:
    import night_sky
finally:
    loader_type.open = original_open
    loader_type.__call__ = original_call

import core


@pytest.fixture
def backend_storage(tmp_path):
    root = tmp_path / "backend"
    return SimpleNamespace(
        root=root,
        tmp_dir=root / "tmp",
        analytics_dir=root / "analytics",
        style_files_dir=root / "style_files",
        suggested_data_dir=root / "suggested_data",
        synths_dir=root / "synths",
        samples_dir=root / "samples",
    )


@pytest.fixture
def api_client(backend_storage, monkeypatch):
    import StorageManager as storage_manager_module
    import analytics
    import constellations
    import data_composer
    import light_curves
    import main
    import night_sky
    import paths
    import utils
    from StorageManager import StorageManager

    backend_storage.tmp_dir.mkdir(parents=True)
    backend_storage.analytics_dir.mkdir(parents=True)
    backend_storage.style_files_dir.mkdir(parents=True)
    backend_storage.suggested_data_dir.mkdir(parents=True)
    backend_storage.synths_dir.mkdir(parents=True)
    backend_storage.samples_dir.mkdir(parents=True)

    for module in (
        paths,
        core,
        data_composer,
        light_curves,
        constellations,
        night_sky,
        utils,
        main,
    ):
        monkeypatch.setattr(module, "TMP_DIR", backend_storage.tmp_dir)

    monkeypatch.setattr(core, "STYLE_FILES_DIR", backend_storage.style_files_dir)
    monkeypatch.setattr(
        core, "SUGGESTED_DATA_DIR", backend_storage.suggested_data_dir
    )
    monkeypatch.setattr(core, "SYNTHS_DIR", backend_storage.synths_dir)
    monkeypatch.setattr(core, "SAMPLES_DIR", backend_storage.samples_dir)
    monkeypatch.setattr(
        storage_manager_module,
        "ANALYTICS_DIR",
        backend_storage.analytics_dir,
    )
    monkeypatch.setattr(analytics, "ANALYTICS_DIR", backend_storage.analytics_dir)
    monkeypatch.setattr(
        analytics, "LOCK_FILE", backend_storage.analytics_dir / "analytics.lock"
    )
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(
        main,
        "storage_manager",
        StorageManager(
            target_dir=backend_storage.tmp_dir,
            max_age_days=36500,
            disk_threshold_percent=100,
            emergency_threshold_percent=100,
            min_free_gb=0,
        ),
    )

    with TestClient(
        main.app,
        base_url="https://testserver",
        raise_server_exceptions=False,
    ) as client:
        yield client


@pytest.fixture
def session_file(api_client, backend_storage):
    def write_file(filename, contents, uploads=False):
        response = api_client.get("/core/session/")
        assert response.status_code == 200
        session_id = response.json()["session_id"]
        session_dir = backend_storage.tmp_dir / session_id
        if uploads:
            session_dir = session_dir / "uploads"
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / filename).write_bytes(
            contents.encode() if isinstance(contents, str) else contents
        )
        prefix = "session:uploads:" if uploads else "session:"
        return session_id, f"{prefix}{filename}"

    return write_file


@pytest.fixture
def session_id():
    token = core.session_id_var.set("pytest-session")
    yield "pytest-session"
    core.session_id_var.reset(token)
