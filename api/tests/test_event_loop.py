"""Regression tests for the event loop selection.

psycopg's asynchronous connections require a selector based event loop. On
Windows uvicorn's built-in ``asyncio`` loop factory installs a proactor loop,
which makes every async database connection fail with::

    InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode.

These tests lock in the selector loop so the failure cannot come back.
"""

from __future__ import annotations

import asyncio
import sys

import pytest

from app.core.event_loop import install_event_loop_policy, selector_loop_factory


def test_loop_factory_returns_a_selector_loop() -> None:
    loop = selector_loop_factory()

    try:
        assert isinstance(loop, asyncio.SelectorEventLoop)
    finally:
        loop.close()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific event loop behaviour")
def test_loop_factory_does_not_return_a_proactor_loop() -> None:
    loop = selector_loop_factory()

    try:
        assert not isinstance(loop, asyncio.ProactorEventLoop)
    finally:
        loop.close()


def test_loop_factory_supports_the_reader_hooks_psycopg_needs() -> None:
    """A selector loop must expose ``add_reader``/``add_writer``."""
    loop = selector_loop_factory()

    try:
        assert hasattr(loop, "add_reader")
        assert hasattr(loop, "add_writer")
    finally:
        loop.close()


def test_install_event_loop_policy_is_idempotent() -> None:
    install_event_loop_policy()
    install_event_loop_policy()
