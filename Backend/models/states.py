# tracker/states.py
from enum import Enum, auto


class TrackerState(Enum):
    COLLECT_VERTICAL = auto()
    SEND_VERTICAL = auto()
    STREAM_POSITIONS = auto()