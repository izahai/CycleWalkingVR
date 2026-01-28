import json
from tracker_source.abc_tracker import TrackerSource

class JsonTrackerSource(TrackerSource):
    def __init__(self, path, loop=True):
        with open(path) as f:
            raw = json.load(f)
        self.data = self._normalize(raw)
        self.index = 0
        self.loop = loop

    def _normalize(self, raw):
        if isinstance(raw, dict):
            samples = raw.get("samples")
            if isinstance(samples, list):
                raw = samples

        if not isinstance(raw, list):
            return []

        normalized = []
        for item in raw:
            if isinstance(item, dict):
                if "pos" in item:
                    pos = item["pos"]
                    if isinstance(pos, (list, tuple)) and len(pos) >= 3:
                        normalized.append({"x": pos[0], "y": pos[1], "z": pos[2]})
                elif all(k in item for k in ("x", "y", "z")):
                    normalized.append({"x": item["x"], "y": item["y"], "z": item["z"]})
            elif isinstance(item, (list, tuple)) and len(item) >= 3:
                normalized.append({"x": item[0], "y": item[1], "z": item[2]})

        return normalized

    def get_tracker_position(self):
        if not self.data:
            return None

        if self.index >= len(self.data):
            if not self.loop:
                return None
            self.index = 0

        pos = self.data[self.index]
        self.index += 1
        return (pos["x"], pos["y"], pos["z"])
