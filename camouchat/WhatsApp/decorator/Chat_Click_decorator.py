import asyncio
import functools


def ensure_chat_clicked(chat_click_fn, retries=3, delay=0.5):
    """
    Decorator to ensure a chat is clicked using a provided click function.
    The function should be: async def(self, chat) -> bool
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, chat, *args, **kwargs):
            for attempt in range(1, retries + 1):
                clicked = await chat_click_fn(self, chat)
                if clicked:
                    break
                self.log.warning(f"[{func.__name__}] Click attempt {attempt} failed.")
                await asyncio.sleep(delay)
            else:
                self.log.error(f"[{func.__name__}] Failed to click chat after {retries} attempts.")
                raise Exception(f"[{func.__name__}] Chat click failed. Aborting.")

            return await func(self, chat, *args, **kwargs)

        return wrapper

    return decorator
