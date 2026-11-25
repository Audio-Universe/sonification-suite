import asyncio
import base64
import json

import pandas as pd
import pytest
from fastapi import HTTPException

import constellations
from request_models import ConstellationRequest, DataRequest, NStarsRequest


def test_edges_from_lines_ignores_labels_and_connects_adjacent_stars():
    assert constellations._edges_from_lines(
        [[1, 2, 3], ["thin", 4, 5], [6], ["thin"]]
    ) == [(1, 2), (2, 3), (4, 5)]


def test_load_patterns_extracts_constellations_and_skips_empty_helpers(tmp_path):
    source = tmp_path / "patterns.json"
    source.write_text(
        json.dumps(
            {
                "constellations": [
                    {
                        "common_name": {"native": "Test"},
                        "iau": "TST",
                        "lines": [[1, 2, 3]],
                    }
                ],
                "asterisms": [
                    {
                        "common_name": {"english": "Empty"},
                        "lines": [[1]],
                    },
                    {
                        "common_name": {"english": "Helper"},
                        "is_ray_helper": True,
                        "lines": [[1, 2]],
                    },
                    {
                        "common_name": {"english": "Pair"},
                        "lines": [["thin", 4, 5]],
                    },
                ],
            }
        )
    )

    patterns = constellations._load_patterns(source)

    assert patterns == {
        "Test": {
            "type": "constellation",
            "iau": "TST",
            "edges": [(1, 2), (2, 3)],
        },
        "Pair": {"type": "asterism", "iau": None, "edges": [(4, 5)]},
    }


def test_get_pattern_raises_for_unknown_name(monkeypatch):
    monkeypatch.setattr(constellations, "PATTERNS", {})

    with pytest.raises(HTTPException) as exc_info:
        constellations._get_pattern("Missing")

    assert exc_info.value.status_code == 404


def test_get_constellation_filters_by_edges_and_sorts_by_brightness(
    monkeypatch, tmp_path
):
    path = tmp_path / "stars.csv"
    pd.DataFrame(
        {
            "hip": [1, 2, 3],
            "con": ["TST", "TST", "OTHER"],
            "magnitude": [2.0, 1.0, 0.0],
            "ra": [10.0, 11.0, 12.0],
            "dec": [1.0, 2.0, 3.0],
        }
    ).to_csv(path, index=False)
    monkeypatch.setattr(constellations, "HYG_DATA", path)
    monkeypatch.setattr(
        constellations,
        "PATTERNS",
        {
            "Test": {
                "type": "constellation",
                "iau": "TST",
                "edges": [(1, 2)],
            }
        },
    )

    shape_stars = constellations.get_constellation("Test", stick_figure=True)
    boundary_stars = constellations.get_constellation("Test", stick_figure=False)

    assert shape_stars["hip"].tolist() == [2, 1]
    assert boundary_stars["hip"].tolist() == [2, 1]
    assert shape_stars["ra_corrected"].tolist() == [11.0, 10.0]


def test_get_constellation_rejects_non_official_boundary_query(monkeypatch, tmp_path):
    path = tmp_path / "stars.csv"
    pd.DataFrame(
        {"hip": [1], "con": ["TST"], "magnitude": [1], "ra": [1], "dec": [1]}
    ).to_csv(path, index=False)
    monkeypatch.setattr(constellations, "HYG_DATA", path)
    monkeypatch.setattr(
        constellations,
        "PATTERNS",
        {"NoBoundary": {"type": "constellation", "iau": None, "edges": [(1, 2)]}},
    )

    with pytest.raises(HTTPException) as exc_info:
        constellations.get_constellation("NoBoundary", stick_figure=False)
    assert exc_info.value.status_code == 400


def test_correct_ra_unwraps_only_across_zero_hour():
    assert constellations.correct_ra(pd.Series([23.5, 0.5])).tolist() == [
        23.5,
        24.5,
    ]
    assert constellations.correct_ra(pd.Series([10.0, 11.0])).tolist() == [
        10.0,
        11.0,
    ]


def test_get_pattern_from_df_finds_the_pattern_with_most_edges(monkeypatch):
    monkeypatch.setattr(
        constellations,
        "PATTERNS",
        {
            "One": {"edges": [(1, 2), (2, 3)]},
            "Two": {"edges": [(1, 2)]},
        },
    )

    assert constellations.get_pattern_from_df(pd.DataFrame(index=[1, 2, 3])) == "One"
    assert constellations.get_pattern_from_df(pd.DataFrame(index=[8, 9])) is None


def test_plot_constellation_returns_svg_and_rejects_empty_data():
    frame = pd.DataFrame(
        {
            "ra_corrected": [10.0, 11.0],
            "dec": [20.0, 21.0],
            "magnitude": [1.0, 2.0],
            "colour": [0.2, 1.0],
            "proper": ["First", ""],
        },
        index=pd.Index([1, 2], name="hip"),
    )

    image = constellations.plot_and_format_constellation(frame, lines=False)

    assert base64.b64decode(image).lstrip().startswith(b"<?xml")
    with pytest.raises(ValueError, match="No stars"):
        constellations.plot_and_format_constellation(frame.iloc[:0], False)


def test_list_patterns_separates_constellations_and_asterisms(monkeypatch):
    monkeypatch.setattr(
        constellations,
        "PATTERNS",
        {
            "Test": {"type": "constellation"},
            "Pair": {"type": "asterism"},
        },
    )

    assert asyncio.run(constellations.list_patterns()) == {
        "constellations": ["Test"],
        "asterisms": ["Pair"],
    }


def test_plot_csv_reads_uploaded_data_and_uses_stick_figure_flag(
    monkeypatch, tmp_path
):
    source = tmp_path / "imported.csv"
    pd.DataFrame(
        {
            "hip": [1],
            "stick_figure": [True],
            "ra_corrected": [10],
            "dec": [20],
        }
    ).to_csv(source, index=False)
    calls = {}
    monkeypatch.setattr(constellations, "resolve_file", lambda ref: source)
    monkeypatch.setattr(
        constellations,
        "plot_and_format_constellation",
        lambda frame, lines: calls.update(frame=frame, lines=lines) or "image",
    )

    result = asyncio.run(
        constellations.plot_csv(DataRequest(file_ref="session:imported.csv"))
    )

    assert result == {"image": "image"}
    assert calls["frame"].index.tolist() == [1]
    assert calls["lines"] is True


def test_plot_csv_rejects_non_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(
        constellations, "resolve_file", lambda ref: tmp_path / "stars.txt"
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            constellations.plot_csv(DataRequest(file_ref="session:stars.txt"))
        )
    assert exc_info.value.status_code == 400


def test_plot_constellation_limits_boundary_order_and_translates_plot_errors(
    monkeypatch,
):
    stars = pd.DataFrame(
        {
            "hip": [3, 1, 2],
            "magnitude": [3.0, 1.0, 2.0],
        }
    )
    calls = {}
    monkeypatch.setattr(
        constellations,
        "get_constellation",
        lambda *args, **kwargs: stars.sort_values("magnitude"),
    )
    monkeypatch.setattr(
        constellations,
        "plot_and_format_constellation",
        lambda frame, lines: calls.update(frame=frame, lines=lines) or "image",
    )
    request = ConstellationRequest(
        name="Test", stick_figure=False, n_stars=2
    )

    assert asyncio.run(constellations.plot_constellation(request)) == {
        "image": "image"
    }
    assert calls["frame"].index.tolist() == [1, 2]
    assert calls["lines"] is False

    def raise_plot_error(frame, lines):
        raise ValueError("no stars")

    monkeypatch.setattr(
        constellations, "plot_and_format_constellation", raise_plot_error
    )
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(constellations.plot_constellation(request))
    assert exc_info.value.status_code == 400


def test_get_plotting_data_includes_only_known_pattern_edges(monkeypatch):
    stars = pd.DataFrame(
        {
            "hip": [1, 2],
            "ra_corrected": [10.0, 11.0],
            "dec": [20.0, 21.0],
            "display_name": ["A", "B"],
        }
    )
    monkeypatch.setattr(constellations, "get_constellation", lambda *args, **kwargs: stars)
    monkeypatch.setattr(
        constellations,
        "PATTERNS",
        {"Test": {"edges": [(1, 2), (2, 3)]}},
    )

    result = asyncio.run(
        constellations.get_plotting_data(
            ConstellationRequest(name="Test", stick_figure=True)
        )
    )

    assert result == {
        "lines": [[1, 2]],
        "stars": [
            {"id": 1, "ra": 10.0, "dec": 20.0, "display_name": "A"},
            {"id": 2, "ra": 11.0, "dec": 21.0, "display_name": "B"},
        ],
    }


def test_get_magnitude_and_n_stars_apply_requested_limits(monkeypatch):
    stars = pd.DataFrame({"magnitude": [1.0, 2.0, 3.0]})
    monkeypatch.setattr(constellations, "get_constellation", lambda *args, **kwargs: stars)

    assert asyncio.run(
        constellations.get_magnitude(
            ConstellationRequest(name="Test", n_stars=2)
        )
    ) == {"max_magnitude": 2.0}
    assert asyncio.run(
        constellations.get_n_stars(NStarsRequest(name="Test", max_magnitude=2))
    ) == {"n_stars": 2}


def test_constellation_center_unwraps_ra_and_handles_single_star():
    frame = pd.DataFrame({"ra": [23.0, 1.0], "dec": [10.0, 14.0]})
    single = pd.DataFrame({"ra": [3.0], "dec": [-5.0]})

    assert constellations.constellation_center(frame) == (0.0, 12.0)
    assert constellations.constellation_center(single) == (45.0, -5.0)


def test_save_refined_sets_custom_order_and_session_reference(
    monkeypatch, tmp_path, session_id
):
    (tmp_path / session_id).mkdir()
    stars = pd.DataFrame(
        {
            "hip": [11, 22],
            "ra": [1.0, 2.0],
            "dec": [3.0, 5.0],
            "magnitude": [1.0, 2.0],
        }
    )
    monkeypatch.setattr(constellations, "TMP_DIR", tmp_path)
    monkeypatch.setattr(
        constellations, "get_constellation", lambda *args, **kwargs: stars.copy()
    )

    result = asyncio.run(
        constellations.save_refined(
            ConstellationRequest(
                name="Test", stick_figure=True, order=[22, 11]
            )
        )
    )

    saved = pd.read_csv(tmp_path / session_id / "constellations.csv")
    assert result["file_ref"] == "session:constellations.csv"
    assert saved["custom_order"].tolist() == [2, 1]
    assert saved["stick_figure"].tolist() == [True, True]
    assert (result["ra"], result["dec"]) == (22.5, 4.0)
