"""
msg_event_hook — the stealth message event decorator.

Wraps any async Python function so that it is called automatically
whenever a new WhatsApp message arrives, with the message already
normalized as a clean MessageModelAPI object.

Usage:
    from camouchat.WhatsApp.decorator.msg_event_hook import msg_event_hook
    from camouchat.WhatsApp.api import WapiSession

    wapi = WapiSession(page)
    await wapi.start()

    @msg_event_hook(wapi)
    async def on_message(msg: MessageModelAPI) -> None:
        print(f"New message from {msg.jid_From}: {msg.body}")

    # The listener is now live. Keep the event loop running.
    await asyncio.sleep(float('inf'))

Guard contract (checked at decoration time, not call time):
  - wapi.bridge must have already run wait_for_ready().
  - If the bridge is not ready, RuntimeError is raised immediately
    so the developer gets an explicit error rather than silent failure.
"""

import asyncio
import functools
from camouchat.WhatsApp.api import WapiSession
from typing import Any, Callable, Coroutine


def msg_event_hook(wapi_session: WapiSession) -> Callable:
    """
    Decorator factory that hooks into WhatsApp's real-time message stream.

    Internally calls:
        wapi_session.messages.start_listener(wrapped_func)

    Which wires:
        Main World WPP.on('chat.new_message')
            → id_serialized across DOM boundary
            → Isolated World RAM fetch via _evaluate_stealth
            → MessageModelAPI.from_dict(raw)
            → wrapped_func(msg)

    Args:
        wapi_session: A fully started WapiSession instance.
                      (wapi_session.start() must have been awaited.)

    Returns:
        A decorator that registers the function as a message handler.

    Raises:
        RuntimeError: If the WPP bridge is not ready at decoration time.
        TypeError:    If the decorated function is not a coroutine function.
    """

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(
                f"@msg_event_hook: '{func.__name__}' must be an async function. "
                f"Got: {type(func)}"
            )

        @functools.wraps(func)
        async def _register() -> None:
            is_ready = getattr(wapi_session, "is_ready", False)
            if not is_ready:
                await wapi_session.start()

            msg_manager = getattr(wapi_session, "message_manager", None)
            if msg_manager is None:
                raise RuntimeError(
                    "@msg_event_hook: wapi_session has no 'messages' manager. "
                    "Ensure WapiSession is fully initialised."
                )

            msg_manager.register_handler(func)

        # Return the registration coroutine so the caller can await it
        # or schedule it: e.g. `await on_message()` or `asyncio.ensure_future(on_message())`
        return _register

    return decorator
