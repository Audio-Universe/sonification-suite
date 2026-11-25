import asyncio
import os
from types import SimpleNamespace

import pytest

import StorageManager as storage_module
from StorageManager import StorageManager


def test_disk_usage_returns_percent_used_and_gigabytes(monkeypatch, tmp_path):
    gib = 1024**3
    monkeypatch.setattr(
        storage_module.shutil,
        "disk_usage",
        lambda path: SimpleNamespace(total=10 * gib, used=7 * gib, free=3 * gib),
    )
    manager = StorageManager(tmp_path)

    assert manager.get_disk_usage() == (70.0, 7.0, 3.0)


def test_session_directories_are_sorted_oldest_first(tmp_path):
    manager = StorageManager(tmp_path)
    newer = tmp_path / "newer"
    older = tmp_path / "older"
    newer.mkdir()
    older.mkdir()
    os.utime(older, (100, 100))
    os.utime(newer, (200, 200))

    assert [path.name for path, _ in manager.get_session_dirs()] == [
        "older",
        "newer",
    ]


def test_delete_session_dir_reports_success_and_failure(tmp_path):
    manager = StorageManager(tmp_path)
    session = tmp_path / "session"
    session.mkdir()
    (session / "data.txt").write_text("data")

    assert manager.delete_session_dir(session) is True
    assert not session.exists()
    assert manager.delete_session_dir(session) is False


def test_cleanup_old_sessions_deletes_expired_and_reports_freed_space(
    monkeypatch, tmp_path
):
    manager = StorageManager(tmp_path, max_age_days=1)
    expired = tmp_path / "expired"
    recent = tmp_path / "recent"
    expired.mkdir()
    recent.mkdir()
    (expired / "payload").write_bytes(b"x" * 2048)
    os.utime(expired, (100, 100))
    os.utime(recent, (172000, 172000))
    monkeypatch.setattr(storage_module.time, "time", lambda: 100 + 2 * 86400)

    result = manager.cleanup_old_sessions()

    assert result["deleted_count"] == 1
    assert result["freed_mb"] == pytest.approx(2048 / (1024**2))
    assert not expired.exists()
    assert recent.exists()


def test_cleanup_by_disk_usage_removes_oldest_until_below_threshold(
    monkeypatch, tmp_path
):
    manager = StorageManager(
        tmp_path,
        disk_threshold_percent=70,
        min_free_gb=0,
    )
    old = tmp_path / "old"
    old.mkdir()
    (old / "payload").write_bytes(b"payload")
    readings = iter([(90.0, 9.0, 1.0), (90.0, 9.0, 1.0)])
    monkeypatch.setattr(manager, "get_disk_usage", lambda: next(readings))

    result = manager.cleanup_by_disk_usage()

    assert result["deleted_count"] == 1
    assert result["reason"] == "disk-threshold"
    assert not old.exists()


def test_cleanup_analytics_removes_old_month_files(monkeypatch, tmp_path):
    monkeypatch.setattr(storage_module, "ANALYTICS_DIR", tmp_path)
    (tmp_path / "2020-01.csv").touch()
    (tmp_path / "2099-01.csv").touch()
    (tmp_path / "not-a-month.csv").touch()

    StorageManager(tmp_path / "sessions").cleanup_analytics(retention_months=12)

    assert not (tmp_path / "2020-01.csv").exists()
    assert (tmp_path / "2099-01.csv").exists()
    assert (tmp_path / "not-a-month.csv").exists()


def test_run_cleanup_combines_policy_results(monkeypatch, tmp_path):
    manager = StorageManager(tmp_path)
    monkeypatch.setattr(manager, "get_disk_usage", lambda: (20.0, 2.0, 8.0))
    monkeypatch.setattr(
        manager,
        "cleanup_old_sessions",
        lambda: {"deleted_count": 1, "freed_mb": 2.0, "reason": "age-based"},
    )
    monkeypatch.setattr(manager, "cleanup_analytics", lambda: None)

    result = manager.run_cleanup()

    assert result["age_cleanup"]["deleted_count"] == 1
    assert result["cleanup_mode"] == "normal"
    assert result["initial_disk_usage_percent"] == 20.0
    assert result["final_disk_usage_percent"] == 20.0


def test_background_cleanup_runs_then_can_be_cancelled(monkeypatch, tmp_path):
    manager = StorageManager(tmp_path, cleanup_interval_hours=1)
    called = asyncio.Event()

    def run_cleanup():
        called.set()
        return {}

    monkeypatch.setattr(manager, "run_cleanup", run_cleanup)

    async def run_once():
        task = asyncio.create_task(manager.start_background_cleanup())
        await asyncio.wait_for(called.wait(), timeout=1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run_once())
