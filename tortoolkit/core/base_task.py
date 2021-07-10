from abc import ABC, abstractmethod
from datetime import datetime

class BaseTask(ABC):

    ALL_TASKS = []

    USER = 0
    ADMIN = 1

    def __init__(self):
        self._task_id = len(self.ALL_TASKS) + 1
        self._is_scheduled = True
        self._is_running = False
        self._is_done = False
        self._is_completed = False
        self._is_canceled = False
        self._is_errored = False
        self._error_reason = ""
        self._canceled_by = None
        self._time_added = datetime.now()
        self._time_completed = None

    @property
    def is_scheduled(self):
        return self._is_scheduled

    @property
    def is_running(self):
        return self._is_running

    @property
    def is_done(self):
        return (self._is_done or self._is_errored or self._is_canceled or self._is_completed)

    @property
    def is_completed(self):
        return self._is_completed
    
    @property
    def is_canceled(self):
        return self._is_canceled
    
    @property
    def is_errored(self):
        return self._is_errored

    def get_canceled_by(self):
        return self._canceled_by
    
    def get_times(self):
        return self._time_added, self._time_completed

    async def execute(self):
        ...
    
    #@abstractmethod
    def cancel(self, is_admin=False):
        ...
    
    #@abstractmethod
    async def get_update(self):
        ...
    
    #@abstractmethod
    def get_error_reason(self):
        ...