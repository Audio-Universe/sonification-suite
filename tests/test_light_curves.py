import asyncio
import base64
import threading
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException

import light_curves
from request_models import DataRequest, DownloadRequest, RefineRequest, StarQuery


def test_sort_key_orders_missions_and_pipeline_priority():
    rows = [
        {"mission": "unknown", "year": 2025, "exposure": 100, "pipeline": "x"},
        {"mission": "K2", "year": 2020, "exposure": 120, "pipeline": "x"},
        {"mission": "TESS", "year": 2024, "exposure": 60, "pipeline": "QLP"},
        {"mission": "TESS", "year": 2023, "exposure": 20, "pipeline": "SPOC"},
        {"mission": "Kepler", "year": 2018, "exposure": 30, "pipeline": "x"},
    ]

    ordered = sorted(rows, key=light_curves.sort_key)

    assert [row["mission"] for row in ordered] == [
        "Kepler",
        "TESS",
        "TESS",
        "K2",
        "unknown",
    ]
    assert [row["pipeline"] for row in ordered[1:3]] == ["SPOC", "QLP"]


def test_run_lightkurve_search_uses_author_mapping_and_sorts(monkeypatch):
    seen = []

    class SearchResult:
        table = [
            {
                "project": "TESS",
                "exptime": 120,
                "author": "SPOC",
                "year": 2022,
                "mission": "TESS",
                "dataURI": "mast:TESS",
            }
        ]

    monkeypatch.setattr(
        light_curves.lk,
        "search_lightcurve",
        lambda ident, author: seen.append((ident, author)) or SearchResult(),
    )

    result = light_curves.run_lightkurve_search(
        ["TIC 1"], {"TIC": ("SPOC",)}, threading.Event()
    )

    assert seen == [("TIC 1", ("SPOC",))]
    assert result[0]["dataURI"] == "mast:TESS"


def test_run_lightkurve_search_observes_cancellation():
    cancel = threading.Event()
    cancel.set()

    assert light_curves.run_lightkurve_search(["TIC 1"], {}, cancel) is None


def test_get_identifiers_filters_simbad_results(monkeypatch):
    class IdTable:
        def __getitem__(self, key):
            assert key == "id"
            return SimpleNamespace(tolist=lambda: ["TIC 1", "KIC 2", "HD 3"])

    monkeypatch.setattr(
        light_curves.Simbad,
        "query_object",
        lambda name: {"ra": [12.5], "dec": [-4.0]},
    )
    monkeypatch.setattr(
        light_curves.Simbad, "query_objectids", lambda name: IdTable()
    )
    query = StarQuery(
        star_name="Example",
        filters={"mission": {"TESS": True, "Kepler": False, "K2": False}},
    )

    assert light_curves.get_identifiers(query) == (["TIC 1"], 12.5, -4.0)


def test_download_lightcurve_trims_nan_edges_and_writes_csv(
    monkeypatch, tmp_path, session_id
):
    (tmp_path / session_id).mkdir()
    monkeypatch.setattr(light_curves, "TMP_DIR", tmp_path)
    monkeypatch.setattr(
        light_curves.lk,
        "read",
        lambda url: SimpleNamespace(
            time=SimpleNamespace(value=np.array([0, 1, 2, 3])),
            flux=SimpleNamespace(value=np.array([np.nan, 2.0, 3.0, np.nan])),
        ),
    )

    path = light_curves.download_lightcurve("mast:example")

    assert path == tmp_path / session_id / "light_curves.csv"
    result = pd.read_csv(path)
    assert result["time"].tolist() == [1.0, 2.0]
    assert result["flux"].tolist() == [2.0, 3.0]


def test_plot_and_format_lc_returns_svg_for_frame_and_csv(tmp_path):
    frame = pd.DataFrame({"time": [0, 1, 2], "flux": [2, 4, 3]})
    path = tmp_path / "lightcurve.csv"
    frame.to_csv(path, index=False)

    for source in (frame, str(path)):
        image = light_curves.plot_and_format_lc(source)
        assert base64.b64decode(image).lstrip().startswith(b"<?xml")


def test_search_lightcurves_returns_results_and_coordinates(monkeypatch):
    monkeypatch.setattr(
        light_curves, "get_identifiers", lambda query: (["TIC 1"], 10.0, 20.0)
    )
    monkeypatch.setattr(
        light_curves,
        "run_lightkurve_search",
        lambda idents, authors, cancel: [{"dataURI": "mast:example"}],
    )
    query = StarQuery(
        star_name="Example",
        filters={"mission": {"TESS": True, "Kepler": False, "K2": False}},
    )

    result = asyncio.run(
        light_curves.search_lightcurves(query, SimpleNamespace())
    )

    assert result == {
        "results": [{"dataURI": "mast:example"}],
        "ra": 10.0,
        "dec": 20.0,
    }


def test_search_lightcurves_reports_no_matching_identifiers(monkeypatch):
    monkeypatch.setattr(
        light_curves, "get_identifiers", lambda query: ([], None, None)
    )
    query = StarQuery(
        star_name="Unknown",
        filters={"mission": {"TESS": True, "Kepler": False, "K2": False}},
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(light_curves.search_lightcurves(query, SimpleNamespace()))

    assert exc_info.value.status_code == 400
    assert "No TESS light curves found" in exc_info.value.detail


def test_get_range_returns_time_range_and_nan_flag(monkeypatch, tmp_path):
    path = tmp_path / "data.csv"
    pd.DataFrame({"time": [1.5, 3.5], "flux": [1.0, np.nan]}).to_csv(
        path, index=False
    )
    monkeypatch.setattr(light_curves, "resolve_file", lambda ref: path)

    assert light_curves.get_range(DataRequest(file_ref="session:data.csv")) == {
        "range": [1.5, 3.5],
        "has_nans": True,
    }


@pytest.mark.parametrize(
    ("strategy", "expected"),
    [
        ("fill", [1.0, 2.0, 3.0]),
        ("interpolate", [1.0, 2.0, 3.0]),
        ("silence", [1.0, np.nan, 3.0]),
    ],
)
def test_refine_light_curve_applies_range_and_nan_strategy(
    monkeypatch, tmp_path, strategy, expected
):
    path = tmp_path / "data.csv"
    pd.DataFrame(
        {"time": [0, 1, 2, 3], "flux": [0.0, 1.0, np.nan, 3.0]}
    ).to_csv(path, index=False)
    monkeypatch.setattr(light_curves, "resolve_file", lambda ref: path)
    request = RefineRequest(
        file_ref="session:data.csv",
        new_range=[1, 3],
        sigma=0,
        nan_strategy=strategy,
        fill_with="median",
    )

    result, had_nans = light_curves.refine_light_curve(request)

    assert had_nans is True
    assert result["time"].tolist() == [1, 2, 3]
    if strategy == "silence":
        assert result["flux"].iloc[0] == 1
        assert pd.isna(result["flux"].iloc[1])
        assert result["flux"].iloc[2] == 3
    else:
        assert result["flux"].tolist() == pytest.approx(expected)


def test_preview_and_save_refined_use_refined_data(monkeypatch, tmp_path, session_id):
    (tmp_path / session_id).mkdir()
    source = tmp_path / "data.csv"
    pd.DataFrame({"time": [0, 1], "flux": [1.0, 2.0]}).to_csv(
        source, index=False
    )
    monkeypatch.setattr(light_curves, "TMP_DIR", tmp_path)
    monkeypatch.setattr(light_curves, "resolve_file", lambda ref: source)
    request = RefineRequest(
        file_ref="session:data.csv",
        new_range=[0, 1],
        sigma=0,
        nan_strategy="silence",
        fill_with="mean",
    )

    preview = light_curves.preview_refined(request)
    saved = light_curves.save_refined(request)

    assert base64.b64decode(preview["image"]).lstrip().startswith(b"<?xml")
    assert preview["nans_after_trim"] is False
    assert saved == {"file_ref": "session:light_curves_refined.csv"}
    assert pd.read_csv(tmp_path / session_id / "light_curves_refined.csv")[
        "flux"
    ].tolist() == [1.0, 2.0]


def test_select_lightcurve_wraps_downloaded_path(monkeypatch, tmp_path):
    path = tmp_path / "light_curves.csv"
    monkeypatch.setattr(light_curves, "download_lightcurve", lambda uri: path)

    assert light_curves.select_lightcurve(
        DownloadRequest(data_uri="mast:example")
    ) == {"file_ref": "session:light_curves.csv"}


def test_plot_lightcurve_uses_local_file(monkeypatch, tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("time,flux\n0,1\n1,2\n")
    monkeypatch.setattr(light_curves, "resolve_file", lambda ref: path)
    monkeypatch.setattr(light_curves, "plot_and_format_lc", lambda file: "image")

    assert light_curves.plot_lightcurve(
        DataRequest(file_ref="session:data.csv")
    ) == {"image": "image"}
