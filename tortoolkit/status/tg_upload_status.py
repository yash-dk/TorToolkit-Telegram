from .base_status import BaseStatus
from ..utils.human_format import human_readable_bytes, human_readable_timedelta

class TGUploadStatus(BaseStatus):
    def __init__(self, downloader):
        self._downloader = downloader

    async def update_now(self):

        self._up_task = await self._downloader.get_update()
        return

    async def create_message(self):
        ...

    def get_type(self):
        return self.QBIT