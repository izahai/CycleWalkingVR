import openvr
from tracker_source.abc_tracker import TrackerSource
from Rudder.RudderManager import RudderManager

class OpenVRTrackerSource(TrackerSource):
    def __init__(self):
        openvr.init(openvr.VRApplication_Other)
        self.vr = openvr.VRSystem()
        self.rudder_manager = RudderManager()

    def shutdown(self):
        openvr.shutdown()

    def get_tracker_position(self):
        poses = self.vr.getDeviceToAbsoluteTrackingPose(
            openvr.TrackingUniverseStanding,
            0,
            openvr.k_unMaxTrackedDeviceCount
        )

        tracker_indices = []

        for i in range(openvr.k_unMaxTrackedDeviceCount):
            if not self.vr.isTrackedDeviceConnected(i):
                continue
            if self.vr.getTrackedDeviceClass(i) != openvr.TrackedDeviceClass_GenericTracker:
                continue
            tracker_indices.append(i)

        # Need at least one tracker
        if len(tracker_indices) < 1:
            return None

        # First tracker → XYZ position
        i = tracker_indices[0]
        if not poses[i].bPoseIsValid:
            return None

        m = poses[i].mDeviceToAbsoluteTracking
        return (m[0][3], m[1][3], m[2][3])

    
    def get_tracker_rudder_degree(self):
        return self.rudder_manager.get_rudder_degree("ViveTracker2")