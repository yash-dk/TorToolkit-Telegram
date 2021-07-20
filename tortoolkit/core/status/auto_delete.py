import asyncio
import time

from ... import to_del
from ..getVars import get_val


async def del_status():
    while True:
        for i in to_del:
            diff = time.time() - i[1]
            if diff >= get_val("STATUS_DEL_TOUT"):
                await i[0].delete()
                to_del.remove(i)

            await asyncio.sleep(1)

        await asyncio.sleep(4)
