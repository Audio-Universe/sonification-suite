import base64
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException

from request_models import DataRequest, MagRequest, NightSkyRequest
import night_sky


@pytest.fixture
def night_sky_module():
    return night_sky


def test_handle_observer_computes_spatial_values(night_sky_module, monkeypatch):
    module = night_sky_module

    class Position:
        def observe(self, star):
            return SimpleNamespace(
                apparent=lambda: SimpleNamespace(
                    altaz=lambda: (
                        SimpleNamespace(degrees=20.0),
                        SimpleNamespace(degrees=40.0),
                        None,
                    )
                )
            )

    monkeypatch.setattr(module, "position_observer", lambda *args: Position())

    result = module.handle_observer(
        {
            "latitude": "1",
            "longitude": "2",
            "ra": 30,
            "dec": 10,
            "date_time": "2025-01-01 00:00:00",
            "orientation": "N",
        }
    )

    assert result["STRAUSS_inputs"]["azimuth"] == 320.0
    assert result["STRAUSS_inputs"]["polar"] == 70.0
    assert result["STRAUSS_inputs"]["pan"] == pytest.approx(
        (1 - np.sin(np.radians(320))) / 2
    )
    assert result["display_values"] == {"azimuth": 40.0, "altitude": 20.0}


def test_position_observer_uses_timezone_and_ephemeris(
    night_sky_module, monkeypatch
):
    module = night_sky_module
    observed = {}

    class Earth:
        def __add__(self, location):
            return location

    class Location:
        def at(self, time):
            observed["time"] = time
            return "observer-position"

    class Timescale:
        def from_datetime(self, value):
            observed["datetime"] = value
            return "skyfield-time"

    monkeypatch.setattr(module, "EARTH", Earth())
    monkeypatch.setattr(module, "TF", SimpleNamespace(timezone_at=lambda **kw: "UTC"))
    monkeypatch.setattr(module.load, "timescale", lambda: Timescale())
    monkeypatch.setattr(module.wgs84, "latlon", lambda lat, lon: Location())

    result = module.position_observer(12, -30, "2025-02-03 04:05:06")

    assert result == "observer-position"
    assert observed["time"] == "skyfield-time"
    assert str(observed["datetime"]) == "2025-02-03 04:05:06+00:00"


def test_get_star_data_filters_below_horizon_and_saves_csv(
    night_sky_module, monkeypatch, tmp_path, session_id
):
    module = night_sky_module
    (tmp_path / session_id).mkdir()
    monkeypatch.setattr(module, "TMP_DIR", tmp_path)
    monkeypatch.setattr(module, "position_observer", lambda *args: object())

    class FakeStar:
        @staticmethod
        def from_dataframe(frame):
            return "stars"

    class Position:
        def observe(self, stars):
            return SimpleNamespace(
                apparent=lambda: SimpleNamespace(
                    altaz=lambda: (
                        SimpleNamespace(degrees=np.array([30.0])),
                        SimpleNamespace(
                            radians=np.array([np.pi / 4])
                        ),
                        None,
                    )
                )
            )

    monkeypatch.setattr(module, "Star", FakeStar)
    monkeypatch.setattr(module, "position_observer", lambda *args: Position())
    request = NightSkyRequest(
        latitude=0,
        longitude=0,
        facing="N",
        date_time="2025-01-01 00:00:00",
    )

    result = module.get_star_data(request)

    assert result == {"file_ref": "session:night_sky.csv"}
    stars = pd.read_csv(tmp_path / session_id / "night_sky.csv")
    assert stars["hip"].tolist() == [1]
    assert stars["zenith_angle"].tolist() == [60.0]
    assert stars["relative_azimuth"].tolist() == [pytest.approx(315.0)]


def test_refine_stars_filters_by_strict_magnitude_limit(
    night_sky_module, monkeypatch, tmp_path, session_id
):
    module = night_sky_module
    (tmp_path / session_id).mkdir()
    source = tmp_path / "source.csv"
    pd.DataFrame({"magnitude": [1.0, 2.0, 3.0]}).to_csv(source, index=False)
    monkeypatch.setattr(module, "TMP_DIR", tmp_path)
    monkeypatch.setattr(module, "resolve_file", lambda ref: source)

    result = module.refine_stars(
        MagRequest(file_ref="session:night_sky.csv", maglim=2.0)
    )

    assert result == {"file_ref": "session:night_sky_refined.csv"}
    assert pd.read_csv(tmp_path / session_id / "night_sky_refined.csv")[
        "magnitude"
    ].tolist() == [1.0]


def test_plot_and_format_stars_returns_svg_and_rejects_empty(
    night_sky_module,
):
    frame = pd.DataFrame(
        {
            "azimuth_rad": [0.5, 1.0],
            "altitude_deg": [20.0, 60.0],
            "magnitude": [1.0, 2.0],
            "colour": [0.2, 1.0],
            "direction_offset": [0.0, 0.0],
        }
    )

    image = night_sky_module.plot_and_format_stars(frame)

    assert base64.b64decode(image).lstrip().startswith(b"<?xml")
    with pytest.raises(ValueError, match="No stars"):
        night_sky_module.plot_and_format_stars(frame.iloc[:0])


def test_plot_star_data_rejects_non_csv_reference(night_sky_module, monkeypatch):
    monkeypatch.setattr(
        night_sky_module, "resolve_file", lambda ref: Path("stars.txt")
    )

    with pytest.raises(HTTPException) as exc_info:
        night_sky_module.plot_star_data(
            DataRequest(file_ref="session:stars.txt")
        )
    assert exc_info.value.status_code == 400
