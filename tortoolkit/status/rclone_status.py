from .base_status import BaseStatus
from ..utils.human_format import human_readable_bytes, human_readable_timedelta

class RcloneStatus(BaseStatus):
    def __init__(self, controller, downloader=None):
        self._controller = controller
        self._downloader = downloader

    async def update_now(self):
        if self._downloader is None:
            self._downloader = await self._controller.get_downloader()

        self._update_message = await self._controller.get_update_message()

        self._up_task = await self._downloader.get_update()

        # Construct the status message
        if self._up_task is not None:
            await self._update_message.edit(await self.create_message(), parse_mode="html")

    async def create_message(self):
        try:
            prg = int(self._up_task.prg)
        except:
            prg = 0
        prg = "{} - {}%".format(self.progress_bar(prg/100), prg)
        msg = "<b>Uploaded:- {} \n{} \nSpeed:- {} \nETA:- {}</b> \n<b>Using Engine:- </b><code>RCLONE</code>".format(self._up_task.uploaded,prg,self._up_task.speed,self._up_task.eta.replace("ETA",""))

        return msg

    def get_type(self):
        return self.QBIT