# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import logging
import asyncio
from ..core.getVars import get_val
from telethon.errors import MessageNotModifiedError

torlog = logging.getLogger(__name__)

class StatusManager():
    ALL_STATUS = []

    def __init__(self) -> None:
        pass

    async def status_manager(self):
        torlog.debug('Status called')
        for i in self.ALL_STATUS:
            if i.is_active and not i.is_inactive:
                try:
                    await i.update_now()
                except MessageNotModifiedError:
                    pass
                except:
                    torlog.exception("This was unexpected.")
                await asyncio.sleep(1.1)

    def add_status(self, status):
        self.ALL_STATUS.append(status)
        # type will be printed
        torlog.debug('Added status: {}'.format(status))

    async def status_poller(self):
        torlog.info("Status polling started")
        while True:
            await self.status_manager()
            await asyncio.sleep(get_val('EDIT_SLEEP_SECS'))