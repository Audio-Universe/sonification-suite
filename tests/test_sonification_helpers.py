from pathlib import Path

import pandas as pd
import pytest

import sonification_helpers as helpers
from request_models import LayerRequest, SonificationRequest


def test_get_source_names_returns_ids_only_for_supported_data_types():
    frame = pd.DataFrame({"hip": [1, 2], "display_name": ["A", "B"]})

    assert helpers.get_source_names(frame, "constellations", LayerRequest(
        data_ref="data", style_ref="style"
    )) == ["A", "B"]
    assert helpers.get_source_names(
        frame,
        "data_composer",
        LayerRequest(data_ref="data", style_ref="style", id_column="hip"),
    ) == [1, 2]
    assert helpers.get_source_names(frame, "light_curves", LayerRequest(
        data_ref="data", style_ref="style"
    )) is None


def test_preprocess_style_adds_note_limit_and_custom_constellation_order(
    monkeypatch, tmp_path
):
    style_path = tmp_path / "style.yml"
    style_path.write_text("placeholder")
    style = {
        "generator": {"preset": "Example"},
        "map": [{"output": "time", "function": "invert"}],
    }
    monkeypatch.setattr(helpers, "read_YAML_file", lambda path: style)
    monkeypatch.setattr(helpers, "write_sound_to_style", lambda value: value)
    monkeypatch.setattr(helpers, "is_time_series", lambda df, value: True)
    request = SonificationRequest(
        soni_type="constellations",
        layers=[{"data_ref": "data", "style_ref": "style"}],
        duration=5,
        system="stereo",
        data_name="example",
        observer=None,
    )
    frame = pd.DataFrame({"custom_order": [2, 1]})

    result = helpers.preprocess_style(style_path, frame, request)

    assert result["max_notes_per_sec"] == 10
    assert result["map"] == [
        {"output": "time", "function": None, "input": "custom_order"}
    ]


def test_place_on_dome_maps_stereo_position_and_removes_spatial_mappings(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        helpers,
        "handle_observer",
        lambda observer: {
            "STRAUSS_inputs": {"pan": 0.25, "azimuth": 30, "polar": 60},
            "display_values": {"altitude": 45, "azimuth": 30},
        },
    )
    monkeypatch.setattr(helpers, "write_YAML_file", lambda style: tmp_path / "style.yml")
    style = {
        "map": [
            {"output": "pan"},
            {"output": "pitch"},
            {"output": "azimuth"},
        ]
    }
    kwargs = {}

    result = helpers.place_on_dome(
        {"latitude": 0}, style, kwargs, "stereo"
    )

    assert result == [45, 30]
    assert kwargs["fix_pan"] == 0.25
    assert style["map"] == [{"output": "pitch"}]
    assert kwargs["style"] == str(tmp_path / "style.yml")


def test_place_on_dome_rejects_mono(monkeypatch):
    monkeypatch.setattr(
        helpers,
        "handle_observer",
        lambda observer: {
            "STRAUSS_inputs": {"pan": 0.5},
            "display_values": {"altitude": 45, "azimuth": 30},
        },
    )
    with pytest.raises(
        ValueError, match="Place on Dome feature not available for mono audio"
    ):
        helpers.place_on_dome(
            {"latitude": 0}, {"map": []}, {}, "mono"
        )


def test_write_mapping_table_writes_table_to_session_directory(tmp_path):
    class FakeFigure:
        def get_table(self, name, source):
            assert name == "sonification_1"
            assert source == "source_0"
            return pd.DataFrame({"value": [1]})

    helpers.write_mapping_table(
        FakeFigure(),
        {"sources": "objects", "map": []},
        "light_curves",
        None,
        pd.DataFrame(),
        1,
        Path(tmp_path),
    )

    assert pd.read_csv(tmp_path / "mapping_table_1.csv").to_dict("list") == {
        "value": [1]
    }
