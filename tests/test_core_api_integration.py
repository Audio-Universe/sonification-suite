import base64
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from scipy.io import wavfile

import core
import main


def start_session(client: TestClient) -> str:
    response = client.get("/core/session/")
    assert response.status_code == 200
    return response.json()["session_id"]


def test_session_cookie_is_created_and_persisted(api_client):
    first = api_client.get("/core/session/")

    assert first.status_code == 200
    session_id = first.json()["session_id"]
    cookie = first.headers["set-cookie"]
    assert api_client.cookies.get("session_id") == session_id
    assert "httponly" in cookie.lower()
    assert "secure" in cookie.lower()
    assert "samesite=none" in cookie.lower()
    assert (api_client.cookies.get("session_id")) == session_id

    second = api_client.get("/core/session/")

    assert second.status_code == 200
    assert second.json() == {"session_id": session_id}
    assert "set-cookie" not in second.headers


def test_separate_clients_receive_independent_sessions(
    api_client, backend_storage
):
    first_session = start_session(api_client)

    with TestClient(
        main.app,
        base_url="https://testserver",
        raise_server_exceptions=False,
    ) as second_client:
        second_session = start_session(second_client)
        assert second_client.cookies.get("session_id") == second_session

    assert first_session != second_session
    assert (backend_storage.tmp_dir / first_session).is_dir()
    assert (backend_storage.tmp_dir / second_session).is_dir()


def test_core_method_and_request_validation(api_client):
    assert api_client.get("/core/upload-data/").status_code == 405
    assert api_client.post("/core/get-outputs/").status_code == 405

    missing_body = api_client.post("/core/generate-spectrogram/", json={})
    missing_query = api_client.get("/core/get-inputs/")

    assert missing_body.status_code == 422
    assert missing_query.status_code == 422
    assert missing_body.json()["detail"][0]["loc"] == ["body", "file_ref"]


def test_get_outputs_returns_expected_response_structure(api_client):
    response = api_client.get("/core/get-outputs/")

    assert response.status_code == 200
    outputs = response.json()
    assert isinstance(outputs, list)
    assert outputs
    assert all(set(output) == {"name", "desc", "key"} for output in outputs)


def test_upload_csv_then_read_inputs_and_download(
    api_client, backend_storage
):
    session_id = start_session(api_client)
    contents = b"time,flux\n0,1.5\n1,2.5\n"

    uploaded = api_client.post(
        "/core/upload-data/",
        files={"file": ("lightcurve.csv", contents, "text/csv")},
    )

    assert uploaded.status_code == 200
    result = uploaded.json()
    assert result["import_info"] is None
    assert result["file_ref"].startswith("session:uploads:")
    upload_name = result["file_ref"].split(":")[-1]
    saved_file = (
        backend_storage.tmp_dir / session_id / "uploads" / upload_name
    )
    assert saved_file.read_bytes() == contents

    inputs = api_client.get(
        "/core/get-inputs/",
        params={
            "file_ref": result["file_ref"],
            "soni_type": "data_composer",
        },
    )
    assert inputs.status_code == 200
    assert inputs.json() == [
        {"name": "time", "desc": "", "key": "time", "numeric": True},
        {"name": "flux", "desc": "", "key": "flux", "numeric": True},
    ]

    download = api_client.get(f"/core/download/{result['file_ref']}")
    assert download.status_code == 200
    assert download.content == contents
    assert download.headers["cache-control"] == "no-store, max-age=0"


def test_upload_data_rejects_bad_extension_over_http(api_client):
    response = api_client.post(
        "/core/upload-data/",
        files={"file": ("payload.txt", b"not csv", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Uploaded data must be in .csv format"


def test_save_and_convert_style_settings_over_http(api_client, monkeypatch):
    start_session(api_client)
    monkeypatch.setattr(core, "is_synth", lambda sound: True)
    payload = {
        "dataMode": "continuous",
        "sound": "Test Synth",
        "map": [{"input": "column 1", "output": "time"}],
        "notes": [],
        "metadata": {"mappingParams": [], "customNotes": False},
    }

    saved = api_client.post("/core/save-style-settings/", json=payload)

    assert saved.status_code == 200
    file_ref = saved.json()["file_ref"]
    assert file_ref.startswith("session:style_")

    converted = api_client.post(
        "/core/convert-style-to-settings/",
        json={"file_ref": file_ref},
    )

    assert converted.status_code == 200
    assert converted.json() == {
        "data_mode": "continuous",
        "sound_name": "Test Synth",
        "map": [{"input": 0, "output": "time_evo"}],
        "notes": [],
        "metadata": {
            "mappingParams": [],
            "customNotes": False,
            "rootNote": None,
            "harmony": None,
            "octaveRange": None,
        },
    }


def test_style_settings_request_validation_over_http(api_client):
    response = api_client.post(
        "/core/save-style-settings/",
        json={"dataMode": "continuous", "sound": "Synth"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]


def test_preview_style_settings_uses_http_request_and_returns_file_ref(
    api_client, backend_storage, monkeypatch
):
    session_id = start_session(api_client)
    style_path = backend_storage.root / "source.yml"
    style_path.write_text("source: test")

    class FakeFigure:
        def sonify(self, *args, **kwargs):
            assert len(args) == 1
            assert len(args[0]) == 100
            assert kwargs["duration"] == 5

        def save(self, path):
            Path(path).write_bytes(b"preview-audio")

    monkeypatch.setattr(core, "resolve_file", lambda ref: style_path)
    monkeypatch.setattr(
        core,
        "read_YAML_file",
        lambda path: {
            "sources": "objects",
            "generator": {"preset": "test"},
            "map": [{"output": "time_evo"}],
        },
    )
    monkeypatch.setattr(core, "write_sound_to_style", lambda style: style)
    monkeypatch.setattr(
        core,
        "write_YAML_file",
        lambda style: backend_storage.root / "preview.yml",
    )
    monkeypatch.setattr(core, "AudioFigure", FakeFigure)

    response = api_client.post(
        "/core/preview-style-settings/",
        json={"file_ref": "style_files:light_curves:test.yml"},
    )

    assert response.status_code == 200
    file_ref = response.json()["file_ref"]
    assert file_ref.startswith("session:preview_")
    assert file_ref.endswith(".wav")
    assert (
        backend_storage.tmp_dir
        / session_id
        / file_ref.split(":")[-1]
    ).read_bytes() == b"preview-audio"


def test_upload_style_over_http_returns_file_ref_and_metadata(
    api_client, backend_storage
):
    session_id = start_session(api_client)
    contents = b"name: API Style\ndescription: uploaded through HTTP\n"

    response = api_client.post(
        "/core/upload-style/",
        files={"file": ("style.yml", contents, "application/yaml")},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["style_name"] == "API Style"
    assert result["style_description"] == "uploaded through HTTP"
    assert result["file_ref"].startswith("session:uploads:")
    assert (
        backend_storage.tmp_dir
        / session_id
        / "uploads"
        / result["file_ref"].split(":")[-1]
    ).read_bytes() == contents


def test_suggested_data_missing_directory_returns_http_404(api_client):
    response = api_client.get("/core/suggested-data/missing/")

    assert response.status_code == 404
    assert "Suggested data directory" in response.json()["detail"]


def test_sound_info_route_returns_json_list_from_isolated_assets(api_client):
    response = api_client.get("/core/sound_info/")

    assert response.status_code == 200
    assert response.json() == []


def test_mix_layer_volumes_route_validates_and_returns_file_reference(api_client):
    response = api_client.post(
        "/core/mix-layer-volumes/", json={"volumes": [1.0, 1.0]}
    )
    invalid = api_client.post("/core/mix-layer-volumes/", json={})

    assert response.status_code == 200
    assert response.json() == {"file_ref": "session:audio_figure.wav"}
    assert invalid.status_code == 422


def test_generate_sonification_route_reports_duration_limit(api_client):
    response = api_client.post(
        "/core/generate-sonification/",
        json={
            "soni_type": "light_curves",
            "layers": [{"data_ref": "data", "style_ref": "style"}],
            "duration": core.MAX_DURATION + 1,
            "system": "stereo",
            "data_name": "example",
            "observer": None,
        },
    )

    assert response.status_code == 400
    assert "maximum length" in response.json()["detail"]


def test_generate_spectrogram_over_http_returns_png(
    api_client, backend_storage
):
    session_id = start_session(api_client)
    session_dir = backend_storage.tmp_dir / session_id
    path = session_dir / "audio.wav"
    sample_rate = 22050
    samples = (
        np.sin(2 * np.pi * 440 * np.arange(4096) / sample_rate)
        * np.iinfo(np.int32).max
    ).astype(np.int32)
    wavfile.write(path, sample_rate, samples)

    response = api_client.post(
        "/core/generate-spectrogram/",
        json={"file_ref": "session:audio.wav"},
    )

    assert response.status_code == 200
    image = base64.b64decode(response.json()["image"])
    assert image.startswith(b"\x89PNG\r\n\x1a\n")


def test_audio_endpoint_serves_file_and_validates_format(
    api_client, backend_storage
):
    session_id = start_session(api_client)
    audio_path = backend_storage.tmp_dir / session_id / "audio.wav"
    audio_path.write_bytes(b"test audio")

    response = api_client.get(
        "/core/audio/session:audio.wav", params={"name": "sample"}
    )
    invalid = api_client.get(
        "/core/audio/session:audio.wav",
        params={"name": "sample", "audio_format": "ogg"},
    )

    assert response.status_code == 200
    assert response.content == b"test audio"
    assert response.headers["content-type"] == "audio/wav"
    assert "sample.wav" in response.headers["content-disposition"]
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "Audio format must be 'wav' or 'mp3'"


def test_missing_style_directory_returns_http_404(api_client):
    response = api_client.get("/core/styles/missing/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Style directory not found"


def test_unhandled_core_error_uses_generic_http_500(api_client, backend_storage):
    session_id = start_session(api_client)
    uploads = backend_storage.tmp_dir / session_id / "uploads"
    uploads.mkdir()
    (uploads / "data.csv").write_text("value\n1\n")

    response = api_client.get(
        "/core/get-inputs/",
        params={
            "file_ref": "session:uploads:data.csv",
            "soni_type": "unknown",
        },
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
