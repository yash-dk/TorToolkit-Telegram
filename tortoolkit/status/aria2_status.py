from .base_status import BaseStatus
from ..utils.human_format import human_readable_bytes, human_readable_timedelta

class Aria2Status(BaseStatus):
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
        downloading_dir_name = "N/A"
        try:
            downloading_dir_name = str(self._dl_task.name)
        except:
            pass

        msg = "<b>Downloading:</b> <code>{}</code>\n".format(
            downloading_dir_name
            )
        msg += "<b>Down:</b> {} <b>Up:</b> {}\n".format(
            self._dl_task.download_speed_string(),
            self._dl_task.upload_speed_string()
            )
        msg += "<b>Progress:</b> {} - {}%\n".format(
            self.progress_bar(self._dl_task.progress/100),
            round(self._dl_task.progress,2)
            )
        msg += "<b>Downloaded:</b> {} of {}\n".format(
            human_readable_bytes(self._dl_task.completed_length),
            human_readable_bytes(self._dl_task.total_length)
            )
        msg += "<b>ETA:</b> <b>{} Mins</b>\n".format(
            self._dl_task.eta_string()
            )
        msg += "<b>Conns:</b>{} <b>\n".format(
            self._dl_task.connections
            )
        msg += "<b>Using engine:</b> <code>Aria2 For DirectLinks</code>"

        return msg

    def get_type(self):
        return self.ARIA2