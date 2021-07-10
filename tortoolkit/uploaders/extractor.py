import asyncio
from ..utils.zip7_utils import extract_archive
from ..core.getVars import get_val
from ..utils.misc_utils import clear_stuff
import time

class Extractor:
    def __init__(self, path, update_message, user_message):
        self._path = path
        self._update_message = update_message
        self._user_message = user_message

    async def execute(self):
        self._update_message = self._update_message.client.get_messages(self._update_message.chat_id,ids=self._update_message.id)

        password = self._update_message.client.dl_passwords.get(self._user_message.id)
        if password is not None:
            password = password[1]
        start = time.time()
        await self._update_message.edit(f"{self._update_message.text}\nTrying to Extract the archive with password: `{password}`")
        wrong_pwd = False

        while True:
            if not wrong_pwd:
                ext_path = await extract_archive(self._path,password=password)
            else:
                if (time.time() - start) > 1200:
                    await self._update_message.edit(f"{self._update_message.text}\nExtract failed as no correct password was provided uploading as it is.")
                    return False

                temppass = self._update_message.client.dl_passwords.get(self._user_message.id)
                if temppass is not None:
                    temppass = temppass[1]
                if temppass == password:
                    await asyncio.sleep(10)
                    continue
                else:
                    password = temppass
                    wrong_pwd = False
                    continue
            
            if isinstance(ext_path, str):
                if "Wrong Password" in ext_path:
                    mess = f"<a href='tg://user?id={self._user_message.sender_id}'>RE-ENTER PASSWORD</a>\nThe passowrd <code>{password}</code> you provided is a wrong password.You have {((time.time()-start)/60)-20} Mins to reply else un extracted zip will be uploaded.\n Use <code>/setpass {self._user_message.id} password-here</code>"
                    await self._user_message.reply(mess, parse_mode="html")
                    wrong_pwd = True
                else:
                    await clear_stuff(self._path)
                    return ext_path
            
            elif ext_path is False:
                return False
            elif ext_path is None:
                # None is to descibe fetal but the upload will fail 
                # itself further nothing to handle here
                return False
            else:
                await clear_stuff(self._path)
                return ext_path