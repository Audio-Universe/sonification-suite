import base64
from types import SimpleNamespace

import numpy as np
import pandas as pd

import night_sky


def test_get_refine_and_plot_night_sky_flow(
    api_client, backend_storage, monkeypatch
):
    session_response = api_client.get("/core/session/")
    session_id = session_response.json()["session_id"]

    class FakeStar:
        @staticmethod
        def from_dataframe(frame):
            return "catalogue-stars"

    class FakePosition:
        def observe(self, stars):
            return SimpleNamespace(
                apparent=lambda: SimpleNamespace(
                    altaz=lambda: (
                        SimpleNamespace(degrees=np.array([35.0])),
                        SimpleNamespace(radians=np.array([0.75])),
                        None,
                    )
                )
            )

    monkeypatch.setattr(night_sky, "Star", FakeStar)
    monkeypatch.setattr(
        night_sky, "position_observer", lambda *args: FakePosition()
    )

    generated = api_client.post(
        "/night-sky/get-stars/",
        json={
            "latitude": 51.5,
            "longitude": -0.1,
            "facing": "N",
            "date_time": "2025-01-01 22:00:00",
        },
    )

    assert generated.status_code == 200
    assert generated.json() == {"file_ref": "session:night_sky.csv"}
    generated_data = pd.read_csv(
        backend_storage.tmp_dir / session_id / "night_sky.csv"
    )
    assert generated_data["hip"].tolist() == [1]
    assert generated_data["zenith_angle"].tolist() == [55.0]

    refined = api_client.post(
        "/night-sky/refine-stars/",
        json={"file_ref": generated.json()["file_ref"], "maglim": 2.0},
    )
    assert refined.status_code == 200
    assert refined.json() == {"file_ref": "session:night_sky_refined.csv"}

    plotted = api_client.post(
        "/night-sky/plot/",
        json={"file_ref": refined.json()["file_ref"]},
    )
    assert plotted.status_code == 200
    assert base64.b64decode(plotted.json()["image"]).lstrip().startswith(
        b"<?xml"
    )


def test_night_sky_request_validation_and_method_errors(api_client):
    invalid_body = api_client.post("/night-sky/get-stars/", json={})
    wrong_method = api_client.get("/night-sky/get-stars/")

    assert invalid_body.status_code == 422
    assert wrong_method.status_code == 405


def test_night_sky_plot_rejects_non_csv_file(api_client, session_file):
    _, file_ref = session_file("stars.txt", b"not csv")

    response = api_client.post(
        "/night-sky/plot/", json={"file_ref": file_ref}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Data file type must be .csv"
