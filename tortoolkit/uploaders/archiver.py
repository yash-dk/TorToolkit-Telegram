# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from ..utils.zip7_utils import add_to_zip
from ..core.getVars import get_val
from ..utils.misc_utils import clear_stuff

class Archiver:
    def __init__(self, path, update_message, user_message, split=True):
        self._path = path
        self._update_message = update_message
        self._user_message = user_message
        self._split = split

    async def execute(self):
        self._update_message = await self._update_message.client.get_messages(self._update_message.chat_id,ids=self._update_message.id)
        
        try:
            await self._update_message.edit(self._update_message.text+"\nStarting to Zip the contents. Please wait.")
            zip_path = await add_to_zip(self._path, get_val("TG_UP_LIMIT"), self._split)
            
            if zip_path is None:
                await self._update_message.edit(self._update_message.text+"\nZip failed. Fallbacked to normal.")
                return False
            
            await self._update_message.edit(self._update_message.text+"\nZipping done. Now uploading.")
            await clear_stuff(self._path)
            return zip_path
        except:
            await self._update_message.edit(self._update_message.text+"\nZip failed. Fallbacked to normal.")
            return False
        