from abc import ABC, abstractmethod

class TrackerSource(ABC):
    @abstractmethod
    def get_tracker_position(self):
        pass