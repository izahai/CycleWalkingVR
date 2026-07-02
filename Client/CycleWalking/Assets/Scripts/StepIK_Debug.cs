using UnityEngine;

/// <summary>
/// MINIMAL TEST — isolates the IK constraint behavior.
/// Press T to raise/lower the right foot by a small amount.
/// No raycasting, no forward probe, no swing detection.
/// </summary>
public class StepIK_Debug : MonoBehaviour
{
    private Transform rightTarget;
    private Transform leftTarget;
    private float testHeight;

    private void Awake()
    {
        // Find targets
        var rightMover = transform.Find("FootRig/RightFootMover");
        var leftMover  = transform.Find("FootRig/LeftFootMover");
        rightTarget = rightMover?.Find("RightTarget");
        leftTarget  = leftMover?.Find("LeftTarget");

        if (rightTarget == null) Debug.LogError("RightTarget not found");
        if (leftTarget == null) Debug.LogError("LeftTarget not found");

        testHeight = rightTarget.position.y;
    }

    private void Update()
    {
        // T: add 0.1m to right foot height
        if (Input.GetKeyDown(KeyCode.T))
        {
            testHeight += 0.1f;
            Vector3 pos = rightTarget.position;
            pos.y = testHeight;
            rightTarget.position = pos;
            Debug.Log($"Right target Y = {testHeight:F3}");
        }

        // G: subtract 0.1m from right foot height
        if (Input.GetKeyDown(KeyCode.G))
        {
            testHeight -= 0.1f;
            Vector3 pos = rightTarget.position;
            pos.y = testHeight;
            rightTarget.position = pos;
            Debug.Log($"Right target Y = {testHeight:F3}");
        }

        // H: reset right foot to left foot height
        if (Input.GetKeyDown(KeyCode.H))
        {
            testHeight = leftTarget.position.y;
            Vector3 pos = rightTarget.position;
            pos.y = testHeight;
            rightTarget.position = pos;
            Debug.Log($"Right target Y reset to {testHeight:F3}");
        }
    }
}
