import asyncio
import sys


def decorator_asyncio_fix(func):
    def wrapper(*args):
        if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())
        return func(*args)
    return wrapper
