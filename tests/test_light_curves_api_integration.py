import base64

import pandas as pd

import light_curves


def test_search_lightcurves_returns_search_results_over_http(
    api_client, monkeypatch
):
    monkeypatch.setattr(
        light_curves,
        "get_identifiers",
        lambda query: (["TIC 123"], 12.5, -4.0),
    )
    monkeypatch.setattr(
        light_curves,
        "run_lightkurve_search",
        lambda idents, authors, cancel: [
            {
                "mission": "TESS",
                "pipeline": "SPOC",
                "dataURI": "mast:TESS/example",
            }
        ],
    )

    response = api_client.post(
        "/light-curves/search-lightcurves/",
        json={
            "star_name": "Example Star",
            "filters": {
                "mission": {"TESS": True, "Kepler": False, "K2": False}
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {
                "mission": "TESS",
                "pipeline": "SPOC",
                "dataURI": "mast:TESS/example",
            }
        ],
        "ra": 12.5,
        "dec": -4.0,
    }


def test_search_lightcurves_returns_http_400_when_no_ids_match(
    api_client, monkeypatch
):
    monkeypatch.setattr(
        light_curves, "get_identifiers", lambda query: ([], None, None)
    )

    response = api_client.post(
        "/light-curves/search-lightcurves/",
        json={
            "star_name": "Unknown",
            "filters": {
                "mission": {"TESS": True, "Kepler": False, "K2": False}
            },
        },
    )

    assert response.status_code == 400
    assert "No TESS light curves found" in response.json()["detail"]


def test_search_lightcurves_validates_request_body(api_client):
    response = api_client.post(
        "/light-curves/search-lightcurves/",
        json={"star_name": "Example"},
    )

    assert response.status_code == 422


def test_select_plot_and_range_flow_uses_session_data(
    api_client, backend_storage, monkeypatch
):
    session_id = api_client.get("/core/session/").json()["session_id"]

    def fake_download(data_uri):
        path = backend_storage.tmp_dir / session_id / "light_curves.csv"
        pd.DataFrame(
            {"time": [0.0, 1.0, 2.0], "flux": [1.0, 2.0, 3.0]}
        ).to_csv(path, index=False)
        return path

    monkeypatch.setattr(light_curves, "download_lightcurve", fake_download)

    selected = api_client.post(
        "/light-curves/select-lightcurve/",
        json={"data_uri": "mast:TESS/example"},
    )

    assert selected.status_code == 200
    assert selected.json() == {"file_ref": "session:light_curves.csv"}

    plotted = api_client.post(
        "/light-curves/plot/",
        json={"file_ref": selected.json()["file_ref"]},
    )
    assert plotted.status_code == 200
    assert base64.b64decode(plotted.json()["image"]).lstrip().startswith(
        b"<?xml"
    )

    data_range = api_client.post(
        "/light-curves/get-range-and-nans/",
        json={"file_ref": selected.json()["file_ref"]},
    )
    assert data_range.status_code == 200
    assert data_range.json() == {
        "range": [0.0, 2.0],
        "has_nans": False,
    }


def test_refine_preview_and_save_are_exposed_over_http(
    api_client, backend_storage, session_file
):
    session_id, file_ref = session_file(
        "light_curves.csv",
        b"time,flux\n0,1.0\n1,\n2,3.0\n",
    )
    request = {
        "file_ref": file_ref,
        "new_range": [0, 2],
        "sigma": 0,
        "nan_strategy": "interpolate",
        "fill_with": "mean",
    }

    preview = api_client.post(
        "/light-curves/preview-refined/", json=request
    )

    assert preview.status_code == 200
    assert base64.b64decode(preview.json()["image"]).lstrip().startswith(
        b"<?xml"
    )
    assert preview.json()["nans_after_trim"] is True

    saved = api_client.post("/light-curves/save-refined/", json=request)

    assert saved.status_code == 200
    assert saved.json() == {"file_ref": "session:light_curves_refined.csv"}
    refined = pd.read_csv(
        backend_storage.tmp_dir / session_id / "light_curves_refined.csv"
    )
    assert refined["flux"].tolist() == [1.0, 2.0, 3.0]


def test_light_curve_routes_report_http_method_and_reference_errors(
    api_client
):
    assert api_client.get("/light-curves/plot/").status_code == 405

    response = api_client.post(
        "/light-curves/plot/",
        json={"file_ref": "session:missing.csv"},
    )
    assert response.status_code == 400
