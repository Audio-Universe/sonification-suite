import pandas as pd


def test_data_composer_get_columns_over_http(api_client, session_file):
    _, file_ref = session_file(
        "data.csv",
        b"time,flux,label\n0,1.0,a\n1,,a\n2,3.0,b\n",
    )

    response = api_client.post(
        "/data-composer/get-columns/", json={"file_ref": file_ref}
    )

    assert response.status_code == 200
    assert response.json() == {
        "columns": [
            {"name": "time", "NaNs": 0, "unique": True},
            {"name": "flux", "NaNs": 1, "unique": True},
            {"name": "label", "NaNs": 0, "unique": False},
        ],
        "total_rows": 3,
    }


def test_data_composer_set_header_over_http(api_client, session_file):
    _, file_ref = session_file("raw.csv", b"1,2\n3,\n")

    response = api_client.post(
        "/data-composer/set-header/",
        json={"file_ref": file_ref, "has_header": False},
    )

    assert response.status_code == 200
    assert response.json() == {"invalid_columns": ["Column 2"]}

    columns = api_client.post(
        "/data-composer/get-columns/", json={"file_ref": file_ref}
    )
    assert [item["name"] for item in columns.json()["columns"]] == [
        "Column 1",
        "Column 2",
    ]


def test_data_composer_preview_refined_returns_json_safe_rows(
    api_client, session_file
):
    _, file_ref = session_file(
        "data.csv",
        b"time,flux,label\n0,1.0,a\n1,,a\n2,3.0,b\n",
    )

    response = api_client.post(
        "/data-composer/preview-refined/",
        json={
            "file_ref": file_ref,
            "columns": ["time", "flux", "label"],
            "nan_strategy": "interpolate",
            "fill_with": None,
            "row_range": [0, 3],
            "n_preview_rows": 2,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "rows": [
            {"time": 0.0, "flux": 1.0, "label": "a"},
            {"time": 1.0, "flux": 2.0, "label": "a"},
        ]
    }


def test_data_composer_save_refined_writes_session_upload(
    api_client, backend_storage, session_file
):
    _, file_ref = session_file(
        "data.csv",
        b"time,flux\n0,1.0\n1,\n2,3.0\n",
        uploads=True,
    )
    request = {
        "file_ref": file_ref,
        "columns": ["time", "flux"],
        "nan_strategy": "fill",
        "fill_with": "mean",
        "row_range": [0, 3],
        "n_preview_rows": 20,
    }

    response = api_client.post("/data-composer/save-refined/", json=request)

    assert response.status_code == 200
    saved_ref = response.json()["file_ref"]
    assert saved_ref.startswith("session:uploads:")
    session_id = api_client.cookies.get("session_id")
    saved_path = (
        backend_storage.tmp_dir
        / session_id
        / "uploads"
        / saved_ref.split(":")[-1]
    )
    saved = pd.read_csv(saved_path)
    assert saved["flux"].tolist() == [1.0, 2.0, 3.0]


def test_data_composer_validate_layer_reports_data_style_mismatches(
    api_client, session_file
):
    _, data_ref = session_file(
        "data.csv", b"label,flux\na,1\nb,2\n"
    )
    _, style_ref = session_file(
        "style.yml",
        "map:\n"
        "  - output: time\n"
        "  - input: missing_column\n"
        "    output: pitch\n"
        "  - output: volume\n",
    )

    response = api_client.post(
        "/data-composer/validate-layer/",
        json={"data_ref": data_ref, "style_ref": style_ref},
    )

    assert response.status_code == 200
    assert response.json() == {
        "missing_columns": ["missing_column"],
        "non_numeric_columns": ["label"],
        "insufficient_columns": {"style": 3, "data": 2},
    }


def test_data_composer_request_validation_and_method_errors(api_client):
    missing_request_field = api_client.post(
        "/data-composer/get-columns/", json={}
    )
    wrong_method = api_client.get("/data-composer/get-columns/")

    assert missing_request_field.status_code == 422
    assert wrong_method.status_code == 405
