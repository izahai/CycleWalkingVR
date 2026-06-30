import openvr
import math


class ViveTracker:
    def __init__(self):
        openvr.init(openvr.VRApplication_Other)
        self.vr = openvr.VRSystem()

    def shutdown(self):
        openvr.shutdown()

    def get_tracker_2_rotation(self):
        """Get roll, pitch, yaw (in degrees) of tracker 2 only."""
        poses = self.vr.getDeviceToAbsoluteTrackingPose(
            openvr.TrackingUniverseStanding,
            0,
            openvr.k_unMaxTrackedDeviceCount
        )
        
        i = 1
        if not self.vr.isTrackedDeviceConnected(i):
            print("[ViveTracker] Error: Tracker 2 not found")
            return (0.0, 0.0, 0.0)

        if self.vr.getTrackedDeviceClass(i) != openvr.TrackedDeviceClass_GenericTracker:
            print("[ViveTracker] Error: Device at index 1 is not a tracker")
            return (0.0, 0.0, 0.0)

        if poses[i].bPoseIsValid:
            R = self._rotation_matrix(poses[i])
            return self._matrix_to_euler_deg(R)
        else:
            print("[ViveTracker] Error: Tracker 2 pose is invalid")
            return (0.0, 0.0, 0.0)

    def _rotation_matrix(self, pose):
        m = pose.mDeviceToAbsoluteTracking
        return (
            (m[0][0], m[0][1], m[0][2]),
            (m[1][0], m[1][1], m[1][2]),
            (m[2][0], m[2][1], m[2][2]),
        )

    def _matrix_to_euler_deg(self, R):
        r00, r01, r02 = R[0]
        r10, r11, r12 = R[1]
        r20, r21, r22 = R[2]

        roll = math.atan2(r21, r22)
        pitch = math.asin(max(-1.0, min(1.0, -r20)))
        yaw = math.atan2(r10, r00)

        return (math.degrees(roll), math.degrees(pitch), math.degrees(yaw))
m