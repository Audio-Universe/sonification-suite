import asyncio
from io import BytesIO
from types import SimpleNamespace

import pandas as pd
import pytest
from fastapi import HTTPException, UploadFile

import core


def make_settings(data_mode, sound, mappings, notes=None):
    return core.CustomStyleSettings(
        dataMode=data_mode,
        sound=sound,
        map=mappings,
        notes=notes or [],
        metadata={
            "mappingParams": [],
            "customNotes": False,
        },
    )


def test_format_style_converts_continuous_mappings(monkeypatch):
    monkeypatch.setattr(core, "is_synth", lambda sound: True)
    settings = make_settings(
        "continuous",
        "Example Synth",
        [
            {"input": "column 2", "output": "time"},
            {"input": "column 1", "output": "pitch", "output_range": [0, 0.5]},
        ],
    )

    style = core.format_style(settings)

    assert style["sources"] == "objects"
    assert style["generator"] == {"type": "synthesizer", "preset": "Example Synth"}
    assert style["map"] == [
        {"input": 1, "output": "time_evo"},
        {"input": 0, "output": "pitch_shift", "output_range": [0, 12]},
    ]


def test_format_style_converts_events_without_notes(monkeypatch):
    monkeypatch.setattr(core, "is_synth", lambda sound: False)
    settings = make_settings(
        "discrete",
        "Example Sample",
        [
            {"input": "column 1", "output": "time"},
            {"input": "column 2", "output": "pitch", "output_range": [0, 1]},
        ],
    )

    style = core.format_style(settings)

    assert style["sources"] == "events"
    assert style["generator"] == {"type": "sampler", "sample": "Example Sample"}
    assert style["map"] == [
        {"input": 0, "output": "time", "input_range": ["0%", "110%"]},
        {"input": 1, "output": "pitch_shift", "output_range": [0, 24]},
    ]
    assert style["pitch_binning"] == "uniform"


def test_format_style_keeps_pitch_mapping_for_events_with_notes(monkeypatch):
    monkeypatch.setattr(core, "is_synth", lambda sound: False)
    settings = make_settings(
        "discrete",
        "Example Sample",
        [{"input": "column 1", "output": "pitch", "output_range": [0, 1]}],
        notes=["C4"],
    )

    style = core.format_style(settings)

    assert style["map"][0]["output"] == "pitch"
    assert style["map"][0]["output_range"] == [0, 1]


def test_validate_import_rejects_unknown_sonification_type():
    with pytest.raises(HTTPException) as exc_info:
        core.validate_import(b"column\nvalue\n", "unknown", "example")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid soni_type: unknown"


def test_validate_import_saves_constellation_and_returns_metadata(
    monkeypatch, tmp_path, session_id
):
    monkeypatch.setattr(core, "TMP_DIR", tmp_path)
    (tmp_path / session_id).mkdir()
    csv_data = (
        "ra_corrected,dec,dist,pmra,pmdec,magnitude,absmag,colour,"
        "stick_figure,hip,custom_order\n"
        "1,2,3,4,5,6,7,8,0,22,2\n"
        "9,10,11,12,13,14,15,16,0,11,1\n"
    ).encode()

    file_ref, import_info = core.validate_import(
        csv_data, "constellations", "my-stars"
    )

    assert file_ref == "session:constellations.csv"
    assert import_info == {
        "data_name": "my-stars",
        "stick_figure": False,
        "star_count": 2,
        "custom_order": [11, 22],
    }
    saved_data = pd.read_csv(tmp_path / session_id / "constellations.csv")
    assert saved_data["hip"].tolist() == [22, 11]


def make_request():
    return SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))


def upload(filename, contents):
    return UploadFile(filename=filename, file=BytesIO(contents))


def test_upload_data_saves_csv_in_session_uploads(
    monkeypatch, tmp_path, session_id
):
    monkeypatch.setattr(core, "TMP_DIR", tmp_path)

    result = asyncio.run(
        core.upload_data(
            make_request(),
            upload("observations.csv", b"time,flux\n0,1\n"),
            soni_type=None,
        )
    )

    assert result["import_info"] is None
    assert result["file_ref"].startswith("session:uploads:")
    stored_file = (
        tmp_path / session_id / "uploads" / result["file_ref"].split(":")[-1]
    )
    assert stored_file.read_bytes() == b"time,flux\n0,1\n"


@pytest.mark.parametrize(
    ("filename", "expected_status"),
    [("observations.txt", 415), ("observations.backup.csv", 400)],
)
def test_upload_data_rejects_unsupported_or_multiple_extensions(
    filename, expected_status
):
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(core.upload_data(make_request(), upload(filename, b"data")))

    assert exc_info.value.status_code == expected_status


@pytest.mark.parametrize(
    ("contents", "expected_status"),
    [(b"", 400), (b"\xff\xfe", 415)],
)
def test_upload_data_rejects_empty_or_non_utf8_csv(contents, expected_status):
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            core.upload_data(make_request(), upload("observations.csv", contents))
        )

    assert exc_info.value.status_code == expected_status


def test_upload_data_enforces_session_quota(monkeypatch, tmp_path, session_id):
    monkeypatch.setattr(core, "TMP_DIR", tmp_path)
    monkeypatch.setattr(core, "UPLOAD_QUOTA_BYTES", 3)
    uploads_dir = tmp_path / session_id / "uploads"
    uploads_dir.mkdir(parents=True)
    (uploads_dir / "existing.csv").write_bytes(b"12")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            core.upload_data(
                make_request(), upload("new.csv", b"34"), soni_type=None
            )
        )

    assert exc_info.value.status_code == 429
