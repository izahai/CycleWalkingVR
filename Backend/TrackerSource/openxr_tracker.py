import openvr
from TrackerSource.abc_tracker import TrackerSource

class OpenVRTrackerSource(TrackerSource):
    def __init__(self):
        openvr.init(openvr.VRApplication_Other)
        self.vr = openvr.VRSystem()

    def shutdown(self):
        openvr.shutdown()

    def get_tracker_position(self):
        poses = self.vr.getDeviceToAbsoluteTrackingPose(
            openvr.TrackingUniverseStanding,
            0,
            openvr.k_unMaxTrackedDeviceCount
        )

        for i in range(openvr.k_unMaxTrackedDeviceCount):
            if (
                self.vr.isTrackedDeviceConnected(i)
                and self.vr.getTrackedDeviceClass(i) == openvr.TrackedDeviceClass_GenericTracker
                and poses[i].bPoseIsValid
            ):
                m = poses[i].mDeviceToAbsoluteTracking
                return (m[0][3], m[1][3], m[2][3])

        return None