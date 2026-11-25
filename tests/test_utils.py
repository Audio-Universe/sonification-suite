import random

import numpy as np
import pandas as pd
import pytest
import yaml
from fastapi import HTTPException

import utils


def test_resolve_file_handles_session_upload_and_missing_refs(
    monkeypatch, tmp_path, session_id
):
    monkeypatch.setattr(utils, "TMP_DIR", tmp_path)
    upload = tmp_path / session_id / "uploads" / "data.csv"
    upload.parent.mkdir(parents=True)
    upload.write_text("x\n1\n")

    assert utils.resolve_file("session:uploads:data.csv") == upload

    with pytest.raises(HTTPException) as exc_info:
        utils.resolve_file("session:uploads:missing.csv")
    assert exc_info.value.status_code == 400


def test_is_synth_distinguishes_synth_sample_and_missing_sound(monkeypatch, tmp_path):
    synths = tmp_path / "synths"
    samples = tmp_path / "samples"
    synths.mkdir()
    samples.mkdir()
    (synths / "Keys.yml").touch()
    (samples / "Harp").mkdir()
    monkeypatch.setattr(utils, "SYNTHS_DIR", synths)
    monkeypatch.setattr(utils, "SAMPLES_DIR", samples)

    assert utils.is_synth("Keys") is True
    assert utils.is_synth("Harp") is False
    with pytest.raises(ValueError, match="not found"):
        utils.is_synth("Unknown")

    (samples / "Keys").mkdir()
    with pytest.raises(ValueError, match="both"):
        utils.is_synth("Keys")


def test_yaml_helpers_round_trip_in_session_directory(
    monkeypatch, tmp_path, session_id
):
    monkeypatch.setattr(utils, "TMP_DIR", tmp_path)
    source = {"name": "Example", "map": [{"output": "time"}]}

    path = utils.write_YAML_file(source)

    assert path.parent == tmp_path / session_id
    assert utils.read_YAML_file(path) == source


def test_read_yaml_reports_invalid_yaml(tmp_path):
    path = tmp_path / "broken.yml"
    path.write_text("name: [")

    with pytest.raises(ValueError, match="Error reading YAML"):
        utils.read_YAML_file(path)


def test_write_sound_to_style_resolves_synth_and_sample(monkeypatch):
    resolved = []
    monkeypatch.setattr(utils, "resolve_file", lambda ref: resolved.append(ref) or ref)
    synth_style = {"generator": {"type": "synthesizer", "preset": "Keys"}}
    sample_style = {"generator": {"type": "sampler", "sample": "Harp"}}

    assert utils.write_sound_to_style(synth_style)["generator"]["preset"] == (
        "sound_assets:synths:Keys.yml"
    )
    assert utils.write_sound_to_style(sample_style)["generator"]["sample"] == (
        "sound_assets:samples:Harp"
    )
    assert resolved == [
        "sound_assets:synths:Keys.yml",
        "sound_assets:samples:Harp",
    ]


@pytest.mark.parametrize(
    ("times", "expected"),
    [
        ([0, 1, 2, 3], True),
        ([0, 1, 3, 4], False),
        ([0], False),
    ],
)
def test_is_time_series(times, expected):
    frame = pd.DataFrame({"time": times, "flux": range(len(times))})
    style = {"map": [{"input": "time", "output": "time"}]}

    assert utils.is_time_series(frame, style) is expected


def test_get_time_axis_uses_input_or_mapping_position():
    assert utils.get_time_axis(
        {"map": [{"output": "pitch"}, {"output": "time"}]}
    ) == 1
    assert utils.get_time_axis(
        {"map": [{"input": "seconds", "output": "time_evo"}]}
    ) == "seconds"


def test_update_style_rewrites_object_mappings(monkeypatch, tmp_path, session_id):
    source = tmp_path / "style.yml"
    source.write_text(
        yaml.safe_dump(
            {
                "sources": "objects",
                "generator": {},
                "map": [{"output": "time"}, {"output": "pitch"}],
            }
        )
    )
    monkeypatch.setattr(utils, "TMP_DIR", tmp_path)

    rewritten = utils.update_style(source)
    assert rewritten.parent == tmp_path / session_id
    changed = utils.read_YAML_file(rewritten)
    assert [mapping["output"] for mapping in changed["map"]] == [
        "time_evo",
        "pitch_shift",
    ]


def test_update_style_leaves_unchanged_style_at_original_path(tmp_path):
    source = tmp_path / "style.yml"
    source.write_text(
        yaml.safe_dump(
            {"sources": "events", "generator": {}, "map": [{"output": "volume"}]}
        )
    )

    assert utils.update_style(source) == source


@pytest.mark.parametrize(
    ("value", "expected"),
    [("2.5", True), ("-4", True), ("not a number", False)],
)
def test_is_number(value, expected):
    assert utils.is_number(value) is expected


def test_voice_chord_returns_four_voiced_notes_and_rejects_missing_fifth():
    assert utils.voice_chord("C") == ["C2", "G3", "E4", "C5"]
    with pytest.raises(ValueError, match="perfect fifth"):
        utils.voice_chord("Cdim")


def test_random_chord_returns_one_four_note_voicing(monkeypatch):
    monkeypatch.setattr(random, "choice", lambda values: values[0])

    chord = utils.random_chord()

    assert len(chord) == 1
    assert len(chord[0]) == 4
    assert [note[-1] for note in chord[0]] == ["2", "3", "4", "5"]


def test_cleanup_old_layers_keeps_current_wav_and_removes_stale_files(
    monkeypatch, tmp_path
):
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    for name in (
        "layer_1.wav",
        "layer_2.wav",
        "layer_3.mp3",
        "mapping_table_1.csv",
        "mapping_table_3.csv",
        "audio_figure.wav",
        "unrelated.csv",
    ):
        (session_dir / name).touch()
    monkeypatch.setattr(utils, "TMP_DIR", tmp_path)

    utils.cleanup_old_layers("session", 1)

    assert sorted(path.name for path in session_dir.iterdir()) == [
        "audio_figure.wav",
        "layer_1.wav",
        "mapping_table_1.csv",
        "unrelated.csv",
    ]


@pytest.mark.parametrize(
    ("user_agent", "expected"),
    [("Mozilla/5.0", False), ("FriendlyCrawler", True), ("BOT", True)],
)
def test_is_bot(user_agent, expected):
    assert utils.is_bot(user_agent) is expected
