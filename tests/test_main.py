import asyncio
import sys
from types import SimpleNamespace

from fastapi import Request
from fastapi.responses import JSONResponse, Response

import main


def test_root_status():
    assert main.get_status() == {
        "message": "Hello! The server is up and running."
    }


def test_cleanup_status_reports_disk_and_session_state(monkeypatch):
    monkeypatch.setattr(
        main,
        "storage_manager",
        SimpleNamespace(
            get_disk_usage=lambda: (54.567, 20.0, 16.0),
            get_session_dirs=lambda: [(None, 0), (None, 1)],
            disk_threshold=70,
            emergency_threshold=80,
            min_free_bytes=2 * 1024**3,
            max_age_seconds=2 * 86400,
            cleanup_interval=6 * 3600,
        ),
    )

    result = asyncio.run(main.cleanup_status())

    assert result == {
        "disk_usage_percent": 54.57,
        "used_gb": 20.0,
        "free_gb": 16.0,
        "total_sessions": 2,
        "thresholds": {
            "normal_cleanup": 70,
            "emergency_cleanup": 80,
            "min_free_gb": 2.0,
        },
        "config": {"max_age_days": 2.0, "cleanup_interval_hours": 6.0},
    }


def test_session_middleware_sets_and_resets_session_context():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"cookie", b"session_id=middleware-test")],
            "query_string": b"",
            "server": ("test", 80),
            "client": ("127.0.0.1", 1234),
            "scheme": "http",
        }
    )
    observed = []

    async def call_next(current_request):
        observed.append(main.session_id_var.get())
        return Response("ok")

    response = asyncio.run(main.session_middleware(request, call_next))

    assert response.status_code == 200
    assert observed == ["middleware-test"]
    assert main.session_id_var.get() == "no_id"


def test_global_exception_handler_returns_generic_server_error():
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "server": ("test", 80),
            "client": ("127.0.0.1", 1234),
            "scheme": "http",
        }
    )

    response = asyncio.run(
        main.global_exception_handler(request, RuntimeError("private details"))
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 500
    assert response.body == b'{"detail":"Internal server error"}'


def test_lifespan_starts_and_cancels_cleanup_task(monkeypatch):
    monkeypatch.setattr(main.sys, "platform", "win32")
    calls = []

    async def background_cleanup():
        calls.append("started")
        await asyncio.Event().wait()

    monkeypatch.setattr(
        main,
        "storage_manager",
        SimpleNamespace(start_background_cleanup=background_cleanup),
    )

    async def exercise_lifespan():
        async with main.lifespan(main.app):
            await asyncio.sleep(0)

    asyncio.run(exercise_lifespan())

    assert calls == ["started"]
