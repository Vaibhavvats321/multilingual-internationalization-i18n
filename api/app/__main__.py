"""Command line entry point for the API server.

This is the supported way to run the API because it selects the event loop
factory that psycopg requires on Windows (see
:mod:`app.core.event_loop`). It works identically on Linux, macOS and
Windows::

    uv run python -m app --reload
    uv run python -m app --host 0.0.0.0 --port 8000

Running ``uvicorn app.main:app`` directly also works on Linux and macOS.
On Windows the loop must be selected explicitly::

    uv run uvicorn app.main:app --loop app.core.event_loop:selector_loop_factory
"""

from __future__ import annotations

import argparse

import uvicorn

LOOP_FACTORY = "app.core.event_loop:selector_loop_factory"
APP_PATH = "app.main:app"


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    parser = argparse.ArgumentParser(
        prog="python -m app",
        description="Run the multilingual event platform API.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind.")
    parser.add_argument("--reload", action="store_true", help="Reload on source changes.")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes.")
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Override the log level.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the API server."""
    args = build_parser().parse_args(argv)
    uvicorn.run(
        APP_PATH,
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level,
        loop=LOOP_FACTORY,
    )


if __name__ == "__main__":
    main()
