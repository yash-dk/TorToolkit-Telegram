from abc import ABC, abstractmethod

class BaseStatus(ABC):
    QBIT = 0
    ARIA2 = 1
    MEGA = 2
    YTDL = 3
    PYTDL = 4
    RCLUP = 5
    TGUP = 6
    def __init__(self):
        self._is_active = False
        self._is_inactive = False

    @property
    def is_active(self):
        return self._is_active
    
    @property
    def is_inactive(self):
        return self._is_inactive

    @property
    def is_dormant(self):
        return (not self.is_inactive and not self.is_active)
    
    @abstractmethod
    async def update_now(self):
        ...

    @abstractmethod
    def get_type(self):
        ...