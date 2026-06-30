# tracker/states.py
from enum import Enum, auto


class TrackerState(Enum):
    COLLECT_VERTICAL = auto()
    COLLECT_HORIZONTAL = auto()
    SEND_CIRCLE = auto()
    SEND_REF_LINE = auto()
    STREAMING = auto()
    RETURN = auto()