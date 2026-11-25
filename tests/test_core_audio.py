import base64
import math
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi import BackgroundTasks, HTTPException
from pydub import AudioSegment
from pydub.generators import Sine
from scipy.io import wavfile

import core
from request_models import (
    DataRequest,
    LayerRequest,
    SonificationRequest,
    VolumeRequest,
)


def test_generate_sonification_rejects_long_duration():
    request = SonificationRequest(
        soni_type="light_curves",
        layers=[{"data_ref": "data", "style_ref": "style"}],
        duration=core.MAX_DURATION + 1,
        system="stereo",
        data_name="example",
        observer=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        core.generate_sonification(request, SimpleNamespace())
    assert exc_info.value.status_code == 400


def test_generate_sonification_requires_session_cookie(session_id):
    token = core.session_id_var.set("")
    try:
        request = SonificationRequest(
            soni_type="light_curves",
            layers=[{"data_ref": "data", "style_ref": "style"}],
            duration=5,
            system="stereo",
            data_name="example",
            observer=None,
        )
        with pytest.raises(HTTPException) as exc_info:
            core.generate_sonification(request, SimpleNamespace())
        assert exc_info.value.status_code == 400
    finally:
        core.session_id_var.reset(token)


def test_generate_sonification_builds_session_audio(
    monkeypatch, tmp_path, session_id
):
    session_dir = tmp_path / session_id
    session_dir.mkdir()
    data_path = tmp_path / "data.csv"
    data_path.write_text("time,flux\n0,1\n1,2\n")
    style_path = tmp_path / "style.yml"
    style_path.write_text("style")
    calls = {}

    class FakeFigure:
        def __init__(self, system):
            calls["system"] = system

        def sonify(self, frame, **kwargs):
            calls["kwargs"] = kwargs
            return SimpleNamespace()

        def set_level(self, **kwargs):
            calls["level"] = kwargs

        def save(self, path, master_volume):
            calls["master_volume"] = master_volume
            path.write_bytes(b"audio")

    monkeypatch.setattr(core, "TMP_DIR", tmp_path)
    monkeypatch.setattr(
        core,
        "resolve_file",
        lambda ref: data_path if ref == "data" else style_path,
    )
    monkeypatch.setattr(core, "AudioFigure", FakeFigure)
    monkeypatch.setattr(
        core, "preprocess_style", lambda path, frame, request: {"style": "value"}
    )
    monkeypatch.setattr(core, "write_YAML_file", lambda style: tmp_path / "preprocessed.yml")
    monkeypatch.setattr(core, "get_source_names", lambda frame, kind, layer: None)
    monkeypatch.setattr(core, "write_mapping_table", lambda *args: None)
    monkeypatch.setattr(core, "log_event", lambda **kwargs: None)
    monkeypatch.setattr(core, "cleanup_old_layers", lambda *args: None)
    request = SonificationRequest(
        soni_type="light_curves",
        layers=[
            LayerRequest(data_ref="data", style_ref="style", volume=0.6)
        ],
        duration=5,
        system="stereo",
        data_name="example",
        observer=None,
    )

    result = core.generate_sonification(
        request, SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
    )

    assert result == {"file_ref": "session:audio_figure.wav", "alt_az": None}
    assert (session_dir / "audio_figure.wav").read_bytes() == b"audio"
    assert calls["system"] == "stereo"
    assert calls["level"] == {"name": "sonification_1", "level": 0.6}
    assert calls["master_volume"] == 0.6


def test_generate_sonification_rejects_non_csv_layer(
    monkeypatch, tmp_path, session_id
):
    session_dir = tmp_path / session_id
    session_dir.mkdir()
    bad_file = tmp_path / "data.json"
    bad_file.write_text("{}")
    monkeypatch.setattr(core, "TMP_DIR", tmp_path)
    monkeypatch.setattr(core, "resolve_file", lambda ref: bad_file)
    request = SonificationRequest(
        soni_type="light_curves",
        layers=[{"data_ref": "data", "style_ref": "style"}],
        duration=5,
        system="stereo",
        data_name="example",
        observer=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        core.generate_sonification(
            request, SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
        )

    assert exc_info.value.status_code == 500


def test_generate_spectrogram_returns_png(monkeypatch, tmp_path):
    path = tmp_path / "audio.wav"
    sample_rate = 44100
    samples = (
        np.sin(2 * np.pi * 440 * np.arange(8192) / sample_rate)
        * np.iinfo(np.int32).max
    ).astype(np.int32)
    wavfile.write(path, sample_rate, np.column_stack((samples, samples)))
    monkeypatch.setattr(core, "resolve_file", lambda ref: path)

    result = core.generate_spectrogram(DataRequest(file_ref="session:audio.wav"))

    assert base64.b64decode(result["image"]).startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize(
    ("audio_format", "volume", "detail"),
    [
        ("ogg", 1.0, "Audio format must be 'wav' or 'mp3'"),
        ("wav", -0.1, "Volume must be between 0 and 1"),
        ("wav", 1.1, "Volume must be between 0 and 1"),
    ],
)
def test_get_audio_rejects_invalid_format_or_volume(
    audio_format, volume, detail
):
    with pytest.raises(HTTPException) as exc_info:
        core.get_audio(
            SimpleNamespace(),
            BackgroundTasks(),
            "session:audio.wav",
            "audio",
            audio_format=audio_format,
            volume=volume,
        )
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == detail


def test_get_audio_returns_wav_response_without_transcoding(
    monkeypatch, tmp_path
):
    path = tmp_path / "audio.wav"
    path.write_bytes(b"wav")
    monkeypatch.setattr(core, "resolve_file", lambda ref: path)

    response = core.get_audio(
        SimpleNamespace(),
        BackgroundTasks(),
        "session:audio.wav",
        "download-name",
    )

    assert response.path == str(path)
    assert response.media_type == "audio/wav"
    assert "download-name.wav" in response.headers["content-disposition"]


def test_apply_volume_outputs_silence_at_zero_and_rejects_bad_values(tmp_path):
    source = tmp_path / "source.wav"
    output = tmp_path / "silent.wav"
    Sine(440).to_audio_segment(duration=250).export(source, format="wav")

    core.apply_volume(str(source), 0, str(output))

    result = AudioSegment.from_wav(output)
    assert len(result) == 250
    assert result.max_dBFS == float("-inf")
    with pytest.raises(ValueError, match="between 0 and 1"):
        core.apply_volume(str(source), 1.1, str(output))


def test_mix_layer_volumes_returns_original_for_unmodified_levels():
    assert core.mix_layer_volumes(VolumeRequest(volumes=[1, 1])) == {
        "file_ref": "session:audio_figure.wav"
    }


def test_mix_layer_volumes_writes_adjusted_single_layer(
    monkeypatch, tmp_path, session_id
):
    session_dir = tmp_path / session_id
    session_dir.mkdir()
    Sine(440).to_audio_segment(duration=200).export(
        session_dir / "audio_figure.wav", format="wav"
    )
    monkeypatch.setattr(core, "TMP_DIR", tmp_path)

    result = core.mix_layer_volumes(VolumeRequest(volumes=[0.5]))

    assert result == {"file_ref": "session:audio_figure_mixed.wav"}
    mixed = AudioSegment.from_wav(session_dir / "audio_figure_mixed.wav")
    assert len(mixed) == 200
    assert mixed.dBFS == pytest.approx(Sine(440).to_audio_segment(duration=200).dBFS + 20 * math.log10(0.5), abs=1.0)


def test_mix_layer_volumes_skips_muted_layers(monkeypatch, tmp_path, session_id):
    session_dir = tmp_path / session_id
    session_dir.mkdir()
    for name in ("audio_figure.wav", "layer_1.wav", "layer_2.wav"):
        Sine(440).to_audio_segment(duration=200).export(
            session_dir / name, format="wav"
        )
    monkeypatch.setattr(core, "TMP_DIR", tmp_path)

    result = core.mix_layer_volumes(VolumeRequest(volumes=[0.5, 0]))

    assert result == {"file_ref": "session:audio_figure_mixed.wav"}
    mixed = AudioSegment.from_wav(session_dir / "audio_figure_mixed.wav")
    assert len(mixed) == 200


def test_convert_to_mp3_validates_file_before_conversion(tmp_path):
    with pytest.raises(FileNotFoundError):
        core.convert_to_mp3(str(tmp_path / "missing.wav"))

    non_wav = tmp_path / "audio.txt"
    non_wav.touch()
    with pytest.raises(ValueError, match="Expected a .wav"):
        core.convert_to_mp3(str(non_wav))


def test_convert_to_mp3_reports_missing_ffmpeg(monkeypatch, tmp_path):
    wav = tmp_path / "audio.wav"
    wav.touch()
    monkeypatch.setattr(core.shutil, "which", lambda name: None)
    monkeypatch.setattr(core.Path, "exists", lambda path: path == wav)

    with pytest.raises(RuntimeError, match="FFmpeg is not installed"):
        core.convert_to_mp3(str(wav))


def test_get_uploads_dir_size_counts_nested_files(tmp_path):
    uploads = tmp_path / "uploads"
    (uploads / "nested").mkdir(parents=True)
    (uploads / "a.csv").write_bytes(b"abc")
    (uploads / "nested" / "b.csv").write_bytes(b"12345")

    assert core.get_uploads_dir_size(str(uploads)) == 8


def test_download_file_sets_cache_control_and_download_name(
    monkeypatch, tmp_path
):
    source = tmp_path / "table.csv"
    source.write_text("x\n1\n")
    monkeypatch.setattr(core, "resolve_file", lambda ref: source)

    response = core.download_file("session:table.csv", name="custom.csv")

    assert response.path == str(source)
    assert response.headers["Cache-Control"] == "no-store, max-age=0"
    assert "custom.csv" in response.headers["content-disposition"]
