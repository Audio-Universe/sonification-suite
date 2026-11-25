import asyncio
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
import yaml
from fastapi import HTTPException, Response, UploadFile

import core
import utils
from request_models import CustomStyleSettings, DataRequest


def test_get_or_create_session_creates_cookie_directory_and_analytics(
    monkeypatch, tmp_path
):
    session_dir = tmp_path / "new-session"
    monkeypatch.setattr(core, "TMP_DIR", tmp_path)
    monkeypatch.setattr(core.uuid, "uuid4", lambda: "new-session")
    monkeypatch.setattr(core, "is_bot", lambda user_agent: False)
    events = []
    monkeypatch.setattr(core, "log_event", lambda **kwargs: events.append(kwargs))
    response = Response()

    result = core.get_or_create_session(
        SimpleNamespace(
            headers={"user-agent": "browser"},
            client=SimpleNamespace(host="127.0.0.1"),
        ),
        response,
        session_id=None,
    )

    assert result == {"session_id": "new-session"}
    assert session_dir.is_dir()
    assert response.headers["set-cookie"].startswith("session_id=new-session")
    assert events[0]["event"] == "session_start"


def test_get_or_create_session_skips_analytics_for_bots(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(core, "TMP_DIR", tmp_path)
    monkeypatch.setattr(core.uuid, "uuid4", lambda: "bot-session")
    monkeypatch.setattr(core, "is_bot", lambda user_agent: True)
    monkeypatch.setattr(
        core,
        "log_event",
        lambda **kwargs: pytest.fail("bot session should not be logged"),
    )

    core.get_or_create_session(
        SimpleNamespace(
            headers={"user-agent": "crawler"},
            client=SimpleNamespace(host="127.0.0.1"),
        ),
        Response(),
        session_id=None,
    )

    assert (tmp_path / "bot-session").is_dir()


def test_get_inputs_for_composer_and_builtin_constellations(
    monkeypatch, tmp_path
):
    data = tmp_path / "data.csv"
    pd.DataFrame(
        {"numeric": [1, 2], "label": ["a", "b"], "custom_order": [2, 1]}
    ).to_csv(data, index=False)
    monkeypatch.setattr(core, "resolve_file", lambda ref: data)

    composer_inputs = core.get_inputs("session:data.csv", "data_composer")
    constellation_inputs = core.get_inputs(
        "session:data.csv", "constellations"
    )

    assert composer_inputs == [
        {"name": "numeric", "desc": "", "key": "numeric", "numeric": True},
        {"name": "label", "desc": "", "key": "label", "numeric": False},
        {
            "name": "custom_order",
            "desc": "",
            "key": "custom_order",
            "numeric": True,
        },
    ]
    assert constellation_inputs[-1] == {
        "name": "Custom Order",
        "desc": "Your chosen star order - map this to Time",
        "key": "custom_order",
        "numeric": True,
    }


def test_get_inputs_rejects_non_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(core, "resolve_file", lambda ref: tmp_path / "data.txt")

    with pytest.raises(HTTPException) as exc_info:
        core.get_inputs("session:data.txt", "data_composer")

    assert exc_info.value.status_code == 400


def test_get_outputs_matches_declared_output_metadata():
    outputs = core.get_outputs()

    assert {output["key"] for output in outputs} == set(core.OUTPUTS)
    assert all(set(output) == {"name", "desc", "key"} for output in outputs)


def test_get_suggested_and_styles_read_metadata_files(
    monkeypatch, tmp_path
):
    suggested_dir = tmp_path / "suggested" / "light_curves"
    styles_dir = tmp_path / "styles" / "light_curves"
    suggested_dir.mkdir(parents=True)
    styles_dir.mkdir(parents=True)
    (suggested_dir / "example.yml").write_text(
        yaml.safe_dump(
            {
                "name": "Example",
                "description": "A test dataset",
                "ra": 10,
                "dec": 20,
                "category": "Test",
            }
        )
    )
    (styles_dir / "example.yml").write_text(
        yaml.safe_dump({"name": "Warm", "description": "Warm tone"})
    )
    monkeypatch.setattr(core, "SUGGESTED_DATA_DIR", tmp_path / "suggested")
    monkeypatch.setattr(core, "STYLE_FILES_DIR", tmp_path / "styles")

    suggested = core.get_suggested("light_curves")
    styles = core.get_styles("light_curves")

    assert suggested == [
        {
            "name": "Example",
            "description": "A test dataset",
            "ra": 10,
            "dec": 20,
            "file_ref": "suggested_data:light_curves:example.csv",
            "category": "Test",
        }
    ]
    assert styles == [
        {
            "name": "Warm",
            "description": "Warm tone",
            "file_ref": "style_files:light_curves:example.yml",
        }
    ]


@pytest.mark.parametrize("endpoint", ["suggested", "styles"])
def test_catalog_endpoints_return_404_for_missing_directories(
    monkeypatch, tmp_path, endpoint
):
    monkeypatch.setattr(core, "SUGGESTED_DATA_DIR", tmp_path / "missing-data")
    monkeypatch.setattr(core, "STYLE_FILES_DIR", tmp_path / "missing-styles")

    function = core.get_suggested if endpoint == "suggested" else core.get_styles
    with pytest.raises(HTTPException) as exc_info:
        function("not-found")
    assert exc_info.value.status_code == 404


def test_get_sounds_classifies_synths_and_samples(monkeypatch, tmp_path):
    synths = tmp_path / "synths"
    samples = tmp_path / "samples"
    synths.mkdir()
    samples.mkdir()
    (synths / "Keys.yml").touch()
    (synths / "White Noise.yml").touch()
    harp = samples / "Harp"
    harp.mkdir()
    (harp / "note.wav").touch()
    strings = samples / "Strings"
    strings.mkdir()
    (strings / "one.wav").touch()
    (strings / "two.wav").touch()
    soundfont = samples / "Soundfont"
    soundfont.mkdir()
    (soundfont / "library.sf2").touch()
    monkeypatch.setattr(core, "SYNTHS_DIR", synths)
    monkeypatch.setattr(core, "SAMPLES_DIR", samples)

    sounds = {sound.name: sound for sound in core.get_sounds()}

    assert sounds["Keys"].composable is True
    assert sounds["White Noise"].composable is False
    assert sounds["Harp"].data_modes == ["discrete"]
    assert sounds["Strings"].composable is True
    assert sounds["Strings"].data_modes == ["continuous"]
    assert sounds["Soundfont"].composable is True


def test_get_sound_info_returns_sound_list(monkeypatch):
    monkeypatch.setattr(core, "get_sounds", lambda: ["sound"])

    assert core.get_sound_info() == ["sound"]


def test_save_and_convert_style_settings_round_trip(
    monkeypatch, tmp_path, session_id
):
    monkeypatch.setattr(core, "TMP_DIR", tmp_path)
    monkeypatch.setattr(utils, "TMP_DIR", tmp_path)
    monkeypatch.setattr(core, "is_synth", lambda sound: True)
    settings = CustomStyleSettings(
        dataMode="continuous",
        sound="Keys",
        map=[{"input": "column 1", "output": "time"}],
        notes=[],
        metadata={"mappingParams": [], "customNotes": False},
    )

    saved = core.save_style_settings(settings)
    style_path = tmp_path / session_id / saved["file_ref"].split(":")[-1]
    monkeypatch.setattr(core, "resolve_file", lambda ref: style_path)

    loaded = core.convert_style_to_settings(
        DataRequest(file_ref=saved["file_ref"])
    )

    assert loaded["data_mode"] == "continuous"
    assert loaded["sound_name"] == "Keys"
    assert loaded["map"] == [{"input": 0, "output": "time_evo"}]


def test_preview_style_settings_generates_preview_audio(
    monkeypatch, tmp_path, session_id
):
    session_dir = tmp_path / session_id
    session_dir.mkdir()
    style_path = tmp_path / "source.yml"
    style_path.write_text("style")
    calls = {}

    class FakeFigure:
        def sonify(self, *args, **kwargs):
            calls["args"] = args
            calls["kwargs"] = kwargs

        def save(self, path):
            Path(path).write_bytes(b"preview")

    monkeypatch.setattr(core, "TMP_DIR", tmp_path)
    monkeypatch.setattr(core, "resolve_file", lambda ref: style_path)
    monkeypatch.setattr(
        core,
        "read_YAML_file",
        lambda path: {
            "sources": "objects",
            "map": [
                {"output": "time_evo"},
                {"output": "volume"},
            ],
        },
    )
    monkeypatch.setattr(core, "write_sound_to_style", lambda style: style)
    monkeypatch.setattr(core, "write_YAML_file", lambda style: tmp_path / "preview.yml")
    monkeypatch.setattr(core, "AudioFigure", FakeFigure)

    result = core.preview_style_settings(DataRequest(file_ref="style_files:x:y.yml"))

    assert result["file_ref"].startswith("session:preview_")
    assert result["file_ref"].endswith(".wav")
    assert len(calls["args"]) == 2
    assert len(calls["args"][0]) == 100
    assert calls["args"][0][0] == 0
    assert calls["args"][0][-1] == 1
    assert calls["kwargs"] == {
        "style": str(tmp_path / "preview.yml"),
        "duration": 5,
    }
    assert (session_dir / result["file_ref"].split(":")[-1]).read_bytes() == b"preview"


def test_upload_data_imports_suite_light_curve(
    monkeypatch, tmp_path, session_id
):
    session_dir = tmp_path / session_id
    session_dir.mkdir()
    monkeypatch.setattr(core, "TMP_DIR", tmp_path)
    file = UploadFile(
        filename="curve.csv",
        file=BytesIO(b"time,flux\n0,1\n1,2\n"),
    )
    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))

    result = asyncio.run(
        core.upload_data(request, file, soni_type="light_curves")
    )

    assert result == {
        "file_ref": "session:light_curves.csv",
        "import_info": {"data_name": "curve"},
    }
    assert pd.read_csv(session_dir / "light_curves.csv")["flux"].tolist() == [
        1,
        2,
    ]


def test_upload_style_saves_valid_yaml_and_returns_metadata(
    monkeypatch, tmp_path, session_id
):
    monkeypatch.setattr(core, "TMP_DIR", tmp_path)
    contents = b"name: Custom Tone\ndescription: user supplied\n"
    file = UploadFile(filename="custom.yml", file=BytesIO(contents))
    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))

    result = asyncio.run(core.upload_style(file=file, request=request))
    stored = (
        tmp_path
        / session_id
        / "uploads"
        / result["file_ref"].split(":")[-1]
    )

    assert result["style_name"] == "Custom Tone"
    assert result["style_description"] == "user supplied"
    assert stored.read_bytes() == contents


@pytest.mark.parametrize(
    ("filename", "contents", "status"),
    [
        ("bad.txt", b"name: Test", 415),
        ("double.ext.yml", b"name: Test", 400),
        ("empty.yml", b"", 400),
        ("bad.yml", b"name: [", 415),
        ("invalid.yml", b"\xff", 415),
    ],
)
def test_upload_style_rejects_invalid_files(filename, contents, status):
    file = UploadFile(filename=filename, file=BytesIO(contents))
    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(core.upload_style(file=file, request=request))
    assert exc_info.value.status_code == status
