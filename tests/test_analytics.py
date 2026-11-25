import csv
from types import SimpleNamespace

import analytics


def test_log_event_is_disabled_on_windows(monkeypatch, tmp_path):
    monkeypatch.setattr(analytics.sys, "platform", "win32")
    monkeypatch.setattr(analytics, "ANALYTICS_DIR", tmp_path)

    analytics.log_event("session", "127.0.0.1", "session_start")

    assert list(tmp_path.iterdir()) == []


def test_log_event_appends_country_and_event_to_monthly_csv(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(analytics.sys, "platform", "linux")
    monkeypatch.setattr(analytics, "ANALYTICS_DIR", tmp_path)
    monkeypatch.setattr(analytics, "LOCK_FILE", tmp_path / "analytics.lock")
    monkeypatch.setattr(analytics, "country_code", lambda ip: "GB")
    monkeypatch.setattr(
        analytics,
        "fcntl",
        SimpleNamespace(
            LOCK_EX=1,
            LOCK_UN=2,
            flock=lambda file, operation: None,
        ),
        raising=False,
    )

    analytics.log_event(
        "session-1", "127.0.0.1", "sonification_generated", "light_curves"
    )

    files = list(tmp_path.glob("????-??.csv"))
    assert len(files) == 1
    with files[0].open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 1
    assert rows[0]["session_id"] == "session-1"
    assert rows[0]["country"] == "GB"
    assert rows[0]["event"] == "sonification_generated"
    assert rows[0]["sonification_type"] == "light_curves"
