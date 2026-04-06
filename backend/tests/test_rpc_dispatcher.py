from __future__ import annotations

import pytest

from backend.rpc.dispatcher import RpcDispatcher


def test_rpc_dispatcher_registers_dispatches_and_lists_methods() -> None:
    dispatcher = RpcDispatcher()
    dispatcher.register("rooms.echo", lambda params: {"echo": params["value"]})

    assert dispatcher.has_method("rooms.echo") is True
    assert dispatcher.dispatch("rooms.echo", {"value": 42}) == {"echo": 42}
    assert dispatcher.list_methods() == ["rooms.echo"]


def test_rpc_dispatcher_raises_for_unknown_method() -> None:
    dispatcher = RpcDispatcher()

    with pytest.raises(ValueError, match="Unknown method: missing.method"):
        dispatcher.dispatch("missing.method", {})
