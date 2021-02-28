from .status import Status, QBTask
from ..getVars import get_val
import os

class TGUploadTask(Status):
    
    def __init__(self, task):
        super().__init__()
        self._dl_task = task
        self._files = 0
        self._dirs = 0
        self._uploaded_files = 0
        self._inactive = False
        self._current_file = ""

    async def set_inactive(self):
        self._inactive = True

    async def get_inactive(self):
        return self._inactive

    async def add_a_dir(self, path):
        self.dl_files(path)

    async def dl_files(self, path = None):
        if path is None:
            path = self._dl_task.path
        
        files = self._files
        dirs = self._dirs
        for _, d, f in os.walk(path, topdown=False):
            for _ in f:
                files += 1
            for _ in d:
                dirs += 1
        
        # maybe will add blacklisting of Extensions
        self._files = files
        self._dirs = dirs

    async def uploaded_file(self, name=None):
        self._uploaded_files += 1
        print("\n----updates files to {}\n".format(self._uploaded_files))
        self._current_file = str(name)

    async def create_message(self):
        msg = "<b>Uploading:- </b> <code>{}</code>\n".format(
            self._current_file
        )
        prg = 0
        try:
            prg = self._uploaded_files/self._files

        except ZeroDivisionError:pass
        msg += "<b>Progress:- </b> {} - {}\n".format(
            self.progress_bar(prg),
            prg*100
        )
        msg += "<b>Files:- </b> {} of {} done.\n".format(
            self._uploaded_files,
            self.dl_files
        )
        msg += "<b>Type:- </b> <code>TG Upload</code>\n"

    def progress_bar(self, percentage):
        """Returns a progress bar for download
        """
        #percentage is on the scale of 0-1
        comp = get_val("COMPLETED_STR")
        ncomp = get_val("REMAINING_STR")
        pr = ""

        for i in range(1,11):
            if i <= int(percentage*10):
                pr += comp
            else:
                pr += ncomp
        return pr