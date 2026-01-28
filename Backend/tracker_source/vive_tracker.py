from tracker_source.abc_tracker import TrackerSource

class ViveTrackers:
    def __init__(self, source: TrackerSource):
        self.source = source

    def shutdown(self):
        if hasattr(self.source, "shutdown"):
            self.source.shutdown()

    def get_tracker_position(self):
        return self.source.get_tracker_position()