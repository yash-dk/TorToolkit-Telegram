# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import logging
import asyncio
from ..core.getVars import get_val
from telethon.errors import MessageNotModifiedError

torlog = logging.getLogger(__name__)

class StatusManager():
    ALL_STATUS = []
    CENTRAL_UPDATE = {}
    LOCK = asyncio.Lock()

    def __init__(self) -> None:
        pass

    async def generate_central_update(self, cmd_msg = None):
        print("gen called")
        renew = False
        if cmd_msg is not None:
            print("this set")
            self.CENTRAL_UPDATE["status_message"] = cmd_msg
            renew = True

        if self.CENTRAL_UPDATE.get("status_message", None) is not None:
            update_list = await self.get_update_list()
            if self.CENTRAL_UPDATE.get("prev_len", 0) == 0 or renew:
                for i in self.CENTRAL_UPDATE.get("update_message",[]):
                    await i.delete()
                
                if len(update_list) == 0:
                    if renew:
                        self.CENTRAL_UPDATE["status_message"] = None
                        await cmd_msg.reply("No new status messages")
                    return
                self.CENTRAL_UPDATE["prev_len"] = len(update_list)
                self.CENTRAL_UPDATE["update_message"] = []
                
                for i in update_list:
                    srmsg = await self.CENTRAL_UPDATE["status_message"].reply(i, parse_mode="html")
                    self.CENTRAL_UPDATE["update_message"].append(srmsg)
                    await asyncio.sleep(1.1)
            elif self.CENTRAL_UPDATE.get("prev_len") != len(update_list):
                for i in self.CENTRAL_UPDATE["update_message"]:
                    await i.delete()
                
                for i in update_list:
                    srmsg = await self.CENTRAL_UPDATE["status_message"].reply(i, parse_mode="html")
                    self.CENTRAL_UPDATE["update_message"].append(srmsg)
                    await asyncio.sleep(1.1)
            elif self.CENTRAL_UPDATE.get("prev_len") == len(update_list):
                for i,j in zip(self.CENTRAL_UPDATE["update_message"], update_list):
                    try:
                        await i.edit(j, parse_mode="html")
                    except MessageNotModifiedError:
                        pass
                    await asyncio.sleep(0.5)

    async def status_manager(self):
        torlog.debug('Status called')
        if get_val("CENTRAL_UPDATE"):
            await self.generate_central_update()
        else:
            for i in self.ALL_STATUS:
                if i.is_active and not i.is_inactive:
                    try:
                        await i.update_now()
                    except MessageNotModifiedError:
                        pass
                    except:
                        torlog.exception("This was unexpected.")
                    await asyncio.sleep(1.1)

    async def get_update_list(self):
        msg_list = []
        curr_msg = ""
        for i in self.ALL_STATUS:
            if i.is_active and not i.is_inactive:
                try:
                    try:
                        temp_msg = await i.update_now(True)
                    except:
                        torlog.exception("in update")
                        temp_msg = "Unknown Task Running....\n\n"
                    if (len(temp_msg) + len(curr_msg) > 4000):
                        msg_list.append(curr_msg)
                        curr_msg = temp_msg
                    else:
                        curr_msg += temp_msg
                    
                except:
                    pass
        
        if curr_msg != "":
            msg_list.append(curr_msg)
        
        return msg_list
            

    def add_status(self, status):
        self.ALL_STATUS.append(status)
        # type will be printed
        torlog.debug('Added status: {}'.format(status))

    async def status_poller(self):
        torlog.info("Status polling started")
        while True:
            await self.status_manager()
            await asyncio.sleep(get_val('EDIT_SLEEP_SECS'))