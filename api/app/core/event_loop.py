"""Event loop selection for the API process.

psycopg's asynchronous connections are implemented on top of the event loop's
reader/writer hooks, which only a *selector* based loop provides. uvicorn's
built-in ``asyncio`` loop factory picks the loop per platform::

    # uvicorn/loops/asyncio.py
    def asyncio_loop_factory(use_subprocess: bool = False):
        if sys.platform == "win32" and not use_subprocess:
            return asyncio.ProactorEventLoop
        return asyncio.SelectorEventLoop

On Windows that means every async psycopg connection fails with::

    InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode.

The loop is created *before* uvicorn imports the application module, so the
policy cannot be changed from inside the app: uvicorn resolves the factory
first and then builds the loop. uvicorn does, however, accept a custom
factory through its ``loop`` option (``"<module>:<attribute>"``), which is
what :func:`selector_loop_factory` is for.

On Linux and macOS the selector loop is already the default, so the factory
changes nothing there.
"""

from __future__ import annotations

import asyncio
import sys
import warnings


def selector_loop_factory() -> asyncio.AbstractEventLoop:
    """Create the event loop used by the API process.

    uvicorn resolves a custom ``--loop`` value as ``"<module>:<attribute>"``
    and uses the imported object directly as the loop factory, so this
    function must be a zero argument callable returning a ready to use event
    loop. (``uvicorn.Config.get_loop_factory`` only passes ``use_subprocess``
    to the built-in factories.)

    ``asyncio.SelectorEventLoop`` resolves to the platform default selector:
    ``selectors.SelectSelector`` on Windows and ``selectors.EpollSelector`` on
    Linux. Both implement the reader/writer hooks psycopg relies on.
    """
    return asyncio.SelectorEventLoop()


def install_event_loop_policy() -> None:
    """Install a selector event loop policy for in-process loop creation.

    This is used by the test suite (pytest-asyncio creates the per-test loop)
    and by any embedding that creates its own loop. The server process itself
    uses :func:`selector_loop_factory` instead, because the policy is resolved
    too late there.
    """
    if sys.platform != "win32":
        return

    selector_policy_cls = getattr(asyncio, "WindowsSelectorEventLoopPolicy", None)
    if selector_policy_cls is None:  # pragma: no cover - removed in future CPython
        return

    current_policy = asyncio.get_event_loop_policy()
    if isinstance(current_policy, selector_policy_cls):
        return

    with warnings.catch_warnings():
        # The policy API is deprecated from Python 3.14 onwards. This project
        # pins Python 3.13, but the guard keeps the future upgrade painless.
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(selector_policy_cls())
