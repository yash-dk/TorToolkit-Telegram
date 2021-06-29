from abc import ABC, abstractmethod

class BaseTask(ABC):

    ALL_TASKS = []

    # Update type
    CONSTRUCTED = 1 # Just send as it is
    UNCONSTRUCTED = 2 # Create a message only raw info returned

    # STATE : These are the abastract specs
    QUEUED = 1
    RUNNING = 2

    ERRORED = 3
    COMPLETED = 4
    CANCELED = 5

    def __init__(self):
        self._task_id = len(self.ALL_TASKS) + 1

    @abstractmethod
    async def execute(self):
        ...
    
    @abstractmethod
    def update_type(self):
        ...
    
    @abstractmethod
    async def update_contents(self):
        ...
    
    @abstractmethod
    def get_state(self):
        ...

    @abstractmethod
    def get_error_reason(self):
        ...