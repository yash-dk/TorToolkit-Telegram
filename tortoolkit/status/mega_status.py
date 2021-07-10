from .base_status import BaseStatus
from ..utils.human_format import human_readable_bytes, human_readable_timedelta

class MegaStatus(BaseStatus):
    def __init__(self, controller, downloader=None):
        self._controller = controller
        self._downloader = downloader

    async def update_now(self):
        if self._downloader is None:
            self._downloader = await self._controller.get_downloader()

        self._update_message = await self._controller.get_update_message()

        self._dl_task = await self._downloader.get_update()

        # Construct the status message
        await self._update_message.edit(await self.create_message())

    async def create_message(self):

        msg = "<b>Downloading:</b> <code>{}</code>\n".format(
            self._dl_task["name"]
            )
        msg += "<b>Speed:</b> {}\n".format(
            human_readable_bytes(self._dl_task["speed"])
            )
        msg += "<b>Progress:</b> {} - {}%\n".format(
            self.progress_bar((self._dl_task["completed_length"]/self._dl_task["total_length"])),
            round((self._dl_task["completed_length"]/self._dl_task["total_length"])*100, 2)
            )
        msg += "<b>Downloaded:</b> {} of {}\n".format(
            human_readable_bytes(self._dl_task["completed_length"]),
            human_readable_bytes(self._dl_task["total_length"])
            )
        msg += "<b>ETA:</b> <b>N/A</b>\n"
        
        msg += "<b>Using engine:</b> <code>Mega DL</code>"

        return msg

    def get_type(self):
        return self.MEGA