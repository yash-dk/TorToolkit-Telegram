# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import logging
import asyncio

from telethon.tl.types import KeyboardButtonCallback
from ..core.getVars import get_val
from telethon.errors import MessageNotModifiedError

torlog = logging.getLogger(__name__)

class StatusManager():
    ALL_STATUS = []
    CENTRAL_UPDATE = {}
    LOCK = asyncio.Lock()

    def __init__(self) -> None:
        pass

    async def generate_central_update(self, cmd_msg = None, sender_id=None):
        # Default behaviour is that when all the tasks are completed 
        # the message deletes itself.
        renew = False
        if sender_id is not None:
            update_list, butts = await self.get_update_list(sender_id)
            for i in update_list: 
                await cmd_msg.reply(i, parse_mode="html", buttons=butts)
            
            return

        if cmd_msg is not None:
            self.CENTRAL_UPDATE["status_message"] = cmd_msg
            renew = True

        if self.CENTRAL_UPDATE.get("status_message", None) is not None:
            update_list, butts = await self.get_update_list()
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
                    srmsg = await self.CENTRAL_UPDATE["status_message"].reply(i, parse_mode="html", buttons=butts)
                    self.CENTRAL_UPDATE["update_message"].append(srmsg)
                    await asyncio.sleep(1.1)
            elif self.CENTRAL_UPDATE.get("prev_len") != len(update_list):
                for i in self.CENTRAL_UPDATE["update_message"]:
                    await i.delete()
                
                for i in update_list:
                    srmsg = await self.CENTRAL_UPDATE["status_message"].reply(i, parse_mode="html", buttons=butts)
                    self.CENTRAL_UPDATE["update_message"].append(srmsg)
                    await asyncio.sleep(1.1)
            elif self.CENTRAL_UPDATE.get("prev_len") == len(update_list):
                for i,j in zip(self.CENTRAL_UPDATE["update_message"], update_list):
                    try:
                        await i.edit(j, parse_mode="html", buttons=butts)
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

    def get_num(self, no):
        nums = ['0️⃣','1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
        numstr = ""

        if no <= 9:
            return nums[no]
        else:
            for i in str(no):
                numstr += nums[int(i)]

        return numstr

    async def get_update_list(self, sender_id = None):
        msg_list = []
        curr_msg = ""
        butts = []
        local_row = []
        counter = 1
        for i in self.ALL_STATUS:
            if i.is_active and not i.is_inactive:
                try:
                    try:
                        if sender_id is not None:
                            if str(i.get_sender_id()) == str(sender_id):
                                temp_msg, temp_but = await i.update_now(True)
                                local_row.append(KeyboardButtonCallback(self.get_num(counter), temp_but))
                                
                        else:
                            temp_msg, temp_but = await i.update_now(True)
                            local_row.append(KeyboardButtonCallback(self.get_num(counter), temp_but))
                    
                    except:
                        torlog.exception("in update")
                        temp_msg = "Unknown Task Running....\n\n"
                        
                    
                    temp_msg = self.get_num(counter) + " " + temp_msg
                    counter += 1
                    
                    if len(local_row) >= 4:
                        butts.append(local_row)
                        local_row = []
                    
                    if (len(temp_msg) + len(curr_msg) > 4000):
                        msg_list.append(curr_msg)
                        curr_msg = temp_msg
                    else:
                        curr_msg += "\n\n"+str(temp_msg)
                    
                except:
                    pass
        
        if local_row != []:
            butts.append(local_row)

        if curr_msg != "":
            msg_list.append(curr_msg)
        
        return msg_list, butts
            

    def add_status(self, status):
        self.ALL_STATUS.append(status)
        # type will be printed
        torlog.debug('Added status: {}'.format(status))

    async def status_poller(self):
        torlog.info("Status polling started")
        while True:
            try:
                await self.status_manager()
            except Exception as e:
                torlog.info("in status update "+str(e))
            await asyncio.sleep(get_val('EDIT_SLEEP_SECS'))