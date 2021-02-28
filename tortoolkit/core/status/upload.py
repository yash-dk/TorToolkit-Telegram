from .status import Status, QBTask
import os

class TGUploadTask(Status):
    
    def __init__(self, task):
        super().__init__()
        self._dl_task = task
        self._files = 0
        self._dirs = 0
        self._uploaded_files = 0

    async def dl_files(self):
        files = 0
        dirs = 0
        for _, d, f in os.walk(self._dl_task.path, topdown=False):
            for _ in f:
                files += 1
            for _ in d:
                dirs += 1
        
        # maybe will add blacklisting of Extensions
        self._files = files
        self._dirs = dirs

    async def uploaded_file(self):
        self._uploaded_files += 1