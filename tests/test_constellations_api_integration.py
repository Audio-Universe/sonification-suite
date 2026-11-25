import base64

import pandas as pd

import constellations


def test_list_constellations_is_a_get_endpoint(api_client):
    response = api_client.get("/constellations/list/")
    wrong_method = api_client.post("/constellations/list/")

    assert response.status_code == 200
    result = response.json()
    assert set(result) == {"constellations", "asterisms"}
    assert isinstance(result["constellations"], list)
    assert isinstance(result["asterisms"], list)
    assert wrong_method.status_code == 405


def test_plot_constellation_csv_over_http(api_client, session_file):
    _, file_ref = session_file(
        "constellation.csv",
        "hip,stick_figure,ra_corrected,dec,magnitude,colour,proper\n"
        "1,false,10,20,1,0.2,Alpha\n"
        "2,false,11,21,2,1.0,Beta\n",
    )

    response = api_client.post(
        "/constellations/plot/",
        json={"file_ref": file_ref},
    )

    assert response.status_code == 200
    assert base64.b64decode(response.json()["image"]).lstrip().startswith(
        b"<?xml"
    )


def test_get_plotting_data_returns_star_and_line_payload(
    api_client, monkeypatch, session_file
):
    _, file_ref = session_file(
        "stars.csv",
        "hip,ra_corrected,dec,display_name\n"
        "1,10,20,Alpha\n"
        "2,11,21,Beta\n",
    )
    monkeypatch.setattr(
        constellations,
        "PATTERNS",
        {"Example": {"edges": [(1, 2), (2, 3)]}},
    )

    response = api_client.post(
        "/constellations/get-plotting-data/",
        json={"file_ref": file_ref},
    )

    assert response.status_code == 200
    assert response.json() == {
        "lines": [[1, 2]],
        "stars": [
            {"id": 1, "ra": 10.0, "dec": 20.0, "display_name": "Alpha"},
            {"id": 2, "ra": 11.0, "dec": 21.0, "display_name": "Beta"},
        ],
    }


def test_get_and_plot_imported_constellation_over_http(
    api_client, session_file
):
    _, file_ref = session_file(
        "stars.csv",
        "hip,ra_corrected,ra,dec,magnitude,colour,proper,display_name\n"
        "1,10,10,20,1,0.2,Alpha,Alpha\n"
        "2,11,11,21,2,1.0,Beta,Beta\n"
        "3,12,12,22,3,1.5,Gamma,Gamma\n",
    )

    response = api_client.post(
        "/constellations/get-and-plot/",
        json={
            "file_ref": file_ref,
            "stick_figure": False,
            "n_stars": 2,
        },
    )

    assert response.status_code == 200
    assert base64.b64decode(response.json()["image"]).lstrip().startswith(
        b"<?xml"
    )


def test_constellation_magnitude_and_count_endpoints_over_http(
    api_client, monkeypatch
):
    stars = pd.DataFrame({"magnitude": [1.0, 2.0, 3.0]})
    monkeypatch.setattr(
        constellations,
        "get_constellation",
        lambda *args, **kwargs: stars,
    )

    magnitude = api_client.post(
        "/constellations/get-max-magnitude/",
        json={"name": "Example", "n_stars": 2},
    )
    count = api_client.post(
        "/constellations/get-n-stars/",
        json={"name": "Example", "max_magnitude": 2.0},
    )

    assert magnitude.status_code == 200
    assert magnitude.json() == {"max_magnitude": 2.0}
    assert count.status_code == 200
    assert count.json() == {"n_stars": 2}


def test_save_refined_constellation_persists_custom_order_over_http(
    api_client, backend_storage, session_file
):
    _, file_ref = session_file(
        "stars.csv",
        "hip,ra,dec,magnitude\n"
        "11,23,10,1\n"
        "22,1,14,2\n",
    )

    response = api_client.post(
        "/constellations/save-refined/",
        json={
            "file_ref": file_ref,
            "stick_figure": True,
            "order": [22, 11],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "file_ref": "session:constellations.csv",
        "ra": 0.0,
        "dec": 12.0,
    }
    session_id = api_client.cookies.get("session_id")
    saved = pd.read_csv(
        backend_storage.tmp_dir / session_id / "constellations.csv"
    )
    assert saved["custom_order"].tolist() == [2, 1]
    assert saved["stick_figure"].tolist() == [True, True]


def test_constellation_endpoints_report_validation_and_file_errors(
    api_client
):
    invalid_body = api_client.post("/constellations/get-n-stars/", json={})
    missing_file = api_client.post(
        "/constellations/plot/",
        json={"file_ref": "session:missing.csv"},
    )

    assert invalid_body.status_code == 422
    assert missing_file.status_code == 400
