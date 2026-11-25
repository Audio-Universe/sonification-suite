import pandas as pd
import pytest

import data_composer
from request_models import (
    ComposerRefineRequest,
    DataRequest,
    HeaderRequest,
    LayerRequest,
)


@pytest.fixture
def composer_csv(monkeypatch, tmp_path):
    path = tmp_path / "data.csv"
    pd.DataFrame(
        {
            "time": [0.0, 1.0, 2.0, 3.0],
            "flux": [1.0, None, 3.0, 4.0],
            "label": ["a", "b", "b", "c"],
        }
    ).to_csv(path, index=False)
    monkeypatch.setattr(data_composer, "resolve_file", lambda ref: path)
    return path


def make_refine_request(strategy="interpolate", fill_with=None, **overrides):
    values = {
        "file_ref": "session:data.csv",
        "columns": ["time", "flux", "label"],
        "nan_strategy": strategy,
        "fill_with": fill_with,
        "row_range": [0, 4],
        "n_preview_rows": 2,
    }
    values.update(overrides)
    return ComposerRefineRequest(**values)


def test_get_columns_reports_missing_values_and_unique_values(composer_csv):
    result = data_composer.get_columns(DataRequest(file_ref="session:data.csv"))

    assert result["total_rows"] == 4
    assert result["columns"] == [
        {"name": "time", "NaNs": 0, "unique": True},
        {"name": "flux", "NaNs": 1, "unique": True},
        {"name": "label", "NaNs": 0, "unique": False},
    ]


def test_set_header_assigns_generic_names_and_reports_incomplete_columns(
    monkeypatch, tmp_path
):
    path = tmp_path / "no-header.csv"
    path.write_text("1,2\n3,\n")
    monkeypatch.setattr(data_composer, "resolve_file", lambda ref: path)

    result = data_composer.set_header(
        HeaderRequest(file_ref="session:no-header.csv", has_header=False)
    )

    assert result == {"invalid_columns": ["Column 2"]}
    assert pd.read_csv(path).columns.tolist() == ["Column 1", "Column 2"]


@pytest.mark.parametrize(
    ("strategy", "fill_with", "expected"),
    [
        ("fill", "mean", [1.0, 8 / 3, 3.0, 4.0]),
        ("interpolate", None, [1.0, 2.0, 3.0, 4.0]),
        ("silence", None, [1.0, None, 3.0, 4.0]),
    ],
)
def test_refine_data_applies_nan_strategy_and_row_range(
    composer_csv, strategy, fill_with, expected
):
    result = data_composer.refine_data(
        make_refine_request(
            strategy,
            fill_with,
            row_range=[1, 4],
            columns=["flux"],
        )
    )

    actual = result["flux"].tolist()
    expected_slice = expected[1:]
    if strategy == "silence":
        assert pd.isna(actual[0])
        assert actual[1:] == expected_slice[1:]
    else:
        assert actual == pytest.approx(expected_slice)


def test_preview_refined_converts_nan_to_json_null(composer_csv):
    result = data_composer.preview_refined(
        make_refine_request("silence", row_range=[0, 3])
    )

    assert result["rows"][0]["flux"] == 1.0
    assert result["rows"][1]["flux"] is None


def test_save_refined_stores_upload(monkeypatch, tmp_path, session_id):
    upload_dir = tmp_path / session_id / "uploads"
    upload_dir.mkdir(parents=True)
    monkeypatch.setattr(data_composer, "TMP_DIR", tmp_path)
    monkeypatch.setattr(
        data_composer, "resolve_file", lambda ref: tmp_path / "source.csv"
    )
    pd.DataFrame({"x": [1, 2]}).to_csv(tmp_path / "source.csv", index=False)
    request = make_refine_request(
        "silence", columns=["x"], row_range=[0, 2]
    )

    result = data_composer.save_refined(request)
    stored = upload_dir / result["file_ref"].split(":")[-1]

    assert result["file_ref"].startswith("session:uploads:")
    assert pd.read_csv(stored)["x"].tolist() == [1, 2]


def test_validate_layer_reports_missing_nonnumeric_and_insufficient_columns(
    monkeypatch, tmp_path
):
    data_path = tmp_path / "data.csv"
    style_path = tmp_path / "style.yml"
    pd.DataFrame({"label": ["a"], "flux": [1.0]}).to_csv(data_path, index=False)
    style_path.write_text(
        "map:\n"
        "  - output: time\n"
        "  - input: absent\n"
        "    output: pitch\n"
        "  - output: volume\n"
    )
    monkeypatch.setattr(
        data_composer,
        "resolve_file",
        lambda ref: data_path if ref.endswith("data.csv") else style_path,
    )

    result = data_composer.validate_layer(
        LayerRequest(data_ref="session:data.csv", style_ref="session:style.yml")
    )

    assert result == {
        "missing_columns": ["absent"],
        "non_numeric_columns": ["label"],
        "insufficient_columns": {"style": 3, "data": 2},
    }
