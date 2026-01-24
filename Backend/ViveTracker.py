import openvr
import time

class ViveTrackers:
    def __init__(self):
        openvr.init(openvr.VRApplication_Other)
        self.vr = openvr.VRSystem()

    def shutdown(self):
        openvr.shutdown()

    def _get_pose_position(self, pose):
        m = pose.mDeviceToAbsoluteTracking
        return (
            m[0][3],
            m[1][3],
            m[2][3]
        )

    def get_tracker_position(self):
        poses = self.vr.getDeviceToAbsoluteTrackingPose(
            openvr.TrackingUniverseStanding,
            0,
            openvr.k_unMaxTrackedDeviceCount
        )

        for i in range(openvr.k_unMaxTrackedDeviceCount):
            if not self.vr.isTrackedDeviceConnected(i):
                continue

            if self.vr.getTrackedDeviceClass(i) != openvr.TrackedDeviceClass_GenericTracker:
                continue

            if not poses[i].bPoseIsValid:
                continue

            return self._get_pose_position(poses[i])

        return None


if __name__ == "__main__":
    vt = ViveTrackers()

    try:
        while True:
            t1 = vt.get_tracker_position()

            if t1:
                print(f"Tracker: x={t1[0]:.3f}, y={t1[1]:.3f}, z={t1[2]:.3f}")
            else:
                print("Waiting for tracker...")

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\nShutting down...")

    finally:
        vt.shutdown()
