# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from abc import ABC, abstractmethod
from ..core.getVars import get_val
# TODO add fallback to deactivate the tasks just in case the
#      status is not properly disabled if task is_complete
#      then the task is_active is false and etc

class BaseStatus(ABC):
    QBIT = 0
    ARIA2 = 1
    MEGA = 2
    YTDL = 3
    PYTDL = 4
    RCLUP = 5
    TGUP = 6
    def __init__(self):
        self.is_active = False
        self.is_inactive = False

    def set_active(self):
        self.is_active = True
        self.is_inactive = False

    def set_inactive(self):
        self.is_active = False
        self.is_inactive = True

    @property
    def is_dormant(self):
        return (not self.is_inactive and not self.is_active)

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
    
    @abstractmethod
    async def update_now(self):
        ...

    @abstractmethod
    def get_type(self):
        ...
    
    @abstractmethod
    def get_sender_id(self):
        ...